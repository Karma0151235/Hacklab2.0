from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import os
import base64
from typing import Optional, Dict

class PlaywrightBrowser:
    def __init__(self, video_dir: str = "/tmp/scrape_video_bursa"):
        self.video_dir = video_dir
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def launch(self, headless: bool = True) -> Browser:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        return self.browser

    async def create_context(self) -> BrowserContext:
        if not self.browser:
            await self.launch()

        # Ensure video dir exists
        if not os.path.exists(self.video_dir):
            try:
                os.makedirs(self.video_dir)
            except OSError:
                pass # Ignore if exists

        self.context = await self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US,en;q=0.9",
            viewport={"width": 1920, "height": 1080},
            record_video_dir=self.video_dir,
            record_video_size={"width": 1920, "height": 1080},
        )
        
        self.page = await self.context.new_page()
        return self.context

    async def inject_bounding_box_helpers(self) -> None:
        """Inject JavaScript utilities for bounding box drawing."""
        if not self.page:
            return

        await self.page.evaluate("""() => {
            window.scraperBoxes = [];

            window.drawBoundingBox = function(element, color = '#3b82f6', label = '', persistent = true) {
                if (!element) return null;

                const rect = element.getBoundingClientRect();
                const scrollY = window.pageYOffset || document.documentElement.scrollTop;
                const scrollX = window.pageXOffset || document.documentElement.scrollLeft;

                const box = document.createElement('div');
                box.className = 'scraper-highlight-box';
                box.style.cssText = `
                    position: absolute;
                    left: ${rect.left + scrollX}px;
                    top: ${rect.top + scrollY}px;
                    width: ${rect.width}px;
                    height: ${rect.height}px;
                    border: 3px solid ${color};
                    background: ${color}22;
                    box-shadow: 0 0 20px ${color}88;
                    pointer-events: none;
                    z-index: 999999;
                    transition: all 0.3s ease;
                `;

                if (label) {
                    const labelDiv = document.createElement('div');
                    labelDiv.textContent = label;
                    labelDiv.style.cssText = `
                        position: absolute;
                        top: -28px;
                        left: 0;
                        background: ${color};
                        color: white;
                        padding: 4px 10px;
                        border-radius: 4px;
                        font-size: 13px;
                        font-weight: bold;
                        white-space: nowrap;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                    `;
                    box.appendChild(labelDiv);
                }

                document.body.appendChild(box);

                if (persistent) {
                    window.scraperBoxes.push(box);
                } else {
                    setTimeout(() => box.remove(), 2000);
                }

                return box;
            };

            window.clearAllBoxes = function() {
                window.scraperBoxes.forEach(box => box.remove());
                window.scraperBoxes = [];
            };
        }""")

    async def finalize_video(self) -> str:
        """
        Close context to finalize WebM video, encode to base64.
        """
        video_base64 = ""
        MAX_VIDEO_SIZE = 30 * 1024 * 1024  # 30MB limit
        
        video_path = None
        if self.page:
            video_obj = self.page.video
            if video_obj:
                try:
                    video_path = await video_obj.path()
                except:
                    pass

        if self.context:
            await self.context.close()
            self.context = None
            
        if self.browser:
            await self.browser.close()
            self.browser = None
            
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        # Encode video to base64 if it exists and is not too large
        if video_path and os.path.exists(video_path):
            try:
                file_size = os.path.getsize(video_path)
                if file_size > MAX_VIDEO_SIZE:
                    print(f"⚠️  Video too large ({file_size / 1024 / 1024:.1f}MB), skipping base64 encoding")
                elif file_size > 0:
                    with open(video_path, "rb") as f:
                        video_bytes = f.read()
                    video_base64 = base64.b64encode(video_bytes).decode("utf-8")
                    print(f"✅ Video encoded: {file_size / 1024 / 1024:.1f}MB")
            except Exception as e:
                print(f"⚠️  Error encoding video: {e}")
                
        return video_base64

class BrowserSession:
    """Context manager for easy browser lifecycle management"""
    def __init__(self, video_dir: str = "/tmp/scrape_video_bursa"):
        self.browser = PlaywrightBrowser(video_dir)

    async def __aenter__(self):
        await self.browser.launch(headless=True) # Default to headless
        await self.browser.create_context()
        await self.browser.inject_bounding_box_helpers()
        return self.browser

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
             # If error, try to capture video anyway? 
             # finalize_video closes context/browser
             pass
        await self.browser.finalize_video()
