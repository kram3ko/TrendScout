import asyncio
import json
from dataclasses import dataclass

from playwright.async_api import BrowserContext, Response

from app.products.enums import TrendDirection

WARMUP_URL = "https://trends.google.com/trends/?geo={geo}&hl=en-US"
EXPLORE_URL = "https://trends.google.com/trends/explore?q={keyword}&geo={geo}&hl=en-US"
WIDGET_DATA_PATH = "/trends/api/widgetdata/multiline"

# Google prefixes its widget payloads with )]}', + newline to break naive JSON eval.
XSSI_PREFIX_LENGTH = 5

NAV_TIMEOUT_MS = 45_000
WARMUP_SETTLE_MS = 3_000
WIDGET_TIMEOUT_S = 25.0
# Explore answers 429 when hit without the cookies the landing page hands out.
TOO_MANY_REQUESTS = 429

# A half-over-half move smaller than this is noise, not a trend.
FLAT_BAND_RATIO = 0.10


class TrendsUnavailableError(RuntimeError):
    """Google Trends refused the query — rate limit or an empty widget."""


class TrendsRateLimitedError(TrendsUnavailableError):
    """Google Trends temporarily rate-limited this server."""


@dataclass(frozen=True, slots=True)
class TrendResult:
    keyword: str
    direction: TrendDirection
    latest_value: int | None
    avg_first_half: float
    avg_second_half: float
    points_count: int


class TrendsScraper:
    """One warmed-up page reused for a batch of keywords: the warm-up is the expensive part."""

    def __init__(self, context: BrowserContext, geo: str) -> None:
        self._context = context
        self._geo = geo

    async def collect(self, keywords: list[str]) -> dict[str, TrendResult]:
        page = await self._context.new_page()
        try:
            await page.goto(
                WARMUP_URL.format(geo=self._geo),
                wait_until="domcontentloaded",
                timeout=NAV_TIMEOUT_MS,
            )
            await page.wait_for_timeout(WARMUP_SETTLE_MS)

            results: dict[str, TrendResult] = {}
            for keyword in keywords:
                try:
                    results[keyword] = await self._collect_one(page, keyword)
                except TrendsRateLimitedError:
                    raise
                except TrendsUnavailableError, TimeoutError:
                    continue
            return results
        finally:
            await page.close()

    async def _collect_one(self, page, keyword: str) -> TrendResult:
        payload: asyncio.Future[dict] = asyncio.get_running_loop().create_future()

        async def on_response(response: Response) -> None:
            if WIDGET_DATA_PATH not in response.url or payload.done():
                return
            body = await response.text()
            payload.set_result(json.loads(body[XSSI_PREFIX_LENGTH:]))

        page.on("response", on_response)
        try:
            navigation = await page.goto(
                EXPLORE_URL.format(keyword=keyword.replace(" ", "%20"), geo=self._geo),
                wait_until="domcontentloaded",
                timeout=NAV_TIMEOUT_MS,
            )
            if navigation is not None and navigation.status == TOO_MANY_REQUESTS:
                raise TrendsRateLimitedError("Google Trends rate limit; retry later")
            async with asyncio.timeout(WIDGET_TIMEOUT_S):
                widget = await payload
        finally:
            page.remove_listener("response", on_response)

        return _to_result(keyword, _timeline_values(widget))


def _timeline_values(widget: dict) -> list[int]:
    timeline = widget.get("default", {}).get("timelineData", [])
    return [point["value"][0] for point in timeline if point.get("value")]


def _to_result(keyword: str, values: list[int]) -> TrendResult:
    if not values:
        raise TrendsUnavailableError(f"empty timeline for '{keyword}'")

    midpoint = len(values) // 2 or 1
    first = sum(values[:midpoint]) / midpoint
    second = sum(values[midpoint:]) / max(len(values) - midpoint, 1)
    band = max(first, 1.0) * FLAT_BAND_RATIO

    if second - first > band:
        direction = TrendDirection.RISING
    elif first - second > band:
        direction = TrendDirection.FALLING
    else:
        direction = TrendDirection.FLAT

    return TrendResult(
        keyword=keyword,
        direction=direction,
        latest_value=values[-1],
        avg_first_half=round(first, 2),
        avg_second_half=round(second, 2),
        points_count=len(values),
    )
