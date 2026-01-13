from playwright.async_api import Page
import asyncio

async def scroll_natural(page: Page, speed: int = 100):
    """
    Scrolls the page naturally to trigger lazy loading.
    """
    # Simple scroll for now
    await page.evaluate("""async (speed) => {
        const height = document.body.scrollHeight;
        for (let i = 0; i < height; i += speed) {
            window.scrollTo(0, i);
            await new Promise(resolve => setTimeout(resolve, 50));
        }
    }""", speed)

async def wait_for_selector(page: Page, selector: str, timeout: int = 30000):
    """
    Wrapper for wait_for_selector with better logging.
    """
    try:
        await page.wait_for_selector(selector, timeout=timeout)
    except Exception as e:
        print(f"Wait failed for selector: {selector}")
        raise e

async def draw_bounding_boxes(page: Page, selector: str, color: str = '#3b82f6', label: str = ''):
    """
    Draw boxes around elements matching selector.
    """
    await page.evaluate(f"""() => {{
        const elements = document.querySelectorAll('{selector}');
        elements.forEach((el, idx) => {{
            window.drawBoundingBox(el, '{color}', '{label} ' + (idx + 1), true);
        }});
    }}""")

async def clear_all_boxes(page: Page):
    """
    Clear all bounding boxes.
    """
    await page.evaluate("window.clearAllBoxes()")
