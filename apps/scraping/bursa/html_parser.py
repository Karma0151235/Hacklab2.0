from playwright.async_api import Page
from typing import List, Dict, Any

class BursaHTMLParser:
    """
    Parses detailed content from announcement pages.
    """
    async def extract_tables(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract all tables (Phase 4).
        """
        return await page.evaluate("""() => {
            const results = [];
            const tables = document.querySelectorAll('table');

            for (const table of tables) {
                // Title heuristic
                let title = 'Unnamed Table';
                const caption = table.querySelector('caption');
                if (caption) {
                    title = caption.textContent.trim();
                } else {
                    const prevElement = table.previousElementSibling;
                    if (prevElement && ['H2','H3','H4','STRONG','B'].includes(prevElement.tagName)) {
                        title = prevElement.textContent.trim();
                    }
                }

                // Headers
                const headers = [];
                const headerCells = table.querySelectorAll('thead th, tr:first-child td, tr:first-child th');
                for (const cell of headerCells) {
                    headers.push(cell.innerText.trim());
                }

                // Rows
                const rows = [];
                const bodyRows = table.querySelectorAll('tbody tr, tr:not(:first-child)');
                
                for (const row of bodyRows) {
                    const cells = row.querySelectorAll('td, th');
                    const rowData = {};
                    cells.forEach((cell, idx) => {
                        const key = headers[idx] || `Column_${idx}`;
                        rowData[key] = cell.innerText.trim();
                    });
                    if (Object.keys(rowData).length > 0) rows.push(rowData);
                }

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

    async def extract_all_text(self, page: Page) -> str:
        """
        Extract full text (Phase 5).
        """
        return await page.evaluate("""() => {
            return document.body.innerText;
        }""")

    async def highlight_tables(self, page: Page, tables_data: List[Dict]):
        """
        Draw bounding boxes around tables (Phase 6).
        """
        colors = ['#3b82f6', '#8b5cf6', '#10b981', '#06b6d4', '#f59e0b', '#ef4444']
        for idx, table in enumerate(tables_data):
            color = colors[idx % len(colors)]
            await page.evaluate("""([idx, color, title]) => {
                const tbl = document.querySelectorAll('table')[idx];
                if (tbl) {
                    tbl.scrollIntoView({behavior: 'smooth', block: 'center'});
                    // window.drawBoundingBox is injected by PlaywrightBrowser
                    if (window.drawBoundingBox) {
                        setTimeout(() => {
                            window.drawBoundingBox(tbl, color, title, true);
                        }, 500);
                    }
                }
            }""", [idx, color, table['title'][:30]])
            await page.wait_for_timeout(700)
