"""
Ingestion Layer Entrypoint

Orchestrates data acquisition from multiple sources:
- Bursa Malaysia announcements
- News portals

No reasoning or transformation here - purely data capture.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger


class IngestionRunner:
    """Orchestrates ingestion jobs across all sources."""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.logger = logger

    async def run_bursa_ingestion(
        self,
        year: int = 2025,
        max_announcements: int = 10,
        categories: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Run Bursa Malaysia announcement ingestion.

        Args:
            year: Fiscal year to scrape
            max_announcements: Maximum announcements to fetch
            categories: Optional category filter

        Returns:
            Ingestion result with status and metadata
        """
        try:
            self.logger.info(f"Starting Bursa ingestion: year={year}, max={max_announcements}")

            # TODO: Import and call bursa.listing_crawler
            # raw_documents = await listing_crawler.crawl_yearly_listings(year)

            return {
                "status": "pending_implementation",
                "source": "bursa",
                "timestamp": datetime.utcnow().isoformat(),
                "documents_count": 0,
            }

        except Exception as e:
            self.logger.error(f"Bursa ingestion failed: {e}", exc_info=True)
            raise

    async def run_news_ingestion(
        self,
        sources: Optional[list] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Run news portal ingestion.

        Args:
            sources: List of news sources (e.g., ["the_edge", "nst", "star"])
            limit: Maximum articles per source

        Returns:
            Ingestion result
        """
        try:
            self.logger.info(f"Starting news ingestion: sources={sources}, limit={limit}")

            # TODO: Import and call news scrapers

            return {
                "status": "pending_implementation",
                "source": "news",
                "timestamp": datetime.utcnow().isoformat(),
                "documents_count": 0,
            }

        except Exception as e:
            self.logger.error(f"News ingestion failed: {e}", exc_info=True)
            raise

    async def run_upload_ingestion(self, file_path: str) -> Dict[str, Any]:
        """
        Process manually uploaded files (PDFs, CSVs).

        Args:
            file_path: Path to uploaded file

        Returns:
            Ingestion result
        """
        try:
            self.logger.info(f"Processing upload: {file_path}")

            # TODO: Import and call uploads.file_handler

            return {
                "status": "pending_implementation",
                "source": "upload",
                "file_path": file_path,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Upload processing failed: {e}", exc_info=True)
            raise


async def main():
    """Development/testing entrypoint."""
    runner = IngestionRunner()

    # Example: Run Bursa ingestion
    result = await runner.run_bursa_ingestion(year=2025, max_announcements=5)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
