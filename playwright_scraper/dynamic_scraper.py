from __future__ import annotations

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from config.settings import get_settings


async def fetch_dynamic_html(url: str) -> str:
    settings = get_settings()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(locale="en-IN")
            await page.goto(url, wait_until="domcontentloaded", timeout=settings.playwright_timeout_ms)
            try:
                await page.wait_for_selector("#productTitle", timeout=settings.playwright_timeout_ms)
            except PlaywrightTimeoutError:
                pass  # return whatever rendered; the parser decides what is usable
            return await page.content()
        finally:
            await browser.close()
