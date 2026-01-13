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

    async def extract_iframe_tables(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract tables from iframes (where financial data is embedded).
        
        Returns list of tables found across all iframes.
        """
        all_iframe_tables = []
        
        # Find all iframes on the page
        iframes = page.frames
        print(f"  Found {len(iframes)} frames on page")
        
        for idx, frame in enumerate(iframes):
            try:
                # Skip the main frame
                if frame == page.main_frame:
                    continue
                
                frame_url = frame.url
                print(f"  Checking iframe {idx}: {frame_url[:60]}...")
                
                # Wait for iframe content to load
                await page.wait_for_timeout(1500)
                
                # Extract tables from this iframe using same logic
                iframe_tables = await frame.evaluate("""() => {
                    const results = [];
                    const tables = document.querySelectorAll('table');

                    for (const table of tables) {
                        // Title heuristic
                        let title = 'Iframe Table';
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
                            iframe_url: window.location.href,
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
                
                if iframe_tables and len(iframe_tables) > 0:
                    print(f"    ✅ Found {len(iframe_tables)} tables in iframe")
                    all_iframe_tables.extend(iframe_tables)
                else:
                    print(f"    No tables in this iframe")
                    
            except Exception as e:
                print(f"    ⚠️ Error extracting from iframe: {str(e)[:50]}")
                continue
        
        return all_iframe_tables

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
        Handles both main page tables and iframe tables.
        """
        colors = ['#3b82f6', '#8b5cf6', '#10b981', '#06b6d4', '#f59e0b', '#ef4444']
        
        if not tables_data:
            print("⚠️ No tables found to highlight")
            return
        
        print(f"✅ Highlighting {len(tables_data)} tables")
        
        # First, inject bounding box helpers into all frames
        await self._inject_helpers_to_all_frames(page)
        
        # Track which iframe we're currently looking at
        main_page_table_idx = 0
        current_iframe_idx = 0
        iframe_table_counts = {}  # Track table count per iframe
        
        for idx, table in enumerate(tables_data):
            color = colors[idx % len(colors)]
            table_title = table.get('title', 'Unnamed Table')[:30]
            iframe_url = table.get('iframe_url', None)
            
            # Wait for smooth scrolling
            await page.wait_for_timeout(300)
            
            if iframe_url:
                # This is an iframe table - find the iframe frame
                iframe_found = False
                for frame_idx, frame in enumerate(page.frames):
                    if frame == page.main_frame:
                        continue
                    
                    if frame.url == iframe_url or iframe_url in frame.url:
                        # Found the iframe - draw box inside it
                        try:
                            # Track which table in this iframe
                            if iframe_url not in iframe_table_counts:
                                iframe_table_counts[iframe_url] = 0
                            
                            table_idx_in_iframe = iframe_table_counts[iframe_url]
                            iframe_table_counts[iframe_url] += 1
                            
                            # Draw box in iframe
                            result = await frame.evaluate("""([tableIdx, color, title]) => {
                                const tables = document.querySelectorAll('table');
                                const tbl = tables[tableIdx];
                                
                                if (!tbl) {
                                    return {success: false, message: 'Table not found in iframe'};
                                }
                                
                                // Scroll table into view within iframe
                                tbl.scrollIntoView({behavior: 'smooth', block: 'center'});
                                
                                // Draw bounding box
                                if (window.drawBoundingBox) {
                                    window.drawBoundingBox(tbl, color, title, true);
                                    return {success: true, message: 'Box drawn in iframe'};
                                } else {
                                    return {success: false, message: 'drawBoundingBox not available in iframe'};
                                }
                            }""", [table_idx_in_iframe, color, table_title])
                            
                            print(f"  Table {idx + 1}: {table_title} (iframe) - {result.get('message', 'unknown')}")
                            iframe_found = True
                            
                            # Give time for box to be visible
                            await page.wait_for_timeout(800)
                            
                        except Exception as e:
                            print(f"  Table {idx + 1}: {table_title} (iframe) - Error: {str(e)[:50]}")
                        
                        break
                
                if not iframe_found:
                    print(f"  Table {idx + 1}: {table_title} (iframe) - Iframe not found")
            
            else:
                # This is a main page table
                try:
                    result = await page.evaluate("""([tableIdx, color, title]) => {
                        const tables = document.querySelectorAll('table');
                        const tbl = tables[tableIdx];
                        
                        if (!tbl) {
                            return {success: false, message: 'Table not found'};
                        }
                        
                        // Scroll into view
                        tbl.scrollIntoView({behavior: 'smooth', block: 'center'});
                        
                        // Draw bounding box
                        if (window.drawBoundingBox) {
                            window.drawBoundingBox(tbl, color, title, true);
                            return {success: true, message: 'Box drawn'};
                        } else {
                            return {success: false, message: 'drawBoundingBox not available'};
                        }
                    }""", [main_page_table_idx, color, table_title])
                    
                    print(f"  Table {idx + 1}: {table_title} (main) - {result.get('message', 'unknown')}")
                    main_page_table_idx += 1
                    
                    # Give time for box to be visible
                    await page.wait_for_timeout(800)
                    
                except Exception as e:
                    print(f"  Table {idx + 1}: {table_title} (main) - Error: {str(e)[:50]}")
        
        # Final pause to show all boxes
        print("  📹 Holding boxes for video capture...")
        await page.wait_for_timeout(2000)
    
    async def _inject_helpers_to_all_frames(self, page: Page):
        """Inject bounding box JavaScript helpers into all frames including iframes."""
        
        helper_script = """() => {
            if (window.scraperBoxes) return;  // Already injected
            
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
                    border: 4px solid ${color};
                    background: ${color}33;
                    box-shadow: 0 0 30px ${color}99;
                    pointer-events: none;
                    z-index: 999999;
                    transition: all 0.3s ease;
                `;

                if (label) {
                    const labelDiv = document.createElement('div');
                    labelDiv.textContent = label;
                    labelDiv.style.cssText = `
                        position: absolute;
                        top: -32px;
                        left: 0;
                        background: ${color};
                        color: white;
                        padding: 6px 12px;
                        border-radius: 4px;
                        font-size: 14px;
                        font-weight: bold;
                        white-space: nowrap;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.4);
                    `;
                    box.appendChild(labelDiv);
                }

                document.body.appendChild(box);

                if (persistent) {
                    window.scraperBoxes.push(box);
                }

                return box;
            };

            window.clearAllBoxes = function() {
                window.scraperBoxes.forEach(box => box.remove());
                window.scraperBoxes = [];
            };
        }"""
        
        # Inject into main page
        await page.evaluate(helper_script)
        
        # Inject into all iframes
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            try:
                await frame.evaluate(helper_script)
            except:
                pass  # Some iframes may block access

