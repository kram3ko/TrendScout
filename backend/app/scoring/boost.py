from collections.abc import Iterable

from app.products.keywords import tokenize
from app.salesboost.models import PastProduct
from app.scoring.schemas import BoostMatch

CATEGORY_MATCH_POINTS = 12.0
KEYWORD_MATCH_POINTS = 5.0
MAX_BOOST_POINTS = 20.0
# Two shared meaningful tokens is the point where an overlap stops being coincidence.
MIN_SHARED_TOKENS = 2
MAX_REPORTED_MATCHES = 3

NO_BOOST = BoostMatch(points=0.0, matched_titles=(), category_hit=False)


class BoostCalculator:
    """Internal Sales Boost: rewards products that look like our past winners.

    Tokenized once per past product, then reused for the whole scraped batch —
    a run compares ~120 products against the full history on every pass.
    """

    def __init__(self, past_products: Iterable[PastProduct]) -> None:
        self._entries = [
            (past.title, past.category.strip().lower(), tokenize(f"{past.title} {past.keywords}"))
            for past in past_products
        ]

    def evaluate(self, title: str, category: str) -> BoostMatch:
        if not self._entries:
            return NO_BOOST

        product_tokens = tokenize(title)
        normalized_category = category.strip().lower()

        points = 0.0
        category_hit = False
        matched: list[str] = []
        for past_title, past_category, past_tokens in self._entries:
            same_category = normalized_category == past_category
            shared = len(product_tokens & past_tokens)

            if same_category:
                points += CATEGORY_MATCH_POINTS
                category_hit = True
            elif shared >= MIN_SHARED_TOKENS:
                points += KEYWORD_MATCH_POINTS
            else:
                continue
            matched.append(past_title)

        return BoostMatch(
            points=min(points, MAX_BOOST_POINTS),
            matched_titles=tuple(matched[:MAX_REPORTED_MATCHES]),
            category_hit=category_hit,
        )
