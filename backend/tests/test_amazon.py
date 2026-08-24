from app.scraping.amazon import DiscoveredCategory, parse_category_link


def test_parse_category_link_extracts_amazon_slug() -> None:
    assert parse_category_link(
        "/Best-Sellers-Home-Kitchen/zgbs/home-garden/ref=zg_bs_nav_home-garden_0",
        "Home & Kitchen",
    ) == DiscoveredCategory(slug="home-garden", name="Home & Kitchen")


def test_parse_category_link_ignores_root_tab() -> None:
    assert parse_category_link("/Best-Sellers/zgbs/ref=zg_bs_tab_bs", "Best Sellers") is None
