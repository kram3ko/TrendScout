from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from playwright.async_api import BrowserContext, ViewportSize, async_playwright

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
VIEWPORT = ViewportSize(width=1440, height=900)
LAUNCH_ARGS = ["--no-sandbox", "--disable-blink-features=AutomationControlled"]


@asynccontextmanager
async def browser_context() -> AsyncIterator[BrowserContext]:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=LAUNCH_ARGS)
        context = await browser.new_context(
            user_agent=USER_AGENT,
            locale="en-US",
            timezone_id="America/New_York",
            viewport=VIEWPORT,
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        try:
            yield context
        finally:
            await context.close()
            await browser.close()
