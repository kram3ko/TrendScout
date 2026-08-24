from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

TITLE_MAX_LENGTH = 512
CATEGORY_MAX_LENGTH = 128
KEYWORDS_MAX_LENGTH = 512
NOTE_MAX_LENGTH = 1024


class PastProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    category: str = Field(min_length=1, max_length=CATEGORY_MAX_LENGTH)
    keywords: str = Field(default="", max_length=KEYWORDS_MAX_LENGTH)
    note: str | None = Field(default=None, max_length=NOTE_MAX_LENGTH)


class PastProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    keywords: str
    note: str | None
    created_at: datetime


class CsvImportRow(BaseModel):
    """One rejected CSV line, reported back so the buyer can fix the file."""

    line: int
    error: str


class CsvImportReport(BaseModel):
    imported: int
    skipped: list[CsvImportRow]
