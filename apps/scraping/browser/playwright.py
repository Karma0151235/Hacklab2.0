"""
Playwright Browser Management

Implements Playwright-based browser automation with:
- Anti-bot detection
- Video recording (WebM)
- Bounding box visualization
- Real-time progress tracking

Reference: BursaWebScraper.md
"""

import asyncio
import base64
import os
import tempfile
from typing import Callable, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from loguru import logger

from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class PlaywrightBrowser:
    """Manage Playwright browser lifecycle with video recording."""

    def __init__(
        self,
        headless: bool = True,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        video_dir: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
    ):
        """
        Initialize Playwright browser configuration.

        Args:
            headless: Run in headless mode (production)
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
            video_dir: Directory to store video recordings
            progress_callback: Async callback for progress updates
        """
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.video_dir = video_dir or tempfile.mkdtemp(prefix="scrape_video_")
        self.progress_callback = progress_callback
        self.logger = logger

        # Ensure video directory exists
        Path(self.video_dir).mkdir(parents=True, exist_ok=True)

    async def launch(self) -> Browser:
        """
        Launch Chromium browser with anti-detection settings.

        Returns:
            Playwright Browser instance
        """
        await self._emit_progress("loading", 10, "Launching Chromium browser...")

        p = await async_playwright().start()

        browser = await p.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",  # Hide automation flag
                "--no-sandbox",  # Allow in containers
                "--disable-dev-shm-usage",  # Fix for Docker/Linux
            ],
        )

        self.logger.info("Browser launched successfully")
        return browser

    async def create_context(self, browser: Browser, locale: str = "en-MY") -> BrowserContext:
        """
        Create browser context with video recording.

        Args:
            browser: Playwright Browser instance
            locale: Browser locale (en-MY for Malaysia)

        Returns:
            BrowserContext with recording enabled
        """
        await self._emit_progress("loading", 20, "Configuring video recording...")

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale=locale,
            viewport={"width": self.viewport_width, "height": self.viewport_height},
            record_video_dir=self.video_dir,
            record_video_size={"width": self.viewport_width, "height": self.viewport_height},
        )

        self.logger.info(f"Browser context created with video recording to {self.video_dir}")
        return context

    async def inject_bounding_box_helpers(self, page: Page) -> None:
        """
        Inject JavaScript utilities for bounding box drawing.

        Adds window.drawBoundingBox() and window.clearAllBoxes() functions.
        Ref: WebScraper.md § Bounding Box System
        """
        await self._emit_progress("loading", 25, "Injecting bounding box utilities...")

        await page.evaluate("""() => {
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

        self.logger.info("Bounding box helpers injected")

    async def navigate(self, page: Page, url: str, timeout: int = 30000) -> None:
        """
        Navigate to URL with timeout handling.

        Args:
            page: Playwright Page instance
            url: Target URL
            timeout: Navigation timeout in ms
        """
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            await page.wait_for_timeout(2000)  # Stabilization delay
            self.logger.info(f"Navigated to {url}")
        except Exception as e:
            self.logger.warning(f"Navigation to {url} timed out: {e}")
            # Graceful degradation - continue with partial content

    async def finalize_video(self, context: BrowserContext) -> str:
        """
        Finalize video recording and return base64 encoded WebM.

        Critical: Closing context triggers WebM finalization.

        Args:
            context: BrowserContext with active video recording

        Returns:
            Base64-encoded video string (or empty if too large)
        """
        await self._emit_progress("finalizing", 92, "Finalizing video recording...")

        video_base64 = ""
        MAX_VIDEO_SIZE = 30 * 1024 * 1024  # 30MB limit for gRPC

        try:
            # Close context to finalize video
            await context.close()

            # Find the WebM file
            video_files = list(Path(self.video_dir).glob("*.webm"))
            if not video_files:
                self.logger.warning("No video file found after context close")
                return ""

            video_path = video_files[0]
            file_size = video_path.stat().st_size

            if file_size > MAX_VIDEO_SIZE:
                self.logger.warning(f"Video too large ({file_size / 1024 / 1024:.1f}MB), skipping")
                return ""

            # Encode to base64
            with open(video_path, "rb") as f:
                video_bytes = f.read()

            video_base64 = base64.b64encode(video_bytes).decode("utf-8")
            self.logger.info(f"Video encoded: {len(video_base64)} chars ({file_size / 1024 / 1024:.1f}MB)")

        except Exception as e:
            self.logger.error(f"Error finalizing video: {e}", exc_info=True)

        return video_base64

    async def _emit_progress(self, phase: str, percent: int, message: str) -> None:
        """Emit progress update via callback."""
        if not self.progress_callback:
            return

        try:
            await self.progress_callback(
                phase=phase,
                progress_percent=percent,
                status_message=message,
                metadata={}
            )
        except Exception as e:
            self.logger.warning(f"Progress callback failed: {e}")


class BrowserSession:
    """Context manager for browser session with automatic cleanup."""

    def __init__(self, playwright_config: PlaywrightBrowser):
        self.config = playwright_config
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.logger = logger

    async def __aenter__(self):
        """Launch browser and create context."""
        self.playwright = await async_playwright().start()
        self.browser = await self.config.launch()
        self.context = await self.config.create_context(self.browser)
        self.page = await self.context.new_page()

        await self.config.inject_bounding_box_helpers(self.page)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup: close context (finalizes video), then browser."""
        try:
            if self.page:
                # Clear boxes before closing
                await self.page.evaluate("window.clearAllBoxes()")
                await self.page.close()

            if self.context:
                await self.context.close()  # CRITICAL: Finalizes video!

            if self.browser:
                await self.browser.close()

            if self.playwright:
                await self.playwright.stop()

            self.logger.info("Browser session closed and cleaned up")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}", exc_info=True)

        return False  # Don't suppress exceptions
