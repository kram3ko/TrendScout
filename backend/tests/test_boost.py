from app.salesboost.models import PastProduct
from app.scoring.boost import CATEGORY_MATCH_POINTS, KEYWORD_MATCH_POINTS, BoostCalculator


def past(title: str, category: str, keywords: str = "") -> PastProduct:
    return PastProduct(title=title, category=category, keywords=keywords)


def test_no_history_means_no_boost():
    match = BoostCalculator([]).evaluate("Garden Hose Reel", "lawn-garden")

    assert match.points == 0
    assert match.explanation == "no overlap with our past winners"


def test_same_category_scores_higher_than_keyword_overlap():
    calculator = BoostCalculator([past("Expandable Garden Hose", "lawn-garden")])

    same_category = calculator.evaluate("Garden Hose Reel", "lawn-garden")
    other_category = calculator.evaluate("Expandable Garden Hose Nozzle", "automotive")

    assert same_category.points == CATEGORY_MATCH_POINTS
    assert same_category.category_hit
    assert other_category.points == KEYWORD_MATCH_POINTS
    assert not other_category.category_hit


def test_single_shared_token_is_not_a_match():
    calculator = BoostCalculator([past("Expandable Garden Hose", "lawn-garden")])

    assert calculator.evaluate("Garden Gnome Statue", "home-garden").points == 0


def test_word_forms_match_without_rewarding_a_generic_token() -> None:
    calculator = BoostCalculator([past("Car Trunk Organizers", "automotive")])

    related = calculator.evaluate("Trunk Organizing System for SUV", "Home & Kitchen")
    generic = calculator.evaluate("Car Floor Mats", "Home & Kitchen")

    assert related.points == KEYWORD_MATCH_POINTS
    assert generic.points == 0


def test_boost_is_capped_and_reports_the_matched_titles():
    history = [past(f"Garden Hose {index}", "lawn-garden") for index in range(5)]

    match = BoostCalculator(history).evaluate("Garden Hose Reel", "lawn-garden")

    assert match.points == 20
    assert match.matched_titles == ("Garden Hose 0", "Garden Hose 1", "Garden Hose 2")
