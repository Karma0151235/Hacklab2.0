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

from apps.scraping.browser.playwright import PlaywrightBrowser
from apps.scraping.progress.redis_store import ProgressTracker
from apps.scraping.bursa.listing_crawler import BursaListingCrawler
from apps.scraping.bursa.announcement_fetcher import BursaAnnouncementFetcher
from apps.scraping.bursa.html_parser import BursaHTMLParser
from apps.scraping.common.schemas import StructuredRecord, DocumentObject

# Category configuration: Only Financial Result
CATEGORY_CONFIG = {
    "Financial Result": {
        "cat_id": 10820,
        "folder_name": "financial_result",
        "url": "https://bursa-bm.listedcompany.com/newsroom.html/cat/10820"
    }
}

class BursaWebScraper:
    """
    Main orchestrator for Bursa Malaysia announcements scraping.
    Implements the complete vision with dual outputs, bounding boxes, and video recording.
    """
    def __init__(self, progress_callback=None):
        self.progress_tracker = ProgressTracker(task_id="bursa_scrape")
        self.base_url = "https://bursa-bm.listedcompany.com/newsroom.html"
        self.announcements = []
        self.structured_records = []
        self.document_objects = []

    async def scrape(
        self,
        year: int = 2025,
        max_announcements: int = 10,
        categories: List[str] = None,
        scrape_all_categories: bool = False
    ) -> Dict[str, Any]:
        """
        Main scraping method implementing Phases 1-12.
        
        Args:
            year: Year to filter announcements
            max_announcements: Maximum announcements per category
            categories: Specific categories to scrape (if None and scrape_all_categories=False, scrapes "All Announcements")
            scrape_all_categories: If True, iterates through all available categories
        
        Returns:
            Dict containing structured_records, document_objects, video_base64, and report
        """
        browser = PlaywrightBrowser()
        
        try:
            # Phase 1-2: Initialize browser & video recording
            await self.progress_tracker.emit_progress("loading", 10, "Launching browser...")
            await browser.launch(headless=True)
            await browser.create_context()
            page = browser.page
            
            # Phase 3: Inject bounding box helpers
            await self.progress_tracker.emit_progress("loading", 25, "Injecting visual tracking...")
            await browser.inject_bounding_box_helpers()
            
            # Phase 4: Navigate to listing page
            await self.progress_tracker.emit_progress("loading", 35, "Navigating to Bursa...")
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
            
            await self.progress_tracker.emit_progress(
                "detecting", 
                40, 
                f"Scraping {len(categories_to_scrape)} categories..."
            )
            
            # Phase 6: Iterate through categories using direct URLs
            crawler = BursaListingCrawler()
            
            for cat_idx, (category_name, config) in enumerate(categories_to_scrape):
                cat_progress = 40 + int((cat_idx / len(categories_to_scrape)) * 20)
                await self.progress_tracker.emit_progress(
                    "detecting",
                    cat_progress,
                    f"Category: {category_name}"
                )
                
                # Navigate directly to category URL
                category_announcements = await crawler.crawl_category_by_url(
                    page, 
                    config["url"],
                    category_name,
                    max_announcements
                )
                
                # Highlight announcements on listing page
                await crawler.highlight_announcements_on_page(page, category_announcements)
                
                # Add to main announcements list
                self.announcements.extend(category_announcements)
            
            
            
            # Phase 7: Scrape each announcement detail page
            await self.progress_tracker.emit_progress("scraping", 60, f"Processing {len(self.announcements)} announcements...")
            
            fetcher = BursaAnnouncementFetcher()
            parser = BursaHTMLParser()
            
            for idx, announcement in enumerate(self.announcements):
                progress_percent = 60 + int((idx / len(self.announcements)) * 25)
                await self.progress_tracker.emit_progress(
                    "scraping",
                    progress_percent,
                    f"Scraping {idx + 1}/{len(self.announcements)}: {announcement['title'][:30]}..."
                )
                
                # Navigate to detail page
                success = await fetcher.fetch_detail_page(page, announcement['detail_page_url'])
                if not success:
                    continue
                
                # Re-inject helpers on detail page
                await browser.inject_bounding_box_helpers()
                
                # Clear previous boxes (safely)
                try:
                    await page.evaluate('if (window.clearAllBoxes) window.clearAllBoxes()')
                except:
                    pass
                
                # Extract tables and text
                tables_data = await parser.extract_tables(page)
                raw_text = await parser.extract_all_text(page)
                
                # Highlight tables
                await parser.highlight_tables(page, tables_data)
                
                # Create dual outputs
                structured_record = self._create_structured_record(announcement, tables_data)
                document_object = self._create_document_object(announcement, tables_data, raw_text)
                
                self.structured_records.append(structured_record)
                self.document_objects.append(document_object)
                
                await page.wait_for_timeout(1500)
            
            # Phase 7: Finalize video
            await self.progress_tracker.emit_progress("finalizing", 92, "Finalizing video...")
            video_base64 = await browser.finalize_video()
            
            # Phase 8: Generate report
            await self.progress_tracker.emit_progress("generating", 98, "Generating report...")
            report_markdown = self._generate_report()
            
            # Phase 9: Return results
            await self.progress_tracker.emit_progress("complete", 100, "Scraping complete!")
            
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
            await self.progress_tracker.emit_progress("error", 0, f"Scraping failed: {str(e)}")
            raise
        finally:
            if browser.browser:
                await browser.finalize_video()

    def _create_structured_record(self, announcement: Dict[str, Any], tables_data: List[Dict]) -> StructuredRecord:
        """Create structured record for SQL/Dashboard (Phase 7)."""
        # Extract company name with multiple fallback strategies
        company_code = self._extract_company_name(tables_data)
        
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
            announcement_id=announcement.get('detail_page_url', '').split('/')[-1] or 'unknown',
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
        announcement_id = announcement.get('detail_page_url', '').split('/')[-1] or 'unknown'
        doc_id = f"bursa_{announcement_id}_{int(datetime.utcnow().timestamp())}"
        
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
        company_code = self._extract_company_name(tables_data)
        
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
    
    def _extract_company_name(self, tables_data: List[Dict]) -> str:
        """Extract company name from tables with multiple fallback strategies."""
        # Strategy 1: Look for Stock Name or Company Name in "Announcement Info" table
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
        
        # Strategy 2: Look for any company-related field in any table
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
