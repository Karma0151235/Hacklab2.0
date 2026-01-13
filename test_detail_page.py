import asyncio
from playwright.async_api import async_playwright

async def test_detail_page():
    """Test to see what's actually on the detail page"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Go to a known detail page
        url = "https://www.bursamalaysia.com/market_information/announcements/company_announcement/announcement_details?ann_id=3625930"
        print(f"Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded")
        
        # Wait for manual CAPTCHA solving
        print("\n" + "="*70)
        print("👀 If you see Cloudflare, click it!")
        print("Waiting 10 seconds...")
        print("="*70 + "\n")
        await page.wait_for_timeout(10000)
        
        # Count tables
        table_count = await page.evaluate("() => document.querySelectorAll('table').length")
        print(f"\n✅ Found {table_count} tables on page")
        
        # Get all table text
        if table_count > 0:
            tables_info = await page.evaluate("""() => {
                const tables = document.querySelectorAll('table');
                const info = [];
                for (let i = 0; i < tables.length; i++) {
                    const table = tables[i];
                    const text = table.innerText.substring(0, 200);
                    info.push(`Table ${i + 1}: ${text}...`);
                }
                return info;
            }""")
            
            for table_info in tables_info:
                print(table_info)
        
        # Check for PDF links
        pdf_count = await page.evaluate("() => document.querySelectorAll('a[href*=\".pdf\"]').length")
        print(f"\n✅ Found {pdf_count} PDF links")
        
        # Get some text content
        page_text = await page.evaluate("() => document.body.innerText.substring(0, 500)")
        print(f"\n📄 Page text preview:\n{page_text}")
        
        # Save HTML for inspection
        html = await page.content()
        with open("d:/Hackathons/AmBank/HackLab2.0_Ambank/detail_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("\n✅ Saved HTML to detail_page.html")
        
        input("\nPress Enter to close...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_detail_page())
