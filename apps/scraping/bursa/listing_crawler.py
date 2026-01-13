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

    async def crawl_category_by_url(
        self, 
        page: Page, 
        category_url: str,
        category_name: str,
        max_announcements: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Navigate to category-specific URL and extract announcements.
        
        Args:
            page: Playwright page
            category_url: Full URL with cat ID (e.g., .../newsroom.html/cat/165)
            category_name: Display name for tagging announcements
            max_announcements: Maximum number of announcements to extract
            
        Returns:
            List of announcements with category field set to category_name
        """
        # Navigate to category URL
        await page.goto(category_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)
        
        # Extract announcements from this category page
        announcements = await self._extract_announcements_from_page(page, category_name)
        
        return announcements[:max_announcements]
    
    async def crawl_yearly_listings(self, page: Page, year: int = 2025, max_announcements: int = 10, categories: List[str] = None) -> List[Dict[str, Any]]:
        """
        Extract announcement rows from the listing page (Phase 2).
        
        Args:
            page: Playwright page object
            year: Year to filter announcements
            max_announcements: Maximum number of announcements to scrape
            categories: Optional list of categories to filter (not used, kept for backwards compatibility)
        """
        # Extract announcements with "All Announcements" (no category filter)
        announcements_data = await self._extract_announcements_from_page(page, "General")
        
        return announcements_data[:max_announcements]
    
    async def _extract_announcements_from_page(self, page: Page, category: str = "General") -> List[Dict[str, Any]]:
        """
        Extract announcement data from the current page using JavaScript evaluation.
        
        Args:
            page: Playwright page object
            category: Category name to tag announcements with
            
        Returns:
            List of announcement dictionaries
        """
        announcements_data = await page.evaluate("""(category) => {
            const results = [];
            const seen = new Set();
            
            // Try specific table selector first for bursa-bm.listedcompany.com
            // Identified classes: bm_row1, bm_row2
            const rows = document.querySelectorAll('tr.bm_row1, tr.bm_row2');
            
            for (const row of rows) {
                if (results.length >= 100) break;
                
                const cells = row.querySelectorAll('td');
                if (cells.length < 2) continue; // Expecting Date, Title
                
                // Heuristic column detection
                // Usually Col 1 = Date, Col 2 = Title/Link
                const date = cells[0].innerText.trim();
                const titleElem = cells[1].querySelector('a');
                const title = titleElem ? titleElem.innerText.trim() : cells[1].innerText.trim();
                const detailUrl = titleElem ? titleElem.href : null;
                
                if (!detailUrl || seen.has(detailUrl)) continue;
                seen.add(detailUrl);
                
                results.push({
                    date: date,
                    title: title,
                    category: category, // Use the provided category parameter
                    detail_page_url: detailUrl,
                    pdf_urls: [], // Gathered from detail page usually
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
