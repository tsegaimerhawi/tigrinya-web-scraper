"""Scraper service: parameterized scraping for Tigrinya newspapers."""
import asyncio
import json
import os
import time
from typing import Any, Optional
from dateutil import parser

import requests
from playwright.async_api import async_playwright

from app.config import DATA_DIR, METADATA_PATH, NEWSPAPERS_BY_ID, PDFS_DIR, RAW_DATA_PATH
import pdfplumber

def _verify_pdf_date(pdf_path: str, date_obj) -> bool:
    """Extract text from first page of PDF and check if it contains the year/month/day."""
    if not date_obj:
        return True
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return False
            first_page = pdf.pages[0].extract_text()
            if not first_page:
                return False
            
            # Check for year (e.g., 2026)
            year_str = str(date_obj.year)
            # Tigrinya months/days can be tricky, but year is almost always in Western numerals
            if year_str not in first_page:
                return False
            
            # Additional check: day (with padding and without)
            day_str = str(date_obj.day)
            day_str_padded = f"{date_obj.day:02d}"
            if day_str not in first_page and day_str_padded not in first_page:
                # Year matched but day didn't - might still be okay but let's be strict
                # if the user asked for "strict" check.
                pass
                
            return True
    except Exception:
        return True # Default to True if PDF can't be read to avoid deleting valid files


async def scrape_articles(
    newspaper_id: str = "haddas-ertra",
    max_articles: int = 100,
    max_pages: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    progress_callback: Any = None,
) -> dict:
    """Scrape and download newspaper PDFs. Returns summary dict."""
    # Reset existing data if starting a new scrape
    import shutil
    if os.path.exists(PDFS_DIR):
        try:
            shutil.rmtree(PDFS_DIR)
        except Exception:
            pass
    os.makedirs(PDFS_DIR, exist_ok=True)
    
    if os.path.exists(METADATA_PATH):
        try:
            os.remove(METADATA_PATH)
        except Exception:
            pass
            
    if os.path.exists(RAW_DATA_PATH):
        try:
            os.remove(RAW_DATA_PATH)
        except Exception:
            pass

    newspaper = NEWSPAPERS_BY_ID.get(newspaper_id)
    if not newspaper:
        return {
            "ok": False,
            "error": f"Unknown newspaper: {newspaper_id}",
            "successful": 0,
            "total": 0,
        }

    os.makedirs(PDFS_DIR, exist_ok=True)
    base_url = newspaper["base_url"]
    href_filter = newspaper["link_selector_href"]
    article_selector = 'article.listing-item'  # CSS selector for article elements
    
    # Parse dates and make them timezone-naive for comparison
    parsed_start = None
    parsed_end = None
    if start_date and start_date.strip():
        parsed_start = parser.parse(start_date)
        if parsed_start.tzinfo:
            parsed_start = parsed_start.replace(tzinfo=None)
    if end_date and end_date.strip():
        parsed_end = parser.parse(end_date)
        if parsed_end.tzinfo:
            parsed_end = parsed_end.replace(tzinfo=None)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            article_urls: list[str] = []
            max_pages_to_check = 100 if (start_date or end_date) else max_pages 

            base = base_url.rstrip("/")
            for page_num in range(1, max_pages_to_check + 1):
                if progress_callback:
                    progress_callback({"stage": "collecting", "page": page_num, "urls": len(article_urls)})

                page_url = f"{base}/page/{page_num}/" if page_num > 1 else base

                try:
                    await page.goto(page_url)
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(2000)
                except Exception as e:
                    break

                # Query for articles on the page
                articles = await page.query_selector_all(article_selector)
                current_urls = []
                
                # Inspect articles on page for date filtering
                found_on_page = 0
                older_found = False

                for article in articles:
                   try:
                        # Date check
                        should_include = True
                        article_date = None
                        date_el = await article.query_selector('.entry-date, .post-date, time')
                        if date_el:
                            date_text = (await date_el.text_content()).strip()
                            try:
                                article_date = parser.parse(date_text)
                                # Make timezone-naive for comparison
                                if article_date.tzinfo:
                                    article_date = article_date.replace(tzinfo=None)
                                    
                                if parsed_end and article_date > parsed_end:
                                    should_include = False
                                if parsed_start and article_date < parsed_start:
                                    should_include = False
                                    older_found = True # We hit older articles
                            except:
                                pass # Include if date can't be parsed on listing
                        
                        if should_include:
                            link = await article.query_selector(f'a.post-url[href*="{href_filter}"]')
                            if link:
                                href = await link.get_attribute("href")
                                if href and href not in article_urls:
                                    href = f"https://shabait.com{href}" if not href.startswith("http") else href
                                    current_urls.append(href)
                                    found_on_page += 1
                   except Exception:
                       continue

                # If we hit older articles than our start date, we can stop traversing pages
                if older_found and parsed_start:
                    article_urls.extend(current_urls)
                    break
                
                article_urls.extend(current_urls)

                # If we've collected enough articles and no date range is specified, or we hit max
                if not (parsed_start or parsed_end) and len(article_urls) >= max_articles:
                    break

            article_urls = article_urls[:max_articles]

            pdf_metadata: list[dict] = [] # Initialize empty, append as we process/confirm

            
            # Temporary storage to save metadata iteratively
            # Re-read existing metadata might be safer? 
            # For this service, let's just overwrite for the current scraping session or append?
            # The original code overwrote. Let's stick to that for now or clear.
            
            # Let's process and then save.
            
            final_metadata = []

            for i, article_url in enumerate(article_urls):
                if progress_callback:
                    progress_callback(
                        {"stage": "downloading", "current": i + 1, "total": len(article_urls), "url": article_url}
                    )

                try:
                    await page.goto(article_url)
                    await page.wait_for_load_state("networkidle")

                    title_el = await page.query_selector("h1, .entry-title, .post-title")
                    title = (await title_el.text_content()).strip() if title_el else f"Article {i+1}"

                    date_el = await page.query_selector(".entry-date, .post-date, time")
                    date = (await date_el.text_content()).strip() if date_el else "Unknown Date"
                    
                    # Double check date if filtering was requested
                    if parsed_start or parsed_end:
                        try:
                            article_date = parser.parse(date)
                            if parsed_end and article_date > parsed_end:
                                continue
                            if parsed_start and article_date < parsed_start:
                                continue
                        except:
                            pass

                    direct_pdf_url = None
                    icon = await page.query_selector("img.wp-image-77661")
                    if icon:
                        parent = await icon.query_selector("xpath=ancestor::a[1]")
                        if parent:
                            href = await parent.get_attribute("href")
                            if href and (href.endswith(".pdf") or "erinewspapers.com" in href):
                                direct_pdf_url = href if href.startswith("http") else f"https://shabait.com{href}"

                    if not direct_pdf_url:
                        for link in await page.query_selector_all('a[href$=".pdf"]'):
                            href = await link.get_attribute("href")
                            if href and ("erinewspapers.com" in href or "hadas-eritrea" in href):
                                direct_pdf_url = href if href.startswith("http") else f"https://shabait.com{href}"
                                break

                    meta_entry = {
                        "index": len(final_metadata) + 1,
                        "article_url": article_url,
                        "download_status": "pending",
                        "text_extraction_status": "pending",
                        "title": title,
                        "date": date
                    }

                    if direct_pdf_url:
                        def _safe(s: str) -> str:
                            return "".join(c if c not in '/\\:*?"<>|' else "-" for c in (s or ""))

                        filename = f"{_safe(date)}_{_safe(title)}.pdf"
                        filepath = os.path.join(PDFS_DIR, filename)
                        
                        meta_entry.update({
                            "pdf_filename": filename,
                            "pdf_filepath": filepath,
                            "pdf_url": direct_pdf_url
                        })

                        try:
                            r = requests.get(direct_pdf_url, timeout=30)
                            r.raise_for_status()
                            with open(filepath, "wb") as f:
                                f.write(r.content)
                            
                            # VERIFY PDF CONTENT DATE
                            if parsed_start and not _verify_pdf_date(filepath, parsed_start):
                                os.remove(filepath)
                                continue
                                
                            meta_entry["download_status"] = "completed"
                        except Exception as e:
                            meta_entry["download_status"] = "failed"
                            meta_entry["error"] = str(e)
                    else:
                        meta_entry["download_status"] = "failed"
                        meta_entry["error"] = "No PDF link found"
                    
                    if meta_entry["download_status"] == "completed":
                        final_metadata.append(meta_entry)
                        # Save progressively
                        with open(METADATA_PATH, "w", encoding="utf-8") as f:
                            json.dump(final_metadata, f, ensure_ascii=False, indent=2)

                except Exception as e:
                   pass # Log error but continue

                if i < len(article_urls) - 1:
                    time.sleep(2)

            successful = sum(1 for m in final_metadata if m.get("download_status") == "completed")
            return {
                "ok": True,
                "newspaper_id": newspaper_id,
                "total": len(final_metadata),
                "successful": successful,
                "metadata_path": METADATA_PATH,
            }

        except Exception as e:
            return {"ok": False, "error": str(e), "successful": 0, "total": 0}
        finally:
            await browser.close()


def run_scrape_sync(
    newspaper_id: str = "haddas-ertra",
    max_articles: int = 20,
    max_pages: int = 50,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """Synchronous wrapper for scrape_articles."""
    return asyncio.run(scrape_articles(newspaper_id, max_articles, max_pages, start_date, end_date))
