import csv
import io

from pydantic import ValidationError

from app.salesboost.schemas import CsvImportRow, PastProductCreate

REQUIRED_COLUMNS = frozenset({"title", "category"})
OPTIONAL_COLUMNS = frozenset({"keywords", "note"})
# DictReader yields the first data row as line 2 of the file.
FIRST_DATA_LINE = 2


class CsvFormatError(ValueError):
    """The uploaded file is not the expected Sales Boost export."""


def parse_past_products(raw: bytes) -> tuple[list[PastProductCreate], list[CsvImportRow]]:
    """Parses leniently per row: one bad line must not cost the buyer the whole upload."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise CsvFormatError("File must be UTF-8 encoded") from error

    reader = csv.DictReader(io.StringIO(text))
    columns = {name.strip().lower() for name in reader.fieldnames or []}
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise CsvFormatError(f"Missing required column(s): {', '.join(sorted(missing))}")

    parsed: list[PastProductCreate] = []
    skipped: list[CsvImportRow] = []
    for offset, row in enumerate(reader, start=FIRST_DATA_LINE):
        normalized = {
            key.strip().lower(): (value or "").strip()
            for key, value in row.items()
            if key is not None and key.strip().lower() in REQUIRED_COLUMNS | OPTIONAL_COLUMNS
        }
        try:
            parsed.append(PastProductCreate.model_validate(normalized))
        except ValidationError as error:
            first = error.errors()[0]
            skipped.append(CsvImportRow(line=offset, error=f"{first['loc'][0]}: {first['msg']}"))
    return parsed, skipped
