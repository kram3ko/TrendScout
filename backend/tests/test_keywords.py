from app.products.keywords import tokenize, trends_keyword


def test_tokenize_drops_marketing_filler():
    assert tokenize("Premium Heavy Duty Garden Hose 50 ft") == {"garden", "hose"}


def test_tokenize_ignores_short_tokens():
    assert "ft" not in tokenize("Garden Hose 50 ft")


def test_trends_keyword_keeps_first_meaningful_tokens():
    title = "Professional Stainless Steel Kitchen Knife Set with Wooden Block"
    assert trends_keyword(title) == "stainless steel kitchen"


def test_trends_keyword_falls_back_to_title_when_all_tokens_filtered():
    assert trends_keyword("Set of 5") == "Set of 5"
