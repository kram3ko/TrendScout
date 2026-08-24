import re

TOKEN_RE = re.compile(r"[a-z0-9]+")
MIN_TOKEN_LENGTH = 3
TRENDS_KEYWORD_TOKENS = 3

# Marketing filler that carries no signal: it neither identifies a product on
# Google Trends nor distinguishes one past winner from another.
STOPWORDS = frozenset(
    {
        "for",
        "with",
        "and",
        "the",
        "pack",
        "set",
        "new",
        "pcs",
        "pieces",
        "inch",
        "size",
        "large",
        "small",
        "black",
        "white",
        "blue",
        "red",
        "green",
        "premium",
        "professional",
        "heavy",
        "duty",
        "high",
        "quality",
        "best",
        "upgraded",
        "portable",
        "adjustable",
        "universal",
        "multi",
        "pro",
        "plus",
        "max",
        "mini",
        "count",
        "piece",
        "included",
        "free",
        "kit",
        "compatible",
        "replacement",
    }
)


def tokenize(text: str) -> set[str]:
    """Meaningful lowercase tokens of a product title — the unit of keyword matching."""
    return {
        _canonicalize(token)
        for token in TOKEN_RE.findall(text.lower())
        if len(token) >= MIN_TOKEN_LENGTH and token not in STOPWORDS
    }


def _canonicalize(token: str) -> str:
    if token.endswith("ies") and len(token) > 4:
        token = f"{token[:-3]}y"
    elif token.endswith(("ches", "shes", "xes", "zes")):
        token = token[:-2]
    elif token.endswith("s") and not token.endswith("ss") and len(token) > 4:
        token = token[:-1]

    for suffix in ("ing", "ers", "er", "ed"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            stem = token[: -len(suffix)]
            return stem[:-1] if len(stem) > 1 and stem[-1] == stem[-2] else stem
    return token


def trends_keyword(title: str) -> str:
    """Short query for Google Trends: a long title returns no data at all."""
    seen: list[str] = []
    for token in TOKEN_RE.findall(title.lower()):
        if len(token) < MIN_TOKEN_LENGTH or token in STOPWORDS or token in seen:
            continue
        seen.append(token)
        if len(seen) == TRENDS_KEYWORD_TOKENS:
            break
    return " ".join(seen) or title[:64].strip()
