from playwright.async_api import Page
from typing import List, Dict, Any, Optional
from .selectors import SELECTORS
import asyncio
import time
import math
from urllib.parse import quote

class BursaListingCrawler:
    """
    Handles scraping of the announcement listing page.
    """
    def __init__(self):
        self._proxy_cache: Optional[List[str]] = None
        self._proxy_cache_at: Optional[float] = None

    async def crawl_category_by_filter(
        self, 
        page: Page, 
        base_url: str,
        category_code: Optional[str],
        category_name: str,
        max_announcements: int = 10,
        company_filter: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        allow_manual_captcha: bool = True,
        use_cloudscraper: bool = True,
        manual_captcha_timeout_seconds: int = 120
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
        if allow_manual_captcha:
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
            await self._wait_for_category_selector(
                page,
                allow_manual_captcha=allow_manual_captcha,
                timeout_seconds=manual_captcha_timeout_seconds,
            )

            # Select the category option by value (if provided)
            if category_code:
                await page.select_option('select[name="cat"]', value=category_code, timeout=5000)
                await page.wait_for_timeout(800)

            # Apply optional company/date filters before search
            if company_filter:
                await self._apply_company_filter(page, company_filter)
            if start_date or end_date:
                await self._apply_date_range(page, start_date, end_date)
            
            # Click Search button only if filters were applied or category was selected
            if category_code or company_filter or start_date or end_date:
                await page.wait_for_selector('.form-submit-btn', timeout=5000)
                await page.click('.form-submit-btn', timeout=5000)
                await page.wait_for_timeout(5000)  # Wait longer for AJAX results to load
            
        except Exception as e:
            print(f"Warning: Could not filter by category '{category_name}': {e}")
            if allow_manual_captcha:
                print("Manual Cloudflare verification enabled; skipping CloudScraper fallback to avoid page reset.")
            elif use_cloudscraper:
                print("Attempting CloudScraper fallback with proxy rotation...")
                loaded = await self._load_page_via_cloudscraper(
                    page,
                    base_url,
                    category_code=category_code,
                )
                if not loaded:
                    print("CloudScraper fallback failed; proceeding with current page content...")
            else:
                print("Attempting to proceed with current page content...")
            # Continue with current page content

        
        # Extract announcements from table with pagination
        announcements: List[Dict[str, Any]] = []
        seen_urls = set()

        # Bursa Malaysia shows ~20 per page; cap pages to avoid infinite loops
        rows_per_page = 20
        max_pages = max(1, math.ceil(max_announcements / rows_per_page))
        max_pages = min(max_pages, 20)
        # If using filters, scan a few extra pages to find matches even when max <= rows_per_page
        if company_filter or start_date or end_date:
            max_pages = max(max_pages, 5)

        for page_idx in range(max_pages):
            page_announcements = await self._extract_announcements_from_table(page, category_name)
            for ann in page_announcements:
                detail_url = ann.get("detail_page_url")
                if not detail_url or detail_url in seen_urls:
                    continue
                seen_urls.add(detail_url)
                announcements.append(ann)

                if len(announcements) >= max_announcements:
                    return announcements[:max_announcements]

            if len(announcements) >= max_announcements:
                break

            if page_idx == max_pages - 1:
                break

            moved = await self._go_to_next_page(page)
            if not moved:
                break

        return announcements[:max_announcements]

    async def get_category_options(self, page: Page) -> List[Dict[str, str]]:
        """
        Read category options from the listing page select.
        Returns list of {label, value}.
        """
        try:
            options = await page.evaluate(
                """() => {
                    const select = document.querySelector('select[name="cat"]');
                    if (!select) return [];
                    return Array.from(select.options || [])
                      .map(opt => ({
                        label: (opt.textContent || '').trim(),
                        value: (opt.value || '').trim()
                      }));
                }"""
            )
        except Exception:
            return []

        seen = set()
        cleaned: List[Dict[str, str]] = []
        for opt in options:
            label = (opt.get("label") or "").strip()
            value = (opt.get("value") or "").strip()
            if not value or not label:
                continue
            if label.lower() in {"all", "all announcements"}:
                continue
            key = f"{label}|{value}"
            if key in seen:
                continue
            seen.add(key)
            cleaned.append({"label": label, "value": value})

        return cleaned

    async def _apply_company_filter(self, page: Page, company_filter: List[str]) -> None:
        target = company_filter[0] if company_filter else None
        if not target:
            return

        normalized_target = " ".join(target.split()).strip().lower()

        # Try select dropdown first
        try:
            success = await page.evaluate(
                """(needle) => {
                    const selects = Array.from(document.querySelectorAll("select"));
                    for (const select of selects) {
                        const options = Array.from(select.options || []);
                        const match = options.find((opt) =>
                            opt.textContent && opt.textContent.toLowerCase().includes(needle)
                        );
                        if (match) {
                            select.value = match.value;
                            select.dispatchEvent(new Event("change", { bubbles: true }));
                            return true;
                        }
                    }
                    return false;
                }""",
                normalized_target,
            )
            if success:
                await page.wait_for_timeout(300)
                return
        except Exception:
            pass

        # Try input/autocomplete
        try:
            candidates = [
                "input[placeholder*='Company' i]",
                "input[name*='company' i]",
                "input[id*='company' i]",
            ]
            for selector in candidates:
                locator = page.locator(selector)
                if await locator.count() > 0:
                    await locator.first.fill(target)
                    await locator.first.press("Enter")
                    await page.wait_for_timeout(300)
                    return
        except Exception:
            pass

    async def _apply_date_range(self, page: Page, start_date: Optional[str], end_date: Optional[str]) -> None:
        try:
            if start_date:
                start_candidates = [
                    "input[placeholder*='Start' i]",
                    "input[name*='start' i]",
                    "input[id*='start' i]",
                ]
                for selector in start_candidates:
                    locator = page.locator(selector)
                    if await locator.count() > 0:
                        await locator.first.fill(start_date)
                        await locator.first.press("Enter")
                        break

            if end_date:
                end_candidates = [
                    "input[placeholder*='End' i]",
                    "input[name*='end' i]",
                    "input[id*='end' i]",
                ]
                for selector in end_candidates:
                    locator = page.locator(selector)
                    if await locator.count() > 0:
                        await locator.first.fill(end_date)
                        await locator.first.press("Enter")
                        break
        except Exception:
            pass

    async def _wait_for_category_selector(
        self,
        page: Page,
        allow_manual_captcha: bool,
        timeout_seconds: int = 60,
    ) -> None:
        deadline = time.time() + timeout_seconds
        last_error: Optional[Exception] = None

        while time.time() < deadline:
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=10000)
                await page.wait_for_selector('select[name="cat"]', timeout=5000, state="visible")
                return
            except Exception as e:
                last_error = e
                if allow_manual_captcha and await self._is_cloudflare_challenge(page):
                    print("Cloudflare challenge detected. Complete the verification in the browser...")
                    await page.wait_for_timeout(5000)
                    continue

                await page.wait_for_timeout(2000)

        if last_error:
            raise last_error

    async def _is_cloudflare_challenge(self, page: Page) -> bool:
        selectors = [
            "iframe[src*='challenges.cloudflare.com']",
            "iframe[src*='turnstile']",
            "div#cf-turnstile",
            "form#challenge-form",
            "div.cf-challenge",
        ]
        for selector in selectors:
            try:
                locator = page.locator(selector)
                if await locator.count() > 0:
                    return True
            except Exception:
                continue
        return False

    async def _load_page_via_cloudscraper(
        self,
        page: Page,
        base_url: str,
        category_code: Optional[str] = None,
    ) -> bool:
        try:
            import cloudscraper
            import requests
        except Exception as import_error:
            print(f"CloudScraper import failed: {import_error}")
            return False

        proxies = self._get_http_proxies()
        if not proxies:
            print("No proxies available for CloudScraper fallback.")
            return False

        # Attempt to load filtered page if supported by server
        url = base_url
        if category_code:
            url = f"{base_url}?cat={quote(category_code)}"

        try:
            scraper = cloudscraper.create_scraper()
            proxy = proxies[int(time.time()) % len(proxies)]
            response = scraper.get(url, timeout=30, proxies={"http": proxy, "https": proxy})
            if response.status_code != 200 or not response.text:
                print(f"CloudScraper HTTP {response.status_code} for {url}")
                return False

            await page.set_content(response.text, wait_until="domcontentloaded")
            return True
        except requests.RequestException as req_error:
            print(f"CloudScraper request failed: {req_error}")
            return False

    def _get_http_proxies(self, cache_ttl_seconds: int = 3600, limit: int = 200) -> List[str]:
        now = time.time()
        if self._proxy_cache and self._proxy_cache_at and (now - self._proxy_cache_at) < cache_ttl_seconds:
            return self._proxy_cache[:limit]

        proxy_list_url = "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
        proxies: List[str] = []
        try:
            import requests
            response = requests.get(proxy_list_url, timeout=20)
            if response.status_code != 200:
                print(f"Proxy list fetch failed with HTTP {response.status_code}")
                return []

            for line in response.text.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue
                if not line.startswith("http://") and not line.startswith("https://"):
                    line = f"http://{line}"
                proxies.append(line)

            self._proxy_cache = proxies
            self._proxy_cache_at = now
            return proxies[:limit]
        except Exception as e:
            print(f"Failed to fetch proxy list: {e}")
            return []
    
    async def _extract_announcements_from_table(
        self, 
        page: Page, 
        category: str = "Financial Result"
    ) -> List[Dict[str, Any]]:
        """
        Extract announcements from www.bursamalaysia.com table structure.
        
        Table columns: No., Announcement Date, Company Name, Title
        """
        announcements_data = await page.evaluate(r"""(category) => {
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
    
    async def _go_to_next_page(self, page: Page) -> bool:
        before_url = await self._get_first_detail_url(page)

        candidates = [
            "a[rel='next']",
            "a[aria-label*='Next']",
            "button[aria-label*='Next']",
            "a:has-text('Next')",
            "button:has-text('Next')",
            "a.pagination__next",
            "li.next a",
            "button:has-text('Load More')",
            "a:has-text('Load More')",
        ]

        next_locator = None
        for selector in candidates:
            locator = page.locator(selector)
            try:
                if await locator.count() > 0:
                    next_locator = locator.first
                    break
            except Exception:
                continue

        if not next_locator:
            return False

        try:
            await next_locator.click()
            await page.wait_for_load_state("domcontentloaded", timeout=10000)

            if before_url:
                try:
                    await page.wait_for_function(
                        """(prevUrl) => {
                            const link = document.querySelector('tbody tr td a[href*="announcement_details"]');
                            return link && link.href !== prevUrl;
                        }""",
                        before_url,
                        timeout=10000,
                    )
                except Exception:
                    pass

            after_url = await self._get_first_detail_url(page)
            if before_url and after_url and after_url == before_url:
                return False

            return True
        except Exception:
            return False

    async def _get_first_detail_url(self, page: Page) -> Optional[str]:
        try:
            return await page.evaluate(
                """() => {
                    const link = document.querySelector('tbody tr td a[href*="announcement_details"]');
                    return link ? link.href : null;
                }"""
            )
        except Exception:
            return None


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
