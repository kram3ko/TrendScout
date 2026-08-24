from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.auth.deps import CurrentUser
from app.salesboost.csv_import import CsvFormatError, parse_past_products
from app.salesboost.deps import SalesBoostServiceDep
from app.salesboost.schemas import CsvImportReport, PastProductCreate, PastProductRead
from app.tasks.jobs import score_products

# A history file is a few hundred rows; anything larger is a mistaken upload.
MAX_CSV_BYTES = 2 * 1024 * 1024

router = APIRouter(prefix="/past-products", tags=["sales-boost"])


@router.get("", response_model=list[PastProductRead])
async def list_past_products(
    user: CurrentUser, sales_boost: SalesBoostServiceDep
) -> list[PastProductRead]:
    products = await sales_boost.list_all()
    return [PastProductRead.model_validate(product) for product in products]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PastProductRead)
async def add_past_product(
    payload: PastProductCreate, user: CurrentUser, sales_boost: SalesBoostServiceDep
) -> PastProductRead:
    created = await sales_boost.add(payload)
    await score_products.kiq(rescore_all=True)
    return PastProductRead.model_validate(created)


@router.post("/import", response_model=CsvImportReport)
async def import_past_products(
    user: CurrentUser, sales_boost: SalesBoostServiceDep, file: Annotated[UploadFile, File()]
) -> CsvImportReport:
    raw = await file.read(MAX_CSV_BYTES + 1)
    if len(raw) > MAX_CSV_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="CSV file is too large"
        )

    try:
        parsed, skipped = parse_past_products(raw)
    except CsvFormatError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error

    imported = await sales_boost.add_many(parsed)
    if imported:
        await score_products.kiq(rescore_all=True)
    return CsvImportReport(imported=imported, skipped=skipped)


@router.delete("/{past_product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_past_product(
    past_product_id: int, user: CurrentUser, sales_boost: SalesBoostServiceDep
) -> None:
    if not await sales_boost.delete(past_product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Past product not found")
    await score_products.kiq(rescore_all=True)
