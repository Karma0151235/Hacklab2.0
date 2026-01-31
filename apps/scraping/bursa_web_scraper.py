import asyncio
import os
import sys
import json
import re
from datetime import datetime
from typing import List, Dict, Any

# Force UTF-8 stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from scraping.browser.playwright import PlaywrightBrowser
from scraping.progress.redis_store import ProgressTracker
from scraping.bursa.listing_crawler import BursaListingCrawler
from scraping.bursa.announcement_fetcher import BursaAnnouncementFetcher
from scraping.bursa.html_parser import BursaHTMLParser
from scraping.common.schemas import StructuredRecord, DocumentObject
from etl.logging_config import get_logger

logger = get_logger(__name__)

# Category configuration: Financial Results on www.bursamalaysia.com
CATEGORY_CONFIG = {
    "Financial Result": {
        "cat_code": "FA,FRCO",  # Category code for API filtering
        "folder_name": "financial_result",
        "url": "https://www.bursamalaysia.com/market_information/announcements/company_announcement"
    }
}

class BursaWebScraper:
    """
    Main orchestrator for Bursa Malaysia announcements scraping.
    Implements the complete vision with dual outputs, bounding boxes, and video recording.
    """
    def __init__(self, progress_callback=None):
        self.progress_tracker = ProgressTracker(task_id="bursa_scrape")
        self.progress_callback = progress_callback
        self.base_url = "https://www.bursamalaysia.com/market_information/announcements/company_announcement"
        self.announcements = []
        self.structured_records = []
        self.document_objects = []

    async def scrape(
        self,
        year: int = 2025,
        max_announcements: int = 10,
        company_filter: List[str] = None,
        categories: List[str] = None,
        scrape_all_categories: bool = False,
        resource_efficient: bool = False,
        use_cloudscraper: bool = True,
        manual_captcha_timeout_seconds: int = 120
    ) -> Dict[str, Any]:
        """
        Main scraping method implementing Phases 1-12.
        
        Args:
            year: Year to filter announcements
            max_announcements: Maximum announcements per category
            company_filter: List of company names/codes to filter (e.g., ["MAYBANK", "CIMB"])
            categories: Specific categories to scrape (if None and scrape_all_categories=False, scrapes "All Announcements")
            scrape_all_categories: If True, iterates through all available categories
        
        Returns:
            Dict containing structured_records, document_objects, video_base64, and report
        """
        browser = PlaywrightBrowser()
        
        try:
            # Phase 1-2: Initialize browser & video recording
            await self._emit_progress("loading", 10, "Launching browser...")
            if resource_efficient:
                await browser.launch(headless=True)
                await browser.create_context(
                    record_video=False,
                    viewport={"width": 1280, "height": 720},
                    block_resources=True,
                )
            else:
                # Level 1 Cloudflare Bypass: headless=False to appear human
                await browser.launch(headless=False)  # VISIBLE BROWSER - Can manually solve CAPTCHA
                await browser.create_context()
            page = browser.page
            
            # Phase 3: Inject bounding box helpers
            if not resource_efficient:
                await self._emit_progress("loading", 25, "Injecting visual tracking...")
                await browser.inject_bounding_box_helpers()
            
            # Phase 4: Navigate to listing page
            await self._emit_progress("loading", 35, "Navigating to Bursa...")
            listing_url = self.base_url
            await page.goto(listing_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)
            
            
            
            # Phase 5: Determine which categories to scrape (now only Financial Result)
            if scrape_all_categories:
                categories_to_scrape = list(CATEGORY_CONFIG.items())
            elif categories:
                # Filter to requested categories
                categories_to_scrape = [(k, v) for k, v in CATEGORY_CONFIG.items() if k in categories]
            else:
                # Default: scrape only Financial Result
                categories_to_scrape = [("Financial Result", CATEGORY_CONFIG["Financial Result"])]
            
            await self._emit_progress(
                "detecting", 
                40, 
                f"Scraping {len(categories_to_scrape)} categories...",
                metadata={"categories": [name for name, _ in categories_to_scrape]}
            )
            
            # Phase 6: Iterate through categories using direct URLs
            crawler = BursaListingCrawler()
            
            for cat_idx, (category_name, config) in enumerate(categories_to_scrape):
                cat_progress = 40 + int((cat_idx / len(categories_to_scrape)) * 20)
                await self._emit_progress(
                    "detecting",
                    cat_progress,
                    f"Category: {category_name}",
                    metadata={"category": category_name}
                )
                
                
                # Navigate to base URL and filter by category
                category_announcements = await crawler.crawl_category_by_filter(
                    page, 
                    self.base_url,
                    config["cat_code"],  # Use category code for filtering
                    category_name,
                    max_announcements,
                    allow_manual_captcha=not resource_efficient,
                    use_cloudscraper=use_cloudscraper,
                    manual_captcha_timeout_seconds=manual_captcha_timeout_seconds
                )
                
                # Apply company filter if specified
                if company_filter:
                    filtered_announcements = []
                    for ann in category_announcements:
                        company_name = ann.get('company_name', '').upper()
                        # Check if any filter term matches the company name
                        if any(filter_term.upper() in company_name for filter_term in company_filter):
                            filtered_announcements.append(ann)
                    
                    logger.info(f"[Company Filter] Filtered {len(category_announcements)} → {len(filtered_announcements)} announcements")
                    category_announcements = filtered_announcements
                
                # Highlight announcements on listing page
                if not resource_efficient:
                    await crawler.highlight_announcements_on_page(page, category_announcements)
                
                # Add to main announcements list
                self.announcements.extend(category_announcements)
            
            
            
            # Phase 7: Scrape each announcement detail page
            await self._emit_progress(
                "scraping",
                60,
                f"Processing {len(self.announcements)} announcements...",
                metadata={"scraped_count": 0, "total_announcements": len(self.announcements)}
            )
            
            fetcher = BursaAnnouncementFetcher()
            parser = BursaHTMLParser()
            
            for idx, announcement in enumerate(self.announcements):
                progress_percent = 60 + int((idx / len(self.announcements)) * 25)
                await self._emit_progress(
                    "scraping",
                    progress_percent,
                    f"Scraping {idx + 1}/{len(self.announcements)}: {announcement['title'][:30]}...",
                    metadata={"scraped_count": idx + 1, "total_announcements": len(self.announcements)}
                )
                
                # Navigate to detail page
                success = await fetcher.fetch_detail_page(page, announcement['detail_page_url'])
                if not success:
                    continue
                
                # Re-inject helpers on detail page
                if not resource_efficient:
                    await browser.inject_bounding_box_helpers()
                
                # Clear previous boxes (safely)
                if not resource_efficient:
                    try:
                        await page.evaluate('if (window.clearAllBoxes) window.clearAllBoxes()')
                    except:
                        pass
                
                # Extract tables from main page
                tables_data = await parser.extract_tables(page)
                print(f"  Main page: {len(tables_data)} tables")
                
                # Extract tables from iframes (where financial data is)
                iframe_tables = await parser.extract_iframe_tables(page)
                print(f"  Iframes: {len(iframe_tables)} tables")
                
                # Merge all tables
                all_tables = tables_data + iframe_tables
                print(f"  Total tables: {len(all_tables)}")
                
                raw_text = await parser.extract_all_text(page)
                
                # Highlight ALL tables (including iframe tables)
                if not resource_efficient:
                    await parser.highlight_tables(page, all_tables)
                
                # Create dual outputs with all tables
                structured_record = self._create_structured_record(announcement, all_tables)
                document_object = self._create_document_object(announcement, all_tables, raw_text)

                
                self.structured_records.append(structured_record)
                self.document_objects.append(document_object)
                
                await page.wait_for_timeout(1500)
            
            # Phase 7: Finalize video
            await self._emit_progress("finalizing", 92, "Finalizing video...")
            video_base64 = await browser.finalize_video()
            
            # Phase 8: Generate report
            await self._emit_progress("generating", 98, "Generating report...")
            report_markdown = self._generate_report()
            
            # Phase 9: Return results
            await self._emit_progress("complete", 100, "Scraping complete!")
            
            return {
                "status": "success",
                "structured_records": self.structured_records,
                "document_objects": self.document_objects,
                "video_base64": video_base64,
                "report_markdown": report_markdown,
                "total_announcements": len(self.announcements),
                "timestamp": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            await self._emit_progress("error", 0, f"Scraping failed: {str(e)}")
            raise
        finally:
            if browser.browser:
                await browser.finalize_video()

    async def _emit_progress(self, phase: str, percent: int, message: str, metadata: Dict[str, Any] = None):
        await self.progress_tracker.emit_progress(phase, percent, message, metadata=metadata)
        if self.progress_callback:
            try:
                self.progress_callback(phase, percent, message, metadata or {})
            except Exception:
                pass

    def _create_structured_record(self, announcement: Dict[str, Any], tables_data: List[Dict]) -> StructuredRecord:
        """Create structured record for SQL/Dashboard (Phase 7)."""
        # Extract company name with multiple fallback strategies
        company_code = self._extract_company_name(announcement, tables_data)
        
        # Extract numeric fields
        numeric_data = {}
        for table in tables_data:
            for row in table.get('rows', []):
                for key, value in row.items():
                    if value and isinstance(value, str):
                        if '%' in value:
                            try:
                                numeric_data[key + '_percent'] = float(value.replace('%', '').strip())
                            except:
                                pass
                        elif any(c.isdigit() for c in value):
                            try:
                                clean_val = value.replace(',', '').replace(' ', '')
                                numeric_data[key] = float(clean_val) if '.' in clean_val else int(clean_val)
                            except:
                                pass
        
        return StructuredRecord(
            announcement_id=announcement.get('announcement_id', 'unknown'),  # Use ann_id from listing
            company_code=company_code,
            announcement_date=announcement.get('date', ''),
            category=announcement.get('category', ''),
            title=announcement.get('title', ''),
            detail_page_url=announcement.get('detail_page_url', ''),
            pdf_urls=announcement.get('pdf_urls', []),
            tables_count=len(tables_data),
            table_titles=[t.get('title', '') for t in tables_data],
            numeric_fields=numeric_data,
            extracted_at=datetime.utcnow().isoformat(),
        )

    def _create_document_object(self, announcement: Dict[str, Any], tables_data: List[Dict], raw_text: str) -> DocumentObject:
        """Create document object for NLP/RAG (Phase 8)."""
        announcement_id = announcement.get('announcement_id')
        if not announcement_id:
            detail_url = announcement.get('detail_page_url', '')
            match = re.search(r"ann_id=([^&]+)", detail_url)
            if match:
                announcement_id = match.group(1)
            else:
                announcement_id = detail_url.split('/')[-1] or 'unknown'
        doc_id = f"bursa_{announcement_id}"
        
        # Determine doc_type from category
        category = announcement.get('category', '').lower()
        doc_type = "announcement"
        if 'dividend' in category:
            doc_type = "dividend"
        elif 'acquisition' in category:
            doc_type = "acquisition"
        elif 'notice' in category:
            doc_type = "notice"
        
        
        # Extract company name with multiple fallback strategies
        company_code = self._extract_company_name(announcement, tables_data)
        
        # Build metadata from tables
        metadata = {}
        for table in tables_data:
            table_key = table.get('title', '').lower().replace(' ', '_')
            if len(table.get('rows', [])) == 1:
                for key, value in table['rows'][0].items():
                    metadata[f"{table_key}_{key.lower().replace(' ', '_')}"] = value
            else:
                metadata[f"{table_key}_rows_count"] = len(table.get('rows', []))
        
        return DocumentObject(
            doc_id=doc_id,
            announcement_id=announcement_id,
            company_code=company_code,
            doc_type=doc_type,
            category=announcement.get('category', ''),
            title=announcement.get('title', ''),
            raw_text=raw_text,
            tables=[{
                "title": t.get('title', ''),
                "headers": t.get('headers', []),
                "rows": t.get('rows', []),
            } for t in tables_data],
            metadata=metadata,
            announcement_date=announcement.get('date', ''),
            extracted_at=datetime.utcnow().isoformat(),
            source_url=announcement.get('detail_page_url', ''),
            pdf_urls=announcement.get('pdf_urls', []),
            keywords=self._extract_keywords(announcement.get('title', '') + ' ' + raw_text[:500]),
            summary=raw_text[:200] + "..." if len(raw_text) > 200 else raw_text,
        )
    
    
    def _extract_company_name(self, announcement: Dict, tables_data: List[Dict]) -> str:
        """
        Extract company name with multiple fallback strategies.
        
        Priority:
        1. Company name from listing table (new www.bursamalaysia.com)
        2. Stock Name/Company Name from detail page tables
        3. Announcement ID as fallback
        """
        # Strategy 1: Use company_name from listing (available on new site)
        if announcement.get('company_name') and announcement['company_name'] not in ['N/A', 'Unknown', '']:
            return announcement['company_name']
        
        # Strategy 2: Look for Stock Name or Company Name in "Announcement Info" table
        for table in tables_data:
            if table.get('title', '').lower() == 'announcement info':
                for row in table.get('rows', []):
                    # Check for Stock Name
                    if 'Stock Name' in row and row['Stock Name']:
                        return row['Stock Name']
                    # Check for Company Name as a key
                    if 'Company Name' in row:
                        # The value might be in a different column
                        for key, value in row.items():
                            if key != 'Company Name' and value and len(value) > 2:
                                return value
        
        # Strategy 3: Look for any company-related field in any table
        for table in tables_data:
            for row in table.get('rows', []):
                for key in ['Stock Name', 'Company Name', 'Stock Code', 'Code', 'Symbol', 'Company Code']:
                    if key in row and row[key]:
                        value = row[key]
                        # Skip if it's just the key repeated or too short
                        if value != key and len(value) > 2:
                            return value
        
        # Fallback: Return None (will be handled by scraper_runner)
        return None

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        words = re.findall(r'\b[A-Z][a-z]+\b|\b[A-Z]{2,}\b', text)
        return list(set(words))[:10]

    def _generate_report(self) -> str:
        """Generate markdown report (Phase 11)."""
        markdown = f"""# Bursa Malaysia Scraping Report
*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*

## Summary
- **Announcements Scraped**: {len(self.announcements)}
- **Structured Records**: {len(self.structured_records)}
- **Document Objects**: {len(self.document_objects)}

## Announcements

"""
        for idx, record in enumerate(self.structured_records, 1):
            markdown += f"""### {idx}. {record.title}
- **Date**: {record.announcement_date}
- **Category**: {record.category}
- **Company**: {record.company_code or 'N/A'}
- **Tables**: {record.tables_count}

"""
        
        markdown += """
## Outputs
- **structured_records.json**: For SQL/Dashboard ingestion
- **document_objects.json**: For NLP/RAG systems
"""
        return markdown
