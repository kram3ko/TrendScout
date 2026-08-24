from typing import Annotated

from fastapi import Depends

from app.core.deps import SessionDep
from app.products.service import ProductService


def get_product_service(session: SessionDep) -> ProductService:
    return ProductService(session)


ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
