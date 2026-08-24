import re
from dataclasses import dataclass
from urllib.parse import urlparse

from playwright.async_api import BrowserContext

BASE_URL = "https://www.amazon.com"
BESTSELLERS_URL = BASE_URL + "/Best-Sellers/zgbs/{category}/"
BESTSELLERS_ROOT_URL = BASE_URL + "/Best-Sellers/zgbs"
CARD_SELECTOR = "#gridItemRoot"
REVIEWS_SELECTOR = ".a-size-small"
LINK_SELECTOR = "a.a-link-normal"

NAV_TIMEOUT_MS = 60_000
SETTLE_MS = 4_000

ASIN_RE = re.compile(r"/dp/([A-Z0-9]{10})")
PRICE_RE = re.compile(r"\$([\d,]+\.?\d*)")
RATING_RE = re.compile(r"([\d.]+) out of 5")
RANK_RE = re.compile(r"^#(\d+)")
CATEGORY_PATH_RE = re.compile(r"/zgbs/([^/?#]+)")

CAPTCHA_MARKERS = (
    "Enter the characters you see below",
    "Sorry, we just need to make sure",
    "/errors/validateCaptcha",
)


class BlockedError(RuntimeError):
    """Amazon показал капчу вместо выдачи."""


@dataclass(frozen=True, slots=True)
class ScrapedProduct:
    asin: str
    title: str
    category: str
    price: float | None
    rating: float | None
    reviews_count: int | None
    url: str
    image_url: str
    bestseller_rank: int | None


@dataclass(frozen=True, slots=True)
class DiscoveredCategory:
    slug: str
    name: str


async def discover_categories(context: BrowserContext) -> list[DiscoveredCategory]:
    page = await context.new_page()
    try:
        await page.goto(
            BESTSELLERS_ROOT_URL,
            wait_until="domcontentloaded",
            timeout=NAV_TIMEOUT_MS,
        )
        await page.wait_for_timeout(SETTLE_MS)

        html = await page.content()
        if any(marker in html for marker in CAPTCHA_MARKERS):
            raise BlockedError("captcha on Best Sellers categories")

        discovered: dict[str, DiscoveredCategory] = {}
        anchors = page.locator("a[href*='/zgbs/']")
        for index in range(await anchors.count()):
            anchor = anchors.nth(index)
            href = await anchor.get_attribute("href")
            name = " ".join((await anchor.inner_text()).split())
            category = parse_category_link(href, name)
            if category is not None:
                discovered[category.slug] = category
        return sorted(discovered.values(), key=lambda item: item.name.casefold())
    finally:
        await page.close()


def parse_category_link(href: str | None, name: str) -> DiscoveredCategory | None:
    if not href or not name or name == "Best Sellers":
        return None
    match = CATEGORY_PATH_RE.search(urlparse(href).path)
    if match is None:
        return None
    return DiscoveredCategory(slug=match.group(1), name=name)


async def scrape_category(
    context: BrowserContext, category: str, limit: int, category_name: str | None = None
) -> list[ScrapedProduct]:
    page = await context.new_page()
    try:
        await page.goto(
            BESTSELLERS_URL.format(category=category),
            wait_until="domcontentloaded",
            timeout=NAV_TIMEOUT_MS,
        )
        await page.wait_for_timeout(SETTLE_MS)

        html = await page.content()
        if any(marker in html for marker in CAPTCHA_MARKERS):
            raise BlockedError(f"captcha on category {category}")

        cards = page.locator(CARD_SELECTOR)
        products = []
        for index in range(min(await cards.count(), limit)):
            product = await _parse_card(cards.nth(index), category_name or category)
            if product:
                products.append(product)
        return products
    finally:
        await page.close()


async def _parse_card(card, category: str) -> ScrapedProduct | None:
    text = await card.inner_text()
    link = card.locator(LINK_SELECTOR).first
    image = card.locator("img").first

    href = await link.get_attribute("href") if await link.count() else None
    asin_match = ASIN_RE.search(href or "")
    if not asin_match:
        return None

    title = await image.get_attribute("alt") if await image.count() else None
    if not title:
        return None

    return ScrapedProduct(
        asin=asin_match.group(1),
        title=title.strip(),
        category=category,
        price=_to_float(PRICE_RE.search(text)),
        rating=_to_float(RATING_RE.search(text)),
        reviews_count=await _reviews_count(card),
        url=f"{BASE_URL}/dp/{asin_match.group(1)}",
        image_url=await image.get_attribute("src") or "",
        bestseller_rank=_to_int(RANK_RE.search(text)),
    )


async def _reviews_count(card) -> int | None:
    node = card.locator(REVIEWS_SELECTOR).first
    if not await node.count():
        return None
    raw = (await node.inner_text()).strip().replace(",", "")
    return int(raw) if raw.isdigit() else None


def _to_float(match: re.Match | None) -> float | None:
    return float(match.group(1).replace(",", "")) if match else None


def _to_int(match: re.Match | None) -> int | None:
    return int(match.group(1)) if match else None
