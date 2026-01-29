import asyncio
import json
import time
import requests
import os
import argparse
from datetime import datetime
from dateutil import parser
from playwright.async_api import async_playwright


async def scrape_articles(start_date=None, end_date=None):
    """Scrape and download Haddas Ertra PDFs within a date range."""
    
    print(f"Scraping articles" + (f" from {start_date}" if start_date else "") + (f" to {end_date}" if end_date else "") + "...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Collect article URLs from multiple pages
            article_urls = []
            max_articles = 50 # Increased limit to allow finding articles in range
            found_articles_in_range = False
            
            for page_num in range(1, 101):  # Check up to 100 pages
                print(f"Processing page {page_num}...")

                page_url = "https://shabait.com/category/newspapers/haddas-ertra-news/" + (f"page/{page_num}/" if page_num > 1 else "")

                try:
                    await page.goto(page_url)
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_timeout(2000)
                except Exception as e:
                    print(f"Error loading page {page_num}: {e}")
                    break

                # Get articles on this page with their dates if possible (metadata often not available directly on listing)
                # So we collect links and check dates inside, OR check dates on listing if available.
                # Checking listing dates first is much faster.
                
                articles = await page.query_selector_all('article.listing-item')
                current_page_urls = []
                
                for article in articles:
                    try:
                        # Extract date from listing
                        date_elem = await article.query_selector('.entry-date, .post-date, time')
                        if date_elem:
                            date_text = (await date_elem.text_content()).strip()
                            try:
                                article_date = parser.parse(date_text)
                                # Filter
                                if end_date and article_date > end_date:
                                    continue # Too new, skip
                                if start_date and article_date < start_date:
                                    # Assuming reverse chronological order, if we hit a date older than start_date, we might be done?
                                    # But sometimes sticky posts exist, so maybe just skip for now, but mark signal.
                                    # However, standard newspaper archives are usually chronological.
                                    # Let's simple skip but keep checking to be safe, or break if we are sure.
                                    # For now, let's just skip but keep checking page.
                                    # Actually, if we are on page 10 and see 2020, and want 2022, we should stop? No, we are going backwards.
                                    # We want 2022-2023.
                                    # Page 1: 2024 (skip, > end)
                                    # ...
                                    # Page 5: 2023 (keep)
                                    # ...
                                    # Page 10: 2021 (< start, stop?)
                                    # Yes, usually can stop if significantly past start date.
                                    pass
                                    
                                if (not start_date or article_date >= start_date) and (not end_date or article_date <= end_date):
                                     link = await article.query_selector('a.post-url[href*="haddas-ertra"]')
                                     if link:
                                         href = await link.get_attribute('href')
                                         if href and href not in article_urls:
                                             href = f"https://shabait.com{href}" if not href.startswith('http') else href
                                             current_page_urls.append(href)
                                             found_articles_in_range = True
                            except:
                                # If date parse fails, maybe include it to be safe and check later? or skip?
                                # safer to include if we can't parse date on listing
                                link = await article.query_selector('a.post-url[href*="haddas-ertra"]')
                                if link:
                                     href = await link.get_attribute('href')
                                     if href and href not in article_urls:
                                         current_page_urls.append(href)
                        else:
                             # No date on listing, grab link to check later
                             link = await article.query_selector('a.post-url[href*="haddas-ertra"]')
                             if link:
                                 href = await link.get_attribute('href')
                                 if href and href not in article_urls:
                                     current_page_urls.append(href)

                    except Exception as e:
                        continue

                print(f"Found {len(current_page_urls)} potential articles on page {page_num}")

                if not current_page_urls and found_articles_in_range:
                     # If we found some before, but none now, and assuming chronological, maybe we are done?
                     # But let's verify if we passed the start date.
                     # Simplified: If we found no matching URLs on a page, and we have found some before, likely reached end.
                     # Or if we have collected enough.
                     if len(article_urls) > 0:
                         # Check if the last article date on page was before start_date
                         # This is complex to do perfectly without seeing all dates.
                         # Let's rely on manual break or sufficient count.
                         pass
                
                # If we found nothing on this page, and haven't found anything yet, maybe we just need to go further back (if searching for old dates)
                # If we found nothing, and DID find something before, maybe we are done.

                if not current_page_urls and len(article_urls) > 0:
                     # Heuristic: stop if empty page after finding stuff
                     # But current_page_urls is filtered.
                     pass

                article_urls.extend(current_page_urls)

                if len(article_urls) >= max_articles:
                    break
                
                # Heuristic to stop if we are going too far back?
                # Hard to tell without parsing all dates.
                # Let's limit strictly by pages for safety or max count.

            article_urls = article_urls[:max_articles]
            print(f"Collected {len(article_urls)} article URLs")

            # Create metadata
            pdf_metadata = []
            
            # Create download directory
            download_dir = os.path.join(os.getcwd(), 'pdfs')
            os.makedirs(download_dir, exist_ok=True)

            # Download PDFs
            for i, article_url in enumerate(article_urls):
                print(f"Processing article {i+1}/{len(article_urls)}")

                try:
                    await page.goto(article_url)
                    await page.wait_for_load_state('networkidle')

                    # Extract title and date
                    title_element = await page.query_selector('h1, .entry-title, .post-title')
                    title = (await title_element.text_content()).strip() if title_element else f'Article {i+1}'

                    date_element = await page.query_selector('.entry-date, .post-date, time')
                    date_str = (await date_element.text_content()).strip() if date_element else 'Unknown Date'
                    
                    # Double check date if we pushed it here
                    try:
                        article_date = parser.parse(date_str)
                        if end_date and article_date > end_date:
                            print(f"Skipping {title} (Date: {date_str} > {end_date})")
                            continue
                        if start_date and article_date < start_date:
                            print(f"Skipping {title} (Date: {date_str} < {start_date})")
                            continue
                    except:
                        pass # Keep if date parse fails

                    # Find PDF download link
                    download_icon = await page.query_selector('img.wp-image-77661')
                    direct_pdf_url = None

                    if download_icon:
                        parent_link = await download_icon.query_selector('xpath=ancestor::a[1]')
                        if parent_link:
                            href = await parent_link.get_attribute('href')
                            if href and (href.endswith('.pdf') or 'erinewspapers.com' in href):
                                direct_pdf_url = href if href.startswith('http') else f"https://shabait.com{href}"

                    # Fallback: search for PDF links
                    if not direct_pdf_url:
                        pdf_links = await page.query_selector_all('a[href$=".pdf"]')
                        for link in pdf_links:
                            href = await link.get_attribute('href')
                            if href and ('erinewspapers.com' in href or 'hadas-eritrea' in href):
                                direct_pdf_url = href if href.startswith('http') else f"https://shabait.com{href}"
                                break

                    if direct_pdf_url:
                        # Create filename and download
                        safe_title = title.replace('/', '-').replace('\\', '-').replace(':', '-').replace('*', '-').replace('?', '-').replace('"', '-').replace('<', '-').replace('>', '-').replace('|', '-')
                        safe_date = date_str.replace('/', '-').replace('\\', '-').replace(':', '-').replace('*', '-').replace('?', '-').replace('"', '-').replace('<', '-').replace('>', '-').replace('|', '-')
                        filename = f"{safe_date}_{safe_title}.pdf"
                        filepath = os.path.join(download_dir, filename)
                        
                        # Add to metadata
                        meta_entry = {
                            'index': len(pdf_metadata) + 1,
                            'article_url': article_url,
                            'title': title,
                            'date': date_str,
                            'pdf_filename': filename,
                            'pdf_filepath': filepath,
                            'pdf_url': direct_pdf_url,
                            'download_status': 'pending',
                            'text_extraction_status': 'pending'
                        }
                        
                        pdf_metadata.append(meta_entry)

                        try:
                            response = requests.get(direct_pdf_url, timeout=60) # Increased timeout
                            response.raise_for_status()

                            with open(filepath, 'wb') as f:
                                f.write(response.content)

                            print(f"✓ Downloaded: {filename}")
                            meta_entry['download_status'] = 'completed'

                        except Exception as e:
                            print(f"✗ Failed: {filename} - {str(e)}")
                            meta_entry['download_status'] = 'failed'
                            meta_entry['error'] = str(e)
                    else:
                        print(f"✗ No PDF link found for article {i+1}")

                except Exception as e:
                    print(f"✗ Error processing article {i+1}: {str(e)}")

                # Update metadata after each article
                with open('pdf_metadata.json', 'w', encoding='utf-8') as f:
                    json.dump(pdf_metadata, f, ensure_ascii=False, indent=2)

                # Rate limiting
                time.sleep(2)

            # Final summary
            successful_count = sum(1 for m in pdf_metadata if m['download_status'] == 'completed')
            print(f"\nCompleted: {successful_count}/{len(pdf_metadata)} PDFs downloaded")

        except Exception as e:
            print(f"Scraping error: {str(e)}")

        finally:
            await browser.close()


async def main():
    """Main function."""
    parser_args = argparse.ArgumentParser(description='Haddas Ertra Scraper')
    parser_args.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser_args.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    args = parser_args.parse_args()
    
    start_date = parser.parse(args.start_date) if args.start_date else None
    end_date = parser.parse(args.end_date) if args.end_date else None

    print("Starting Haddas Ertra PDF downloader...")
    await scrape_articles(start_date, end_date)


if __name__ == "__main__":
    asyncio.run(main())
