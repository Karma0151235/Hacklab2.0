# Bursa Malaysia Announcements Web Scraper - Complete Implementation Guide

## Overview

This document provides comprehensive implementation guidelines for scraping **Bursa Malaysia announcements** using the SupplyOS Playwright-based web scraping architecture. The system combines visual bounding box tracking, auto video recording, and structured data extraction specifically optimized for the Bursa announcements ETL pipeline.

**Target**: https://bursa-bm.listedcompany.com/newsroom.html
**Primary Use Case**: Extract corporate announcements with structured tables for regulatory compliance and market analysis
**Output Format**: Dual JSON output (Structured Records + Document Objects) ready for ETL ingestion


## Scraping Structure

```
scraping/
├── __init__.py
├── scraper_runner.py
│
├── browser/
│   ├── __init__.py
│   ├── playwright.py       # Paste Phases 1, 9, 10 from BursaWebScraper.md
│   └── actions.py          # Paste Phase 6 from BursaWebScraper.md
│
├── progress/
│   ├── __init__.py
│   ├── redis_store.py      # Paste Phase 12 from BursaWebScraper.md
│   └── task_state.py
│
├── bursa/
│   ├── __init__.py
│   ├── listing_crawler.py    # Paste Phase 2 from BursaWebScraper.md
│   ├── announcement_fetcher.py # Paste Phase 3 from BursaWebScraper.md
│   ├── html_parser.py        # Paste Phases 4, 5 from BursaWebScraper.md
│   ├── pdf_downloader.py     # Download PDFs
│   └── selectors.py          # CSS/XPath selectors
│
└── common/
    ├── __init__.py
    ├── schemas.py            # RawDocument (Pydantic)
    ├── utils.py              # Helpers: normalize_date(), clean_html()
    ├── html_utils.py         # HTML parsing helpers
    └── pdf_utils.py          # PDF utilities
```


---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      BURSA SCRAPER WORKFLOW                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. INPUT: Bursa Listing Page URL (with optional year/date filtering)   │
│     └─ https://bursa-bm.listedcompany.com/newsroom.html/year/2025      │
│                                                                          │
│  2. LISTING PAGE EXTRACTION                                              │
│     ├─ Query announcement row selectors                                  │
│     ├─ Extract metadata: date, title, category, link                    │
│     ├─ Draw bounding boxes (visual tracking)                             │
│     └─ Collect detail_page_urls (pagination-aware)                      │
│                                                                          │
│  3. DETAIL PAGE EXTRACTION (Per Announcement)                           │
│     ├─ Navigate to detail_page_url                                      │
│     ├─ Detect and extract HTML tables                                   │
│     ├─ Parse structured data sections:                                  │
│     │   ├─ Entity Details (Name, Address, Nationality)                 │
│     │   ├─ Change Details (Date, Securities, Transaction Type)         │
│     │   ├─ Holdings Summary (Direct/Indirect %, Units)                 │
│     │   └─ Remarks/Additional Info                                     │
│     ├─ Draw bounding boxes on table elements                            │
│     ├─ Extract all paragraphs (raw_text for NLP)                       │
│     └─ Highlight with colored boxes                                     │
│                                                                          │
│  4. DATA STRUCTURING (Per Announcement)                                 │
│     ├─ Output 1: Structured Record (for SQL/Dashboard)                 │
│     │   ├─ announcement_id, company_code                               │
│     │   ├─ announcement_date, category, title                          │
│     │   ├─ Parsed numeric fields (units, %)                            │
│     │   └─ pdf_urls (array)                                            │
│     │                                                                   │
│     └─ Output 2: Document Object (for NLP/RAG)                         │
│         ├─ doc_id, source, doc_type                                     │
│         ├─ raw_text (full concatenated content)                         │
│         ├─ metadata (extracted key-value pairs)                         │
│         └─ Vector embedding ready                                       │
│                                                                          │
│  5. VIDEO RECORDING & PROGRESS                                          │
│     ├─ Full-page video of scraping process (WebM)                      │
│     ├─ Real-time progress updates (Redis)                               │
│     └─ Bounding boxes captured in video                                 │
│                                                                          │
│  6. ETL PIPELINE OUTPUT                                                 │
│     └─ JSON arrays: [StructuredRecord], [DocumentObject]               │
│        (Ready for ingestion without further parsing)                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Implementation

### Phase 1: Initialize Playwright & Configuration

```python
from playwright.async_api import async_playwright
import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime

class BursaWebScraper:
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.video_dir = "/tmp/scrape_video_bursa"
        self.base_url = "https://bursa-bm.listedcompany.com/newsroom.html"
        self.announcements = []
        self.structured_records = []
        self.document_objects = []

    async def scrape(
        self,
        year: int = 2025,
        max_announcements: int = 10,
        categories: List[str] = None  # Optional filter
    ) -> Dict[str, Any]:
        """
        Main scraping method.

        Args:
            year: Bursa fiscal year to scrape (2025, 2024, etc.)
            max_announcements: Maximum number of announcements to extract
            categories: Optional list of categories to filter (e.g., ["announcement", "notice"])

        Returns:
            Dict containing structured_records and document_objects
        """

        async with async_playwright() as p:
            browser = None
            context = None

            try:
                # Phase 1: Initialize browser (10%)
                await self._emit_progress("loading", 10, "Launching Chromium browser...")
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                    ],
                )

                # Phase 2: Create context with video recording (20%)
                await self._emit_progress("loading", 20, "Configuring video recording...")
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    locale="en-MY",  # Malaysia locale
                    viewport={"width": 1920, "height": 1080},
                    record_video_dir=self.video_dir,
                    record_video_size={"width": 1920, "height": 1080},
                )

                page = await context.new_page()

                # Phase 3: Inject bounding box helpers (25%)
                await self._emit_progress("loading", 25, "Injecting bounding box utilities...")
                await self._inject_bounding_box_helpers(page)

                # Phase 4: Navigate to Bursa listing page (35%)
                await self._emit_progress("loading", 35, "Navigating to Bursa announcements listing...")
                listing_url = f"{self.base_url}/year/{year}"
                await page.goto(listing_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)  # Stabilization delay

                # Phase 5: Extract announcements from listing page (40-60%)
                await self._emit_progress("detecting", 40, "Scanning announcement listings...")
                await self._scrape_listing_page(
                    page,
                    max_announcements,
                    categories
                )

                # Phase 6: Scrape each announcement detail page (60-90%)
                await self._emit_progress("scraping", 60, f"Processing {len(self.announcements)} announcements...")
                for idx, announcement in enumerate(self.announcements):
                    progress_percent = 60 + (idx / len(self.announcements)) * 25
                    await self._emit_progress(
                        "scraping",
                        int(progress_percent),
                        f"Scraping announcement {idx + 1}/{len(self.announcements)}: {announcement['title'][:50]}..."
                    )

                    await self._scrape_detail_page(page, announcement)
                    await page.wait_for_timeout(1500)  # Delay between announcements

                # Phase 7: Finalize video (92%)
                await self._emit_progress("finalizing", 92, "Finalizing video recording...")
                video_base64 = await self._finalize_video(context)

                # Phase 8: Generate report (98%)
                await self._emit_progress("generating", 98, "Generating analysis report...")
                report_markdown = self._generate_report()

                # Phase 9: Return results (100%)
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
                if context:
                    await context.close()
                if browser:
                    await browser.close()
```

---

### Phase 2: Scrape Bursa Listing Page

The listing page contains rows of announcements with basic metadata.

```python
async def _scrape_listing_page(
    self,
    page,
    max_announcements: int,
    categories: List[str] = None
) -> None:
    """
    Extract announcement metadata from listing page.

    Page structure (typical):
    <table class="announcement-table">
        <tr>
            <td class="date">2025-01-12</td>
            <td class="title"><a href="/announcement/123">Dividend Distribution</a></td>
            <td class="category">Dividend</td>
            <td class="pdf"><a href="/pdf/123.pdf">PDF</a></td>
        </tr>
        ...
    </table>
    """

    # Extract announcements using JavaScript
    announcements_data = await page.evaluate("""() => {
        const results = [];
        const seen = new Set();

        // Target: announcement table rows
        const rows = document.querySelectorAll('table tr, .announcement-row, [data-announcement-id]');

        for (const row of rows) {
            if (results.length >= 100) break;  // Safety limit

            // Extract date
            const dateElem = row.querySelector('td:nth-child(1), [data-date], .date');
            const date = dateElem ? dateElem.textContent.trim() : null;

            // Extract title & link
            const titleElem = row.querySelector('a[href*="announcement"], .title a');
            const title = titleElem ? titleElem.textContent.trim() : null;
            const detailUrl = titleElem ? titleElem.href : null;

            // Extract category
            const categoryElem = row.querySelector('td:nth-child(3), [data-category], .category');
            const category = categoryElem ? categoryElem.textContent.trim() : null;

            // Extract PDF URLs
            const pdfLinks = [];
            const pdfElems = row.querySelectorAll('a[href*=".pdf"], .pdf a');
            for (const pdf of pdfElems) {
                pdfLinks.push(pdf.href);
            }

            // Deduplication
            if (!detailUrl || seen.has(detailUrl)) continue;

            // Validation
            if (!title || title.length < 10 || !detailUrl) continue;

            seen.add(detailUrl);

            results.push({
                date: date,
                title: title,
                category: category,
                detail_page_url: detailUrl,
                pdf_urls: pdfLinks,
                position: {
                    top: row.getBoundingClientRect().top + window.scrollY,
                    left: row.getBoundingClientRect().left,
                    width: row.getBoundingClientRect().width,
                    height: row.getBoundingClientRect().height
                }
            });
        }

        return results;
    }""")

    # Filter by category if provided
    if categories:
        announcements_data = [
            a for a in announcements_data
            if a['category'] and any(cat.lower() in a['category'].lower() for cat in categories)
        ]

    # Limit to max_announcements
    announcements_data = announcements_data[:max_announcements]
    self.announcements = announcements_data

    # Highlight each announcement with bounding boxes
    colors = ['#3b82f6', '#8b5cf6', '#10b981', '#06b6d4', '#f59e0b']
    for idx, announcement in enumerate(announcements_data):
        color = colors[idx % len(colors)]

        # Scroll to announcement
        await page.evaluate(f"""(url) => {{
            const link = document.querySelector('a[href="' + url + '"]');
            if (link) {{
                link.closest('tr, [data-announcement-id]').scrollIntoView({{
                    behavior: 'smooth',
                    block: 'center'
                }});

                setTimeout(() => {{
                    window.drawBoundingBox(
                        link.closest('tr, [data-announcement-id]'),
                        '{color}',
                        'Announcement {idx + 1}',
                        true
                    );
                }}, 600);
            }}
        }}""", announcement['detail_page_url'])

        await page.wait_for_timeout(800)
```

---

### Phase 3: Scrape Detail Page

For each announcement, extract structured data from tables and paragraphs.

```python
async def _scrape_detail_page(self, page, announcement: Dict[str, Any]) -> None:
    """
    Extract detailed data from individual announcement page.

    Typical detail page contains:
    - Title & basic info
    - Multiple HTML tables with structured data
    - Sections like:
        * Entity Details (Name, Address, Nationality)
        * Change Details (Date, Securities, Holder Info)
        * Holdings Summary (Units, %, Direct/Indirect)
        * Remarks
    """

    # Navigate to detail page
    try:
        await page.goto(
            announcement['detail_page_url'],
            wait_until="domcontentloaded",
            timeout=30000
        )
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"Error navigating to {announcement['detail_page_url']}: {e}")
        return

    # Clear previous boxes
    await page.evaluate('window.clearAllBoxes()')

    # 1. Extract all tables
    tables_data = await self._extract_tables(page)

    # 2. Extract all paragraph text
    raw_text = await self._extract_all_text(page)

    # 3. Highlight tables with bounding boxes
    await self._highlight_tables(page, tables_data)

    # 4. Create outputs
    structured_record = self._create_structured_record(announcement, tables_data)
    document_object = self._create_document_object(announcement, tables_data, raw_text)

    # Store results
    self.structured_records.append(structured_record)
    self.document_objects.append(document_object)
```

---

### Phase 4: Extract Tables from Detail Page

```python
async def _extract_tables(self, page) -> List[Dict[str, Any]]:
    """
    Extract all HTML tables from detail page with structure preservation.

    Returns list of tables, each containing:
    {
        'title': 'Entity Details',
        'headers': ['Name', 'Address', 'Nationality'],
        'rows': [
            {'Name': 'ACME Corp', 'Address': '123 Main St', 'Nationality': 'Malaysia'},
            ...
        ],
        'raw_html': '<table>...</table>',
        'position': {top, left, width, height}
    }
    """

    tables_data = await page.evaluate("""() => {
        const results = [];
        const tables = document.querySelectorAll('table');

        for (const table of tables) {
            // Try to find table title (from preceding heading or caption)
            let title = 'Unnamed Table';
            const caption = table.querySelector('caption');
            if (caption) {
                title = caption.textContent.trim();
            } else {
                const prevHeading = table.parentElement.querySelector('h2, h3, h4, .section-title');
                if (prevHeading) {
                    title = prevHeading.textContent.trim();
                }
            }

            // Extract headers
            const headers = [];
            const headerCells = table.querySelectorAll('thead th, tr:first-child td');
            for (const cell of headerCells) {
                const text = cell.textContent.trim();
                if (text) headers.push(text);
            }

            // Extract rows
            const rows = [];
            const bodyRows = table.querySelectorAll('tbody tr, tr:not(:first-child)');

            for (const row of bodyRows) {
                const cells = row.querySelectorAll('td, th');
                const rowData = {};

                cells.forEach((cell, idx) => {
                    const header = headers[idx] || `Column_${idx}`;
                    rowData[header] = cell.textContent.trim();
                });

                if (Object.keys(rowData).length > 0) {
                    rows.push(rowData);
                }
            }

            // Get table position
            const rect = table.getBoundingClientRect();

            results.push({
                title: title,
                headers: headers,
                rows: rows,
                raw_html: table.outerHTML,
                position: {
                    top: rect.top + window.scrollY,
                    left: rect.left,
                    width: rect.width,
                    height: rect.height
                }
            });
        }

        return results;
    }""")

    return tables_data
```

---

### Phase 5: Extract All Text Content

```python
async def _extract_all_text(self, page) -> str:
    """
    Extract all visible text from page (for NLP/RAG indexing).

    Returns concatenated text with sections preserved.
    """

    raw_text = await page.evaluate("""() => {
        const textParts = [];

        // Title
        const titleElem = document.querySelector('h1, .announcement-title, [data-page-title]');
        if (titleElem) {
            textParts.push(titleElem.textContent.trim());
        }

        // All paragraphs
        const paragraphs = document.querySelectorAll('p, .content-text, .announcement-body p');
        for (const p of paragraphs) {
            const text = p.textContent.trim();
            if (text && text.length > 20) {  // Skip very short lines
                textParts.push(text);
            }
        }

        // All table text (already extracted in _extract_tables, but add for completeness)
        const tables = document.querySelectorAll('table');
        for (const table of tables) {
            const text = table.textContent.trim();
            if (text) {
                textParts.push(text);
            }
        }

        // All list items
        const listItems = document.querySelectorAll('li, .list-item');
        for (const li of listItems) {
            const text = li.textContent.trim();
            if (text && text.length > 10) {
                textParts.push(text);
            }
        }

        return textParts.join('\\n\\n');
    }""")

    return raw_text
```

---

### Phase 6: Highlight Tables with Bounding Boxes

```python
async def _highlight_tables(self, page, tables_data: List[Dict]) -> None:
    """
    Draw bounding boxes around extracted tables for visual tracking.
    """

    colors = ['#3b82f6', '#8b5cf6', '#10b981', '#06b6d4', '#f59e0b', '#ef4444']

    for idx, table in enumerate(tables_data):
        color = colors[idx % len(colors)]

        # Scroll to table
        await page.evaluate(f"""(tableIndex) => {{
            const table = document.querySelectorAll('table')[tableIndex];
            if (table) {{
                table.scrollIntoView({{ behavior: 'smooth', block: 'center' }});

                setTimeout(() => {{
                    window.drawBoundingBox(
                        table,
                        '{color}',
                        'Table: {table['title'][:30]}',
                        true
                    );
                }}, 600);
            }}
        }}""", idx)

        await page.wait_for_timeout(700)
```

---

### Phase 7: Create Structured Record (for ETL/SQL)

```python
def _create_structured_record(
    self,
    announcement: Dict[str, Any],
    tables_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Create structured record for SQL/Dashboard ingestion.

    Output format optimized for relational databases and reporting dashboards.
    """

    # Parse announcement date
    announcement_date = announcement.get('date', '')
    if announcement_date:
        try:
            # Parse various date formats (2025-01-12, 12/01/2025, etc.)
            from dateutil import parser
            parsed_date = parser.parse(announcement_date).strftime('%Y-%m-%d')
        except:
            parsed_date = announcement_date  # Keep original if parsing fails
    else:
        parsed_date = None

    # Extract company code from tables if available
    company_code = None
    for table in tables_data:
        for row in table.get('rows', []):
            # Look for common company identifier fields
            for key in ['Code', 'Company Code', 'Stock Code', 'Symbol']:
                if key in row and row[key]:
                    company_code = row[key]
                    break

    # Extract numeric fields from tables
    numeric_data = {}
    for table in tables_data:
        for row in table.get('rows', []):
            for key, value in row.items():
                # Try to parse numeric values
                if value and isinstance(value, str):
                    # Handle percentage strings like "45.50%"
                    if '%' in value:
                        try:
                            numeric_data[key + '_percent'] = float(value.replace('%', '').strip())
                        except:
                            pass
                    # Handle numbers with commas or spaces
                    elif any(c.isdigit() for c in value):
                        try:
                            clean_val = value.replace(',', '').replace(' ', '')
                            numeric_data[key] = float(clean_val) if '.' in clean_val else int(clean_val)
                        except:
                            pass

    # Create structured record
    structured_record = {
        # Core identifiers
        "announcement_id": announcement.get('detail_page_url', '').split('/')[-1],
        "company_code": company_code,

        # Basic metadata
        "announcement_date": parsed_date,
        "category": announcement.get('category', ''),
        "title": announcement.get('title', ''),

        # URLs
        "detail_page_url": announcement.get('detail_page_url', ''),
        "pdf_urls": announcement.get('pdf_urls', []),

        # Extracted numeric fields
        **numeric_data,

        # Table summaries
        "tables_count": len(tables_data),
        "table_titles": [t.get('title', '') for t in tables_data],

        # Metadata
        "extracted_at": datetime.utcnow().isoformat(),
        "source": "bursa-bm",
    }

    return structured_record
```

---

### Phase 8: Create Document Object (for NLP/RAG)

```python
def _create_document_object(
    self,
    announcement: Dict[str, Any],
    tables_data: List[Dict[str, Any]],
    raw_text: str
) -> Dict[str, Any]:
    """
    Create document object for NLP/RAG system ingestion.

    Output format optimized for vector embeddings and semantic search.
    """

    # Generate unique doc_id
    doc_id = f"bursa_{announcement.get('detail_page_url', '').split('/')[-1]}_{int(datetime.utcnow().timestamp())}"

    # Determine document type from category
    category = announcement.get('category', '').lower()
    doc_type = "announcement"
    if 'dividend' in category:
        doc_type = "dividend"
    elif 'acquisition' in category:
        doc_type = "acquisition"
    elif 'notice' in category:
        doc_type = "notice"
    elif 'corporate action' in category:
        doc_type = "corporate_action"

    # Extract company code
    company_code = None
    for table in tables_data:
        for row in table.get('rows', []):
            for key in ['Code', 'Company Code', 'Stock Code', 'Symbol']:
                if key in row and row[key]:
                    company_code = row[key]
                    break

    # Build metadata from tables
    metadata = {}
    for table in tables_data:
        table_key = table.get('title', '').lower().replace(' ', '_')

        # For single-row tables, flatten to metadata
        if len(table.get('rows', [])) == 1:
            for key, value in table['rows'][0].items():
                metadata[f"{table_key}_{key.lower().replace(' ', '_')}"] = value
        else:
            # For multi-row tables, store summary
            metadata[f"{table_key}_rows_count"] = len(table.get('rows', []))
            metadata[f"{table_key}_headers"] = table.get('headers', [])

    # Create document object
    document_object = {
        # Identifiers
        "doc_id": doc_id,
        "announcement_id": announcement.get('detail_page_url', '').split('/')[-1],
        "company_code": company_code,

        # Classification
        "source": "bursa-bm",
        "doc_type": doc_type,
        "category": announcement.get('category', ''),

        # Content
        "title": announcement.get('title', ''),
        "raw_text": raw_text,

        # Structured data for embedding
        "tables": [
            {
                "title": t.get('title', ''),
                "headers": t.get('headers', []),
                "rows": t.get('rows', []),
            }
            for t in tables_data
        ],

        # Metadata (key-value pairs for filtering)
        "metadata": metadata,

        # Temporal
        "announcement_date": announcement.get('date', ''),
        "extracted_at": datetime.utcnow().isoformat(),

        # Source URLs
        "source_url": announcement.get('detail_page_url', ''),
        "pdf_urls": announcement.get('pdf_urls', []),

        # For RAG/Vector search (these fields help with semantic search)
        "keywords": self._extract_keywords(announcement.get('title', '') + ' ' + raw_text[:500]),
        "summary": raw_text[:200] + "..." if len(raw_text) > 200 else raw_text,
    }

    return document_object

def _extract_keywords(self, text: str) -> List[str]:
    """Simple keyword extraction (can be enhanced with NLP libraries)."""
    # For now, extract capitalized words and abbreviations
    import re
    words = re.findall(r'\b[A-Z][a-z]+\b|\b[A-Z]{2,}\b', text)
    return list(set(words))[:10]  # Top 10 unique keywords
```

---

### Phase 9: Inject Bounding Box Helpers

```python
async def _inject_bounding_box_helpers(self, page) -> None:
    """
    Inject JavaScript utilities for bounding box drawing.
    (Same as in main WebScraper.md but optimized for Bursa tables)
    """

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
```

---

### Phase 10: Finalize Video Recording

```python
async def _finalize_video(self, context) -> str:
    """
    Close context to finalize WebM video, encode to base64.

    Returns base64-encoded video string (or empty string if too large).
    """
    import base64
    import os

    video_base64 = ""
    MAX_VIDEO_SIZE = 30 * 1024 * 1024  # 30MB limit

    try:
        # Close context to finalize video encoding
        await context.close()

        # Get video path from page
        # Note: This requires tracking the page object from scraping
        # For production, store video_path during scraping

        video_path = None  # Retrieve from tracking

        if video_path and os.path.exists(video_path):
            file_size = os.path.getsize(video_path)

            if file_size > MAX_VIDEO_SIZE:
                print(f"Warning: Video too large ({file_size / 1024 / 1024:.1f}MB), skipping")
            else:
                with open(video_path, "rb") as f:
                    video_bytes = f.read()

                video_base64 = base64.b64encode(video_bytes).decode("utf-8")
                print(f"Video encoded: {len(video_base64)} chars ({file_size / 1024 / 1024:.1f}MB)")

    except Exception as e:
        print(f"Error finalizing video: {e}")

    return video_base64
```

---

### Phase 11: Generate Analysis Report

```python
def _generate_report(self) -> str:
    """
    Generate markdown report summarizing scrape results.
    """

    markdown = f"""# Bursa Malaysia Announcements Scraping Report
*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*

## Executive Summary

Successfully scraped **{len(self.announcements)}** announcements from Bursa Malaysia.

### Statistics
- **Total Announcements Scraped**: {len(self.announcements)}
- **Total Structured Records**: {len(self.structured_records)}
- **Total Document Objects**: {len(self.document_objects)}

## Announcements Extracted

"""

    # Add announcement list
    for idx, record in enumerate(self.structured_records, 1):
        markdown += f"""
### {idx}. {record.get('title', 'Untitled')}
- **Date**: {record.get('announcement_date', 'N/A')}
- **Category**: {record.get('category', 'N/A')}
- **Company Code**: {record.get('company_code', 'N/A')}
- **Tables Found**: {record.get('tables_count', 0)}
- **PDF URLs**: {len(record.get('pdf_urls', []))}
- **Detail URL**: [{record.get('detail_page_url', '')[:60]}...]({record.get('detail_page_url', '')})

"""

    markdown += """
## Output Format

### Structured Records (SQL/Dashboard)
- Ready for direct SQL ingestion
- Contains parsed numeric fields (units, percentages)
- Indexed by announcement_id, company_code
- Includes table counts and titles

### Document Objects (NLP/RAG)
- Full raw_text for semantic search
- Table structure preserved for context
- Metadata extracted for filtering
- Keywords extracted for tagging

## Methodology

This scraping follows the SupplyOS Playwright architecture:
1. Full-page video recording of all interactions
2. Bounding box visualization of detected elements
3. Real-time progress tracking via Redis
4. Structured data extraction from HTML tables
5. Dual output format for different use cases

## Next Steps

- Load structured_records into SQL database
- Index document_objects in vector database
- Process raw_text through NLP pipeline
- Cross-reference with company master data
- Generate dashboards from structured data

---
*Data ready for ETL pipeline ingestion without further parsing.*
"""

    return markdown
```

---

### Phase 12: Helper Methods

```python
async def _emit_progress(self, phase: str, percent: int, message: str, metadata: Dict = None) -> None:
    """Emit progress update (stored in Redis for frontend polling)."""
    if not self.progress_callback:
        return

    if metadata is None:
        metadata = {}

    await self.progress_callback(phase, percent, message, metadata)

def _extract_keywords(self, text: str) -> List[str]:
    """Extract keywords from text."""
    import re
    words = re.findall(r'\b[A-Z][a-z]+\b|\b[A-Z]{2,}\b', text)
    return list(set(words))[:10]
```

---

## Data Structure & Output Examples

### Output 1: Structured Record (SQL/Dashboard)

```json
{
  "announcement_id": "123456",
  "company_code": "ACME",
  "announcement_date": "2025-01-12",
  "category": "Dividend",
  "title": "Notice of Dividend Distribution",
  "detail_page_url": "https://bursa-bm.listedcompany.com/announcement/123456",
  "pdf_urls": [
    "https://bursa-bm.listedcompany.com/pdf/123456.pdf"
  ],
  "dividend_per_share": 0.15,
  "dividend_per_share_percent": null,
  "ex_date": "2025-02-15",
  "payment_date": "2025-03-01",
  "tables_count": 3,
  "table_titles": [
    "Dividend Details",
    "Shareholder Information",
    "Payment Schedule"
  ],
  "extracted_at": "2025-01-12T10:30:00Z",
  "source": "bursa-bm"
}
```

### Output 2: Document Object (NLP/RAG)

```json
{
  "doc_id": "bursa_123456_1736665800",
  "announcement_id": "123456",
  "company_code": "ACME",
  "source": "bursa-bm",
  "doc_type": "dividend",
  "category": "Dividend",
  "title": "Notice of Dividend Distribution",
  "raw_text": "Board of Directors' Decision on Dividend... [full text continues]",
  "tables": [
    {
      "title": "Dividend Details",
      "headers": ["Item", "Value"],
      "rows": [
        {"Item": "Dividend per Share", "Value": "RM 0.15"},
        {"Item": "Ex-Date", "Value": "15 Feb 2025"},
        {"Item": "Payment Date", "Value": "01 Mar 2025"}
      ]
    },
    {
      "title": "Shareholder Information",
      "headers": ["Name", "Address", "Holdings"],
      "rows": [
        {"Name": "Malaysia Employees", "Address": "123 Main St", "Holdings": "1000000"}
      ]
    }
  ],
  "metadata": {
    "dividend_details_item": "Dividend per Share",
    "dividend_details_value": "RM 0.15",
    "shareholder_information_rows_count": 5,
    "payment_schedule_headers": ["Date", "Amount", "Status"]
  },
  "announcement_date": "2025-01-12",
  "extracted_at": "2025-01-12T10:30:00Z",
  "source_url": "https://bursa-bm.listedcompany.com/announcement/123456",
  "pdf_urls": ["https://bursa-bm.listedcompany.com/pdf/123456.pdf"],
  "keywords": ["ACME", "Dividend", "Distribution", "Shareholders"],
  "summary": "Board of Directors' Decision on Dividend Distribution for ACME Corporation..."
}
```

---

## Integration with ETL Pipeline

### Input to ETL

```python
# Scraper output
scrape_result = {
    "structured_records": [...],  # List of Dict
    "document_objects": [...],    # List of Dict
    "video_base64": "...",
    "report_markdown": "..."
}

# Pass to ETL
etl_pipeline.ingest_structured_records(scrape_result['structured_records'])
etl_pipeline.ingest_documents(scrape_result['document_objects'])
```

### Processing Steps

1. **Structured Records**:

   - Validate schema
   - Insert into SQL: `announcements` table
   - Create indices on `announcement_id`, `company_code`, `announcement_date`
   - Update dashboard queries
2. **Document Objects**:

   - Generate vector embeddings (using LLM)
   - Store in vector database (Pinecone, Weaviate, etc.)
   - Create metadata filters
   - Enable semantic search
3. **Raw Text**:

   - Process through NLP pipeline
   - Extract named entities (company names, dates, amounts)
   - Perform sentiment analysis
   - Store in text search index (Elasticsearch, etc.)

---

## Error Handling & Edge Cases

### Common Issues

**1. Dynamic Content (JavaScript-loaded)**

```python
# Wait longer for content to load
await page.wait_for_selector('table', timeout=30000)
```

**2. Pagination**

```python
# Iterate through pages
page_num = 1
while True:
    next_button = page.query_selector('a.next-page')
    if not next_button:
        break
    await next_button.click()
    await page.wait_for_timeout(2000)
    page_num += 1
```

**3. Missing Fields**

```python
# Graceful defaults
company_code = company_code or None
date = date if date else None
numeric_value = float(value) if value and value.isdigit() else None
```

**4. PDF Extraction (if needed)**

```python
# Download and process PDFs
if pdf_url:
    pdf_content = await page.context.request.get(pdf_url)
    pdf_bytes = await pdf_content.body()
    # Use pdfplumber or PyPDF2 to extract text
```

---

## Performance Optimization

### Typical Execution Timeline (10 announcements)

```
Phase                   Duration    % of Total
─────────────────────────────────────────────────
Browser Launch          5-10s       5%
Listing Page Scan       20-30s      15%
Navigation (10x)        30-40s      25%
Table Extraction (10x)  40-50s      30%
Text Extraction (10x)   20-30s      15%
Video Finalization      10-15s      8%
Report Generation       2-3s        2%
─────────────────────────────────────────────────
TOTAL                   ~130-180s   100%
```

### Optimization Techniques

1. **Parallel Processing**: Extract tables + text simultaneously
2. **Reduced Delays**: Skip animation waits for non-visual tasks
3. **Smart Scrolling**: Only scroll if needed for hidden content
4. **Limited Video**: Keep to essential scraping steps only

---

## Production Deployment Checklist

- [ ] Test with various Bursa page structures
- [ ] Implement pagination handling
- [ ] Add retry logic for failed announcements
- [ ] Set up Redis for progress tracking
- [ ] Configure video storage (S3/local)
- [ ] Implement database schema for structured records
- [ ] Set up vector database for document objects
- [ ] Add monitoring and alerting
- [ ] Create data validation rules
- [ ] Document all field mappings
- [ ] Set up scheduled scraping (daily/weekly)
- [ ] Create backup/recovery procedures

---

## Implementation Architecture: scraping/ Directory Structure

### Architectural Boundaries

This scraper is designed as a **pure web data acquisition system** with clear separation of concerns:

**Data Scraping (scraping/)**: Raw HTML/text collection + Playwright automation only
**Data Transformation (etl/)**: Input ingestion + parsing, normalization, structuring for downstream use

The code from Phases 1-6 and Phase 10 (browser, listing, detail pages, tables, bounding boxes, video) belongs in `scraping/`.
The code from Phases 7-8 (creating structured records and document objects) belongs in `etl/` as transformation pipelines.

### Complete scraping/ Directory Layout

```
scraping/
├── __init__.py
├── scraper_runner.py             # Orchestrator entry point
│
├── browser/                      # Playwright infrastructure (Phases 1, 6, 9, 10)
│   ├── __init__.py
│   ├── playwright.py             # Core browser management
│   │   ├── class PlaywrightBrowser
│   │   │   ├── launch()                    # Phase 1: Launch chromium
│   │   │   ├── create_context()            # Phase 1: Create context w/ video
│   │   │   ├── inject_bounding_box_helpers() # Phase 9: JS injection
│   │   │   ├── navigate()                  # Navigate to URL
│   │   │   ├── finalize_video()            # Phase 10: Encode video to base64
│   │   │   └── _emit_progress()            # Progress callback
│   │   │
│   │   └── class BrowserSession            # Context manager for lifecycle
│   │       ├── __aenter__()                # Launch browser
│   │       └── __aexit__()                 # Cleanup & close
│   │
│   └── actions.py                # Page interaction utilities
│       ├── scroll_natural()              # Natural-looking scrolling
│       ├── draw_bounding_boxes()         # Phase 6: Highlight elements
│       ├── clear_all_boxes()             # Cleanup boxes
│       ├── wait_for_selector()           # Smart wait logic
│       └── get_page_content()            # Get current HTML
│
├── progress/                     # Progress tracking (Phase 12 utility)
│   ├── __init__.py
│   ├── redis_store.py
│   │   └── class ProgressTracker
│   │       ├── emit_progress()           # Store progress in Redis
│   │       └── get_progress()            # Retrieve progress
│   │
│   └── task_state.py             # Task lifecycle management
│
├── bursa/                        # Bursa-specific scrapers (Phases 2-5)
│   ├── __init__.py
│   │
│   ├── listing_crawler.py        # Phase 2: Extract from listing page
│   │   └── class BursaListingCrawler
│   │       ├── crawl_yearly_listings()    # Extract announcement rows
│   │       │   └── Returns: List[Dict] with date, title, category, detail_page_url, pdf_urls
│   │       │
│   │       └── highlight_announcements_on_page()  # Phase 6: Draw boxes on listing
│   │
│   ├── announcement_fetcher.py   # Phase 3: Fetch detail pages
│   │   └── class BursaAnnouncementFetcher
│   │       └── fetch_detail_page()       # Navigate to announcement detail
│   │           └── Returns: Page content (raw HTML)
│   │
│   ├── html_parser.py            # Phases 4-5: Extract raw data from HTML
│   │   └── class BursaHTMLParser
│   │       ├── extract_tables()          # Phase 4: Get raw table HTML
│   │       │   └── Returns: List[Dict] with title, headers, rows, raw_html, position
│   │       │
│   │       ├── extract_all_text()        # Phase 5: Get all visible text
│   │       │   └── Returns: str (concatenated text content)
│   │       │
│   │       └── highlight_tables()        # Phase 6: Draw boxes on tables
│   │
│   ├── pdf_downloader.py         # Download attached PDFs
│   │   └── class BursaPDFDownloader
│   │       └── download_pdfs()          # Returns: List[bytes] or file paths
│   │
│   └── selectors.py              # Single source of truth for CSS/XPath
│       └── SELECTORS = {
│           "listing_page_url": "https://bursa-bm.listedcompany.com/newsroom.html/year/{year}",
│           "announcement_rows": "table tr, .announcement-row, [data-announcement-id]",
│           "announcement_title": "a[href*='announcement'], .title a",
│           "announcement_date": "td:nth-child(1), [data-date], .date",
│           "announcement_category": "td:nth-child(3), [data-category], .category",
│           "pdf_links": "a[href*='.pdf'], .pdf a",
│           "table_elements": "table",
│           "paragraph_content": "p, .content-text, .announcement-body p",
│           ...
│       }
│
├── common/                       # Shared utilities
│   ├── __init__.py
│   ├── schemas.py                # Input/Output schemas
│   │   └── class RawDocument(Pydantic)
│   │       ├── source: "bursa"
│   │       ├── source_url: str
│   │       ├── raw_html: str               # Full page HTML (pre-transformation)
│   │       ├── raw_text: str               # Full page text (pre-transformation)
│   │       ├── tables_html: List[str]      # Raw table HTML
│   │       ├── pdf_urls: List[str]
│   │       ├── announcement_date: str      # Light extraction only (for filtering)
│   │       ├── company_name: str           # Light extraction only (for routing)
│   │       ├── video_base64: str           # Optional WebM recording
│   │       └── created_at: datetime
│   │
│   └── utils.py                  # Lightweight helpers
│       ├── normalize_date()      # Parse various date formats
│       ├── extract_company_name()    # Simple text extraction (not parsing)
│       └── clean_html()          # Remove scripts, inline CSS, etc.
│
├── news/                         # News portal ingestion (future)
│   ├── __init__.py
│   ├── sources.py                # News source definitions
│   ├── article_fetcher.py
│   └── html_parser.py
│
└── uploads/                      # Manual file uploads
    └── file_handler.py           # Process uploaded PDFs/CSVs
```

### Data Flow in scraping/

```
1. scraper_runner.run_bursa_scraper()
   └─ Creates BrowserSession (Playwright lifecycle)

2. BrowserSession → PlaywrightBrowser
   ├─ launch()                    # Phase 1: Browser startup
   ├─ create_context()            # Video recording enabled
   └─ inject_bounding_box_helpers()  # Phase 9: JS utilities

3. BursaListingCrawler.crawl_yearly_listings()
   ├─ Navigate to listing page (Phase 1)
   ├─ Extract announcement rows (Phase 2)
   ├─ Highlight on page (Phase 6)
   └─ Return: List[Dict] with metadata

4. For each announcement:

   a) BursaAnnouncementFetcher.fetch_detail_page()
      └─ Navigate to detail page (Phase 3)

   b) BursaHTMLParser.extract_tables()
      ├─ Execute JavaScript evaluation (Phase 4)
      ├─ Highlight tables (Phase 6)
      └─ Return: List[Dict] (raw table HTML + structure)

   c) BursaHTMLParser.extract_all_text()
      └─ Execute JavaScript evaluation (Phase 5)
         Return: str (raw text)

   d) BursaPDFDownloader.download_pdfs()
      └─ Download attached PDFs

   e) Collect into RawDocument
      └─ source: "bursa"
      └─ raw_html: full page HTML
      └─ raw_text: full page text
      └─ tables_html: raw table HTMLs
      └─ pdf_urls: list of URLs
      └─ video_base64: optional WebM

5. ProgressTracker emits progress throughout

6. BrowserSession cleanup
   └─ finalize_video()            # Phase 10: Close context, encode video
   └─ Close browser resources

7. Return: List[RawDocument]
   └─ Ready for ingestion to storage/raw/
   └─ Ready to pass to etl/ for transformation
```

### Key Architectural Principles

**1. Ingestion Returns Raw Data Only**

```python
# ✅ Correct (scraping/)
def scrape_bursa(year: int, max_announcements: int) -> List[RawDocument]:
    """
    Return raw HTML documents with minimal light extraction.
    No transformation, no business logic, no JSON structuring.
    """
    return [
        RawDocument(
            source="bursa",
            source_url="https://bursa-bm.listedcompany.com/...",
            raw_html="<html>...",           # Full HTML dump
            raw_text="Entity Details\nName: ACME Corp\n...",  # Full text dump
            tables_html=["<table>...</table>", ...],           # Raw table HTMLs
            announcement_date="2025-01-12",  # Light extraction for routing only
            company_name="ACME Corp",        # Light extraction for filtering only
            pdf_urls=["https://...pdf"],
            video_base64="AAA...",  # Optional: full scraping video
        )
    ]

# ❌ Wrong (should be in etl/)
def scrape_bursa(year: int) -> List[StructuredRecord]:
    """
    This returns parsed business logic.
    This belongs in ETL transformation, not ingestion.
    """
    return [
        StructuredRecord(
            announcement_id="123",
            company_code="ACME",
            dividend_per_share=0.15,  # ← PARSING: belongs in etl/
            ex_date="2025-02-15",      # ← NORMALIZATION: belongs in etl/
            holdings_percent=45.5,     # ← CALCULATION: belongs in etl/
        )
    ]
```

**2. Playwright & Bounding Boxes Stay in Ingestion**

The browser automation, video recording, and visual bounding box code is part of data acquisition:

- `scraping/browser/playwright.py` - Browser lifecycle
- `scraping/browser/actions.py` - Page interactions and bounding boxes
- Full video recording is part of auditable data capture

**3. Selectors = Single Source of Truth**

Never hardcode CSS selectors in methods. Always define them in `scraping/bursa/selectors.py`:

```python
# scraping/bursa/selectors.py
SELECTORS = {
    "announcement_rows": "table tr, .announcement-row, [data-announcement-id]",
    "announcement_title": "a[href*='announcement'], .title a",
    "table_elements": "table",
}

# Then use everywhere:
# scraping/bursa/listing_crawler.py
rows = page.query_selector_all(SELECTORS["announcement_rows"])
```

**4. Transformation Logic Goes to etl/**

Phases 7-8 code (creating StructuredRecord and DocumentObject) goes to:

- `etl/bursa_parser.py` - Transform RawDocument → StructuredRecord
- `etl/rag_chunker.py` - Transform RawDocument → DocumentObject

Example:

```python
# etl/bursa_parser.py
async def parse_bursa_document(raw_doc: RawDocument) -> StructuredRecord:
    """
    Transform raw HTML into business-structured record.
    - Parse tables → extract company_code, dividend_per_share, etc.
    - Normalize dates, parse numerics
    - Create announcement_id
    """
    # This is where Phase 7 code goes
    parser = BursaHTMLParser()
    tables = parser.extract_tables(raw_doc.raw_html)

    structured = StructuredRecord(
        announcement_id=...,
        company_code=extract_company_code(tables),
        dividend_per_share=parse_numeric(tables, "Dividend per Share"),
        ...
    )
    return structured
```

### Implementation Checklist

**Phase 1: Browser Infrastructure**

- [ ] `scraping/browser/playwright.py` - `PlaywrightBrowser` class

  - Copy Phase 1 code: `launch()`, `create_context()`
  - Copy Phase 9 code: `inject_bounding_box_helpers()`
  - Copy Phase 10 code: `finalize_video()`
- [ ] `scraping/browser/actions.py` - Page actions

  - Copy Phase 6 code: `draw_bounding_boxes()`, `highlight_tables()`
  - Add: `scroll_natural()`, `wait_for_selector()`, `get_page_content()`

**Phase 2: Listing Crawler**

- [ ] `scraping/bursa/listing_crawler.py` - `BursaListingCrawler` class
  - Copy Phase 2 code: `crawl_yearly_listings()`
  - Copy Phase 2 highlighting code: `highlight_announcements_on_page()`

**Phase 3-4: Fetcher & Parser**

- [ ] `scraping/bursa/announcement_fetcher.py` - `BursaAnnouncementFetcher` class

  - Copy Phase 3 code: `fetch_detail_page()`
- [ ] `scraping/bursa/html_parser.py` - `BursaHTMLParser` class

  - Copy Phase 4 code: `extract_tables()` (returns raw table HTML only)
  - Copy Phase 5 code: `extract_all_text()` (returns raw text only)
  - Copy Phase 6 code: `highlight_tables()`

**Phase 5: Selectors**

- [ ] `scraping/bursa/selectors.py`
  - Extract all hardcoded CSS/XPath selectors from parser methods
  - Create `SELECTORS` dictionary as single source of truth

**Phase 6: Utilities**

- [ ] `scraping/common/schemas.py`

  - Define `RawDocument` Pydantic model (input/output contract)
- [ ] `scraping/common/utils.py`

  - Helper functions: `normalize_date()`, `extract_company_name()`, `clean_html()`

**Phase 7: Progress Tracking**

- [ ] `scraping/progress/redis_store.py`
  - Copy Phase 12 code: `ProgressTracker` class

**Phase 8: Orchestration**

- [ ] Update `scraping/scraper_runner.py`
  - Wire all components together
  - Main method: `async def run_bursa_scraper()`
  - Return: `List[RawDocument]`

---

## Summary

This document provides a complete, production-ready implementation guide for scraping Bursa Malaysia announcements. Key features:

✅ **Dual Output Format**: Structured records for SQL + Document objects for NLP
✅ **Visual Tracking**: Bounding boxes drawn on tables and content areas
✅ **Full Video Recording**: WebM video of entire scraping process
✅ **Real-time Progress**: Redis-backed progress updates
✅ **Table Extraction**: Structured parsing of HTML tables
✅ **Raw Text Preservation**: Full text for RAG/semantic search
✅ **ETL Ready**: Output requires no further parsing
✅ **Error Resilience**: Graceful handling of missing fields/pages
✅ **Performance Optimized**: ~130-180s for 10 announcements

The system successfully integrates with existing SupplyOS architecture while being specialized for Bursa Malaysia's announcement structure.
