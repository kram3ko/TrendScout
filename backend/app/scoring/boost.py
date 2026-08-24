from collections.abc import Iterable
from math import log

from app.products.keywords import tokenize
from app.salesboost.models import PastProduct
from app.scoring.schemas import BoostMatch

CATEGORY_MATCH_POINTS = 12.0
KEYWORD_MATCH_POINTS = 5.0
MAX_BOOST_POINTS = 20.0
# Rare and specific terms can carry a match; short generic words cannot do it alone.
MIN_SHARED_WEIGHT = 1.5
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
        document_count = len(self._entries)
        frequencies: dict[str, int] = {}
        for _, _, tokens in self._entries:
            for token in tokens:
                frequencies[token] = frequencies.get(token, 0) + 1
        self._weights = {
            token: (1.0 + log((document_count + 1) / (frequency + 1))) * _specificity(token)
            for token, frequency in frequencies.items()
        }

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
            shared_weight = sum(self._weights[token] for token in product_tokens & past_tokens)

            if same_category:
                points += CATEGORY_MATCH_POINTS
                category_hit = True
            elif shared_weight >= MIN_SHARED_WEIGHT:
                points += KEYWORD_MATCH_POINTS
            else:
                continue
            matched.append(past_title)

        return BoostMatch(
            points=min(points, MAX_BOOST_POINTS),
            matched_titles=tuple(matched[:MAX_REPORTED_MATCHES]),
            category_hit=category_hit,
        )


def _specificity(token: str) -> float:
    return 1.0 + min(max(len(token) - 5, 0), 4) * 0.25
