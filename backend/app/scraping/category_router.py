from fastapi import APIRouter, HTTPException, status

from app.auth.deps import CurrentUser
from app.scraping.category_service import UnknownCategoryError
from app.scraping.deps import AmazonCategoryServiceDep
from app.scraping.schemas import AmazonCategoryRead, AmazonCategorySelection

router = APIRouter(prefix="/amazon-categories", tags=["amazon categories"])


@router.get("", response_model=list[AmazonCategoryRead])
async def list_amazon_categories(
    user: CurrentUser, categories: AmazonCategoryServiceDep
) -> list[AmazonCategoryRead]:
    return [
        AmazonCategoryRead.model_validate(category)
        for category in await categories.list_available()
    ]


@router.put("", response_model=list[AmazonCategoryRead])
async def select_amazon_categories(
    payload: AmazonCategorySelection,
    user: CurrentUser,
    categories: AmazonCategoryServiceDep,
) -> list[AmazonCategoryRead]:
    try:
        selected = await categories.set_enabled(payload.slugs)
    except UnknownCategoryError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unknown Amazon categories: {error}",
        ) from error
    return [AmazonCategoryRead.model_validate(category) for category in selected]
