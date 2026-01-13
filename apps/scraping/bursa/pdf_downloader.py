from playwright.async_api import Page
import os
import requests

class BursaPDFDownloader:
    """
    Downloads PDFs attached to announcements.
    """
    def __init__(self, download_dir: str):
        self.download_dir = download_dir
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

    async def download_pdfs(self, page: Page, pdf_urls: list) -> list:
        """
        Download PDFs found in the announcement.
        Returns list of local file paths.
        """
        # If urls are not provided, try to find them on page
        if not pdf_urls:
            pdf_urls = await page.evaluate("""() => {
                const links = document.querySelectorAll('a[href$=".pdf"]');
                return Array.from(links).map(a => a.href);
            }""")
            
        saved_files = []
        for url in pdf_urls:
            try:
                # Sync download for simplicity, ideally async with aiohttp
                filename = url.split('/')[-1]
                save_path = os.path.join(self.download_dir, filename)
                
                # Check if exists
                if os.path.exists(save_path):
                    saved_files.append(save_path)
                    continue
                    
                print(f"Downloading PDF: {url}")
                # Use requests for tailored headers if needed to avoid blocking? 
                # Or use page context request
                # For now simple requests
                resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
                if resp.status_code == 200:
                    with open(save_path, 'wb') as f:
                        f.write(resp.content)
                    saved_files.append(save_path)
                else:
                    print(f"Failed to download {url}: {resp.status_code}")
                    
            except Exception as e:
                print(f"Error downloading PDF {url}: {e}")
                
        return saved_files
