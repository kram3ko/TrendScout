from typing import Annotated

from fastapi import APIRouter, Query

from app.auth.deps import CurrentUser
from app.products.deps import ProductServiceDep
from app.products.schemas import ProductPage, ProductQuery

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductPage)
async def list_products(
    user: CurrentUser, products: ProductServiceDep, query: Annotated[ProductQuery, Query()]
) -> ProductPage:
    return await products.list_page(query)


@router.get("/categories", response_model=list[str])
async def list_categories(user: CurrentUser, products: ProductServiceDep) -> list[str]:
    return await products.categories()
