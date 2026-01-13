from playwright.async_api import Page

class BursaAnnouncementFetcher:
    """
    Handles navigation to announcement detail pages.
    """
    def __init__(self):
        pass

    async def fetch_detail_page(self, page: Page, url: str) -> bool:
        """
        Navigate to the detail page.
        """
        try:
            print(f"Navigating to {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # await page.wait_for_selector('table', timeout=10000) # Optional wait
            return True
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            return False
