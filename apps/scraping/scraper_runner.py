import asyncio
import os
import sys
import json
import base64
from datetime import datetime

# Force UTF-8 stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from apps.scraping.bursa_web_scraper import BursaWebScraper

class ScraperRunner:
    """
    Entry point for running the Bursa Malaysia web scraper.
    Saves output to apps/storage/raw/bursa/
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

    async def run(self, year: int = 2025, max_announcements: int = 5):
        """
        Run the scraper and save dual outputs.
        """
        print("🚀 Starting Bursa Malaysia Web Scraper...")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"🎯 Target: {max_announcements} announcements")
        
        scraper = BursaWebScraper()
        
        try:
            result = await scraper.scrape(
                year=year,
                max_announcements=max_announcements,
                categories=None
            )
            
            # Save individual announcement files organized by date
            saved_count = 0
            date_dirs = set()
            
            for idx, (struct_record, doc_object) in enumerate(zip(result['structured_records'], result['document_objects'])):
                # Parse announcement date (format: "DD MMM YYYY" or "YYYY-MM-DD")
                announcement_date = struct_record.announcement_date or ""
                
                # Normalize date to YYYY-MM-DD format
                try:
                    from datetime import datetime
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
                
                # Create date directory
                date_dir = os.path.join(self.output_dir, date_str)
                if not os.path.exists(date_dir):
                    os.makedirs(date_dir, exist_ok=True)
                    date_dirs.add(date_str)
                
                # Generate filename: BURSA_{COMPANY}_{DATE}_{ID}.json
                company = (struct_record.company_code or "UNKNOWN").replace(" ", "_").upper()
                announcement_id = struct_record.announcement_id or str(idx).zfill(3)
                filename = f"BURSA_{company}_{date_for_filename}_{announcement_id}.json"
                
                # Combine structured + document into single JSON
                combined = {
                    "structured_record": struct_record.model_dump(),
                    "document_object": doc_object.model_dump()
                }
                
                file_path = os.path.join(date_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(combined, f, indent=2, ensure_ascii=False)
                
                saved_count += 1
            
            print(f"✅ Saved {saved_count} announcements across {len(date_dirs)} date directories")
            for date_dir in sorted(date_dirs):
                print(f"   📁 {date_dir}/")
            
            
            # Save markdown report
            report_path = os.path.join(self.output_dir, "report.md")
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(result['report_markdown'])
            print(f"✅ Saved markdown report")
            
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

if __name__ == "__main__":
    import sys
    max_announcements = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    
    runner = ScraperRunner()
    asyncio.run(runner.run(max_announcements=max_announcements))
