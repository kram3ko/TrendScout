import pytest

from app.salesboost.csv_import import CsvFormatError, parse_past_products


def test_parses_rows_and_ignores_unknown_columns():
    raw = b"title,category,keywords,internal_id\nGarden Hose,lawn-garden,hose water,42\n"

    parsed, skipped = parse_past_products(raw)

    assert not skipped
    assert parsed[0].title == "Garden Hose"
    assert parsed[0].keywords == "hose water"


def test_one_bad_row_does_not_lose_the_rest_of_the_file():
    raw = b"title,category\n,lawn-garden\nGarden Hose,lawn-garden\n"

    parsed, skipped = parse_past_products(raw)

    assert len(parsed) == 1
    assert skipped[0].line == 2


def test_missing_required_column_is_rejected_up_front():
    with pytest.raises(CsvFormatError, match="category"):
        parse_past_products(b"title\nGarden Hose\n")


def test_bom_prefixed_export_is_accepted():
    parsed, _ = parse_past_products("﻿title,category\nGarden Hose,lawn-garden\n".encode())

    assert parsed[0].title == "Garden Hose"
