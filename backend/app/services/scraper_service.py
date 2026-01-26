"""Scraper service: parameterized scraping for Tigrinya newspapers."""
import asyncio
import json
import os
import time
from typing import Any

import requests
from playwright.async_api import async_playwright

from app.config import DATA_DIR, METADATA_PATH, NEWSPAPERS_BY_ID, PDFS_DIR


async def scrape_articles(
    newspaper_id: str = "haddas-ertra",
    max_articles: int = 20,
    max_pages: int = 50,
    progress_callback: Any = None,
) -> dict:
    """Scrape and download newspaper PDFs. Returns summary dict."""
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

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            article_urls: list[str] = []

            base = base_url.rstrip("/")
            for page_num in range(1, max_pages + 1):
                if progress_callback:
                    progress_callback({"stage": "collecting", "page": page_num, "urls": len(article_urls)})

                page_url = f"{base}/page/{page_num}/" if page_num > 1 else base

                try:
                    await page.goto(page_url)
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(2000)
                except Exception as e:
                    break

                sel = f'article.listing-item a.post-url[href*="{href_filter}"]'
                link_elements = await page.query_selector_all(sel)
                current: list[str] = []

                for link in link_elements:
                    try:
                        href = await link.get_attribute("href")
                        if href and href not in article_urls:
                            href = f"https://shabait.com{href}" if not href.startswith("http") else href
                            current.append(href)
                    except Exception:
                        continue

                if not current:
                    break
                article_urls.extend(current)
                if len(article_urls) >= max_articles:
                    break

            article_urls = article_urls[:max_articles]

            pdf_metadata: list[dict] = [
                {
                    "index": i + 1,
                    "article_url": url,
                    "download_status": "pending",
                    "text_extraction_status": "pending",
                }
                for i, url in enumerate(article_urls)
            ]

            def _save_meta():
                with open(METADATA_PATH, "w", encoding="utf-8") as f:
                    json.dump(pdf_metadata, f, ensure_ascii=False, indent=2)

            _save_meta()

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

                    if direct_pdf_url:
                        def _safe(s: str) -> str:
                            return "".join(c if c not in '/\\:*?"<>|' else "-" for c in (s or ""))

                        filename = f"{_safe(date)}_{_safe(title)}.pdf"
                        filepath = os.path.join(PDFS_DIR, filename)
                        try:
                            r = requests.get(direct_pdf_url, timeout=30)
                            r.raise_for_status()
                            with open(filepath, "wb") as f:
                                f.write(r.content)
                            pdf_metadata[i].update(
                                {
                                    "download_status": "completed",
                                    "title": title,
                                    "date": date,
                                    "pdf_filename": filename,
                                    "pdf_filepath": filepath,
                                    "pdf_url": direct_pdf_url,
                                }
                            )
                        except Exception as e:
                            pdf_metadata[i]["download_status"] = "failed"
                            pdf_metadata[i]["error"] = str(e)
                    else:
                        pdf_metadata[i]["download_status"] = "failed"
                        pdf_metadata[i]["error"] = "No PDF link found"

                except Exception as e:
                    pdf_metadata[i]["download_status"] = "failed"
                    pdf_metadata[i]["error"] = str(e)

                _save_meta()
                if i < len(article_urls) - 1:
                    time.sleep(4)

            successful = sum(1 for m in pdf_metadata if m.get("download_status") == "completed")
            return {
                "ok": True,
                "newspaper_id": newspaper_id,
                "total": len(pdf_metadata),
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
) -> dict:
    """Synchronous wrapper for scrape_articles."""
    return asyncio.run(scrape_articles(newspaper_id, max_articles, max_pages))
