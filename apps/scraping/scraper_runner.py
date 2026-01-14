import asyncio
import os
import sys
import json
import base64
import re
from datetime import datetime

# Add project root to Python path
# Get the directory containing this file (apps/scraping/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get parent directory (apps/)
apps_dir = os.path.dirname(current_dir)
# Get grandparent directory (project root)
project_root = os.path.dirname(apps_dir)
# Add to path so 'apps' module can be imported
sys.path.insert(0, project_root)

# Force UTF-8 stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from apps.scraping.bursa_web_scraper import BursaWebScraper, CATEGORY_CONFIG

class ScraperRunner:
    """
    Entry point for running the Bursa Malaysia web scraper.
    Saves output to apps/storage/raw/bursa/{category}/{date}/
    """
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # Output to apps/storage/raw/bursa/
        self.output_dir = os.path.join(self.base_dir, "../storage/raw/bursa")
        self.video_dir = os.path.join(self.output_dir, "videos")
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
        if not os.path.exists(self.video_dir):
            os.makedirs(self.video_dir, exist_ok=True)

    async def run(self, year: int = 2025, max_announcements: int = 5, scrape_all_categories: bool = False):
        """
        Run the scraper and save dual outputs.
        
        Args:
            year: Year to filter announcements
            max_announcements: Maximum announcements per category
            scrape_all_categories: If True, scrapes all categories; else scrapes "All Announcements"
        """
        print("🚀 Starting Bursa Malaysia Web Scraper...")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"🎯 Target: {max_announcements} announcements")
        print(f"🗂️  Categories: {'All categories' if scrape_all_categories else 'Financial Result only'}")
        
        scraper = BursaWebScraper()
        
        try:
            result = await scraper.scrape(
                year=year,
                max_announcements=max_announcements,
                categories=None,
                scrape_all_categories=scrape_all_categories
            )
            
            # Save individual announcement files organized by category and date
            saved_count = 0
            category_dirs = {}
            
            for idx, (struct_record, doc_object) in enumerate(zip(result['structured_records'], result['document_objects'])):
                # Get category from structured record
                category = struct_record.category or "Unknown"
                
                # Map category to folder name using CATEGORY_CONFIG
                category_folder = None
                for cat_name, config in CATEGORY_CONFIG.items():
                    if cat_name == category or category.lower() in cat_name.lower():
                        category_folder = config["folder_name"]
                        break
                
                # Fallback: sanitize category name if not found in config
                if not category_folder:
                    category_folder = self._sanitize_folder_name(category)
                
                # Parse announcement date (format: "DD MMM YYYY" or "YYYY-MM-DD")
                announcement_date = struct_record.announcement_date or ""
                
                # Normalize date to YYYY-MM-DD format
                try:
                    if announcement_date:
                        # Try parsing "07 Jan 2026" format
                        try:
                            parsed = datetime.strptime(announcement_date, "%d %b %Y")
                        except:
                            # Try "2026-01-07" format
                            try:
                                parsed = datetime.strptime(announcement_date, "%Y-%m-%d")
                            except:
                                # Fallback to current date
                                parsed = datetime.now()
                        
                        date_str = parsed.strftime("%Y-%m-%d")
                        date_for_filename = parsed.strftime("%Y%m%d")
                    else:
                        # No date, use current
                        date_str = datetime.now().strftime("%Y-%m-%d")
                        date_for_filename = datetime.now().strftime("%Y%m%d")
                except:
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    date_for_filename = datetime.now().strftime("%Y%m%d")
                
                # Create category/date directory structure
                category_dir = os.path.join(self.output_dir, category_folder)
                date_dir = os.path.join(category_dir, date_str)
                
                if not os.path.exists(date_dir):
                    os.makedirs(date_dir, exist_ok=True)
                    
                # Track directories for reporting
                if category_folder not in category_dirs:
                    category_dirs[category_folder] = set()
                category_dirs[category_folder].add(date_str)
                
                # Extract company name with improved logic
                company_name = self._extract_company_name(struct_record, doc_object)
                
                # Sanitize company name for filename
                company_sanitized = self._sanitize_filename(company_name)
                
                # Generate filename: BURSA_{CompanyName}_{DATE}_{ID}.json
                announcement_id = struct_record.announcement_id or str(idx).zfill(3)
                filename = f"BURSA_{company_sanitized}_{date_for_filename}_{announcement_id}.json"
                
                # Combine structured + document into single JSON
                combined = {
                    "structured_record": struct_record.model_dump(),
                    "document_object": doc_object.model_dump()
                }
                
                file_path = os.path.join(date_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(combined, f, indent=2, ensure_ascii=False)
                
                saved_count += 1
            
            print(f"\n✅ Saved {saved_count} announcements")
            print(f"📊 Directory structure:")
            for category_folder in sorted(category_dirs.keys()):
                dates = category_dirs[category_folder]
                print(f"   📁 {category_folder}/ ({len(dates)} dates)")
                for date in sorted(dates):
                    print(f"      📅 {date}/")
            
            # Save markdown report
            report_path = os.path.join(self.output_dir, "report.md")
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(result['report_markdown'])
            print(f"\n✅ Saved markdown report")
            
            # Save video file if available
            if result.get('video_base64') and len(result['video_base64']) > 0:
                video_filename = f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"
                video_path = os.path.join(self.video_dir, video_filename)
                
                # Decode base64 and save
                video_bytes = base64.b64decode(result['video_base64'])
                with open(video_path, 'wb') as f:
                    f.write(video_bytes)
                
                print(f"🎥 Saved video: {video_filename} ({len(video_bytes) / 1024 / 1024:.1f}MB)")
            
            print(f"\n🎉 Scraping complete! Total announcements: {result['total_announcements']}")
            return result
            
        except Exception as e:
            print(f"❌ Scraping failed: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _extract_company_name(self, struct_record, doc_object) -> str:
        """Extract company name from structured record or document object."""
        # Try struct_record.company_code first
        if struct_record.company_code and struct_record.company_code not in ['Reference Number', 'UNKNOWN', None]:
            return struct_record.company_code
        
        # Try to find Stock Name or Company Name from document object tables
        if hasattr(doc_object, 'tables') and doc_object.tables:
            for table in doc_object.tables:
                if table.get('title', '').lower() == 'announcement info':
                    for row in table.get('rows', []):
                        # Check for Stock Name
                        if 'Stock Name' in row and row['Stock Name']:
                            return row['Stock Name']
                        # Check for Company Name value
                        if 'Company Name' in row:
                            for key, value in row.items():
                                if key != 'Company Name' and value and len(str(value)) > 2:
                                    return str(value)
            
            # Fallback: Look in all tables
            for table in doc_object.tables:
                for row in table.get('rows', []):
                    for key in ['Stock Name', 'Company Name']:
                        if key in row and row[key] and len(str(row[key])) > 2:
                            value = str(row[key])
                            if value != key:
                                return value
        
        # Final fallback: Use announcement ID
        return struct_record.announcement_id or "UNKNOWN"
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize name for use in filename."""
        # Remove special characters, keep only alphanumeric, spaces, and hyphens
        sanitized = re.sub(r'[^\w\s-]', '', name)
        # Replace spaces with underscores
        sanitized = sanitized.replace(' ', '_')
        # Uppercase
        sanitized = sanitized.upper()
        # Limit length
        return sanitized[:50] if len(sanitized) > 50 else sanitized
    
    def _sanitize_folder_name(self, category: str) -> str:
        """Sanitize category name for use as folder name."""
        # Convert to lowercase and replace spaces with underscores
        sanitized = category.lower().replace(' ', '_')
        # Remove special characters
        sanitized = re.sub(r'[^\w_-]', '', sanitized)
        return sanitized

if __name__ == "__main__":
    import sys
    max_announcements = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    scrape_all = sys.argv[2].lower() == 'true' if len(sys.argv) > 2 else False
    
    runner = ScraperRunner()
    asyncio.run(runner.run(max_announcements=max_announcements, scrape_all_categories=scrape_all))
