import asyncio
import json
import time
import requests
import os
from playwright.async_api import async_playwright


async def scrape_articles():
    """Scrape and download Haddas Ertra PDFs."""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Collect article URLs from multiple pages
            article_urls = []
            max_articles = 20

            for page_num in range(1, 51):  # Check up to 50 pages
                print(f"Processing page {page_num}...")

                page_url = "https://shabait.com/category/newspapers/haddas-ertra-news/" + (f"page/{page_num}/" if page_num > 1 else "")

                try:
                    await page.goto(page_url)
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_timeout(2000)
                except Exception as e:
                    print(f"Error loading page {page_num}: {e}")
                    break

                # Find article links
                link_elements = await page.query_selector_all('article.listing-item a.post-url[href*="haddas-ertra"]')
                current_page_urls = []

                for link in link_elements:
                    try:
                        href = await link.get_attribute('href')
                        if href and href not in article_urls:
                            href = f"https://shabait.com{href}" if not href.startswith('http') else href
                            current_page_urls.append(href)
                    except:
                        continue

                print(f"Found {len(current_page_urls)} articles on page {page_num}")

                if not current_page_urls:
                    break

                article_urls.extend(current_page_urls)

                if len(article_urls) >= max_articles:
                    break

            article_urls = article_urls[:max_articles]
            print(f"Collected {len(article_urls)} article URLs")

            # Create metadata
            pdf_metadata = [{
                'index': i + 1,
                'article_url': url,
                'download_status': 'pending',
                'text_extraction_status': 'pending'
            } for i, url in enumerate(article_urls)]

            with open('pdf_metadata.json', 'w', encoding='utf-8') as f:
                json.dump(pdf_metadata, f, ensure_ascii=False, indent=2)

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
                    date = (await date_element.text_content()).strip() if date_element else 'Unknown Date'

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
                        safe_date = date.replace('/', '-').replace('\\', '-').replace(':', '-').replace('*', '-').replace('?', '-').replace('"', '-').replace('<', '-').replace('>', '-').replace('|', '-')
                        filename = f"{safe_date}_{safe_title}.pdf"
                        filepath = os.path.join(download_dir, filename)

                        try:
                            response = requests.get(direct_pdf_url, timeout=30)
                            response.raise_for_status()

                            with open(filepath, 'wb') as f:
                                f.write(response.content)

                            print(f"✓ Downloaded: {filename}")

                            pdf_metadata[i].update({
                                'download_status': 'completed',
                                'title': title,
                                'date': date,
                                'pdf_filename': filename,
                                'pdf_filepath': filepath,
                                'pdf_url': direct_pdf_url
                            })

                        except Exception as e:
                            print(f"✗ Failed: {filename} - {str(e)}")
                            pdf_metadata[i]['download_status'] = 'failed'
                            pdf_metadata[i]['error'] = str(e)
                    else:
                        print(f"✗ No PDF link found for article {i+1}")
                        pdf_metadata[i]['download_status'] = 'failed'
                        pdf_metadata[i]['error'] = 'No PDF link found'

                except Exception as e:
                    print(f"✗ Error processing article {i+1}: {str(e)}")
                    pdf_metadata[i]['download_status'] = 'failed'
                    pdf_metadata[i]['error'] = str(e)

                # Update metadata after each article
                with open('pdf_metadata.json', 'w', encoding='utf-8') as f:
                    json.dump(pdf_metadata, f, ensure_ascii=False, indent=2)

                # Rate limiting
                if i < len(article_urls) - 1:
                    time.sleep(4)

            # Final summary
            successful_count = sum(1 for m in pdf_metadata if m['download_status'] == 'completed')
            print(f"\nCompleted: {successful_count}/{len(pdf_metadata)} PDFs downloaded")

        except Exception as e:
            print(f"Scraping error: {str(e)}")

        finally:
            await browser.close()


async def main():
    """Main function."""
    print("Starting Haddas Ertra PDF downloader...")
    await scrape_articles()


if __name__ == "__main__":
    asyncio.run(main())