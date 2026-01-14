from playwright.async_api import Page
from typing import List, Dict, Any
from .selectors import SELECTORS
import asyncio

class BursaListingCrawler:
    """
    Handles scraping of the announcement listing page.
    """
    def __init__(self):
        pass

    async def crawl_category_by_filter(
        self, 
        page: Page, 
        base_url: str,
        category_code: str,
        category_name: str,
        max_announcements: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Navigate to base URL and filter by category using form submission.
        
        Args:
            page: Playwright page
            base_url: Base URL (www.bursamalaysia.com announcements)
            category_code: Category code for filtering (e.g., "FA,FRCO")
            category_name: Display name for tagging announcements
            max_announcements: Maximum number of announcements to extract
            
        Returns:
            List of announcements with category field set to category_name
        """
        # Navigate to base URL
        await page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
        
        # Level 1 Cloudflare Bypass: Give user time to manually solve CAPTCHA
        print("\n" + "="*70)
        print("👀 Check the browser window!")
        print("   If you see a Cloudflare 'Verify you are human' box,")
        print("   click it manually now!")
        print("   Waiting 10 seconds...")
        print("="*70 + "\n")
        await page.wait_for_timeout(10000)  # 10 seconds for manual CAPTCHA solving
        
        # Filter by category using form
        try:
            # Wait for category select to be available
            await page.wait_for_selector('select[name="cat"]', timeout=10000)

            
            # Select the category option by value
            await page.select_option('select[name="cat"]', value=category_code, timeout=5000)
            await page.wait_for_timeout(800)
            
            # Click Search button
            await page.wait_for_selector('.form-submit-btn', timeout=5000)
            await page.click('.form-submit-btn', timeout=5000)
            await page.wait_for_timeout(5000)  # Wait longer for AJAX results to load
            
        except Exception as e:
            print(f"Warning: Could not filter by category '{category_name}': {e}")
            print("Attempting to proceed with current page content...")
            # Continue with current page content

        
        # Extract announcements from table
        announcements = await self._extract_announcements_from_table(page, category_name)
        
        # NOTE: Bursa Malaysia website displays 20 results per page by default
        # To scrape more than 20, would need to implement pagination:
        # - Click "Next Page" button or "Load More" button
        # - OR use AJAX pagination to load additional results
        # Current implementation only extracts visible announcements on first page
        
        return announcements[:max_announcements]
    
    async def _extract_announcements_from_table(
        self, 
        page: Page, 
        category: str = "Financial Result"
    ) -> List[Dict[str, Any]]:
        """
        Extract announcements from www.bursamalaysia.com table structure.
        
        Table columns: No., Announcement Date, Company Name, Title
        """
        announcements_data = await page.evaluate("""(category) => {
            const results = [];
            const seen = new Set();
            
            // Select announcement rows from table
            const rows = document.querySelectorAll('tbody tr');
            
            for (const row of rows) {
                if (results.length >= 100) break;
                
                const cells = row.querySelectorAll('td');
                if (cells.length < 4) continue;
                
                // Extract data from columns
                const date = cells[1].innerText.trim();  // Column 2: Announcement Date
                const companyElem = cells[2].querySelector('a');  // Column 3: Company Name
                const companyName = companyElem ? companyElem.innerText.trim() : cells[2].innerText.trim();
                
                const titleElem = cells[3].querySelector('a');  // Column 4: Title
                const title = titleElem ? titleElem.innerText.trim() : cells[3].innerText.trim();
                const detailUrl = titleElem ? titleElem.href : null;
                
                if (!detailUrl || seen.has(detailUrl)) continue;
                seen.add(detailUrl);
                
                // Extract ann_id from URL (pattern: announcement_details?ann_id=XXXXXXX)
                const annIdMatch = detailUrl.match(/ann_id=(\d+)/);
                const annId = annIdMatch ? annIdMatch[1] : null;
                
                if (!annId) continue;
                
                results.push({
                    date: date,
                    title: title,
                    category: category,
                    company_name: companyName,  // Now available directly from listing
                    detail_page_url: detailUrl,
                    announcement_id: annId,  // Extracted from URL
                    pdf_urls: [],  // Will be extracted from detail page
                    position: {
                        top: row.getBoundingClientRect().top + window.scrollY,
                        left: row.getBoundingClientRect().left,
                        width: row.getBoundingClientRect().width,
                        height: row.getBoundingClientRect().height
                    }
                });
            }
            
            return results;
        }""", category)
        
        return announcements_data
    

    async def highlight_announcements_on_page(self, page: Page, announcements: List[Dict[str, Any]]):
        """
        Draw bounding boxes (Phase 6).
        """
        colors = ['#3b82f6', '#8b5cf6', '#10b981', '#06b6d4', '#f59e0b']
        for idx, announcement in enumerate(announcements):
            color = colors[idx % len(colors)]
            
            # Simple scrolling and highlighting by URL selector
            await page.evaluate(f"""(url) => {{
                const link = document.querySelector('a[href="' + url + '"]');
                if (link) {{
                    const row = link.closest('tr');
                    if (row) {{
                        row.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                        // Delay to allow scroll
                        setTimeout(() => {{
                             window.drawBoundingBox(row, '{color}', 'Item {idx+1}', true);
                        }}, 500);
                    }}
                }}
            }}""", announcement['detail_page_url'])
            
            await page.wait_for_timeout(600)
