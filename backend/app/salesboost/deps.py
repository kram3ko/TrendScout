from typing import Annotated

from fastapi import Depends

from app.core.deps import SessionDep
from app.salesboost.service import SalesBoostService


def get_sales_boost_service(session: SessionDep) -> SalesBoostService:
    return SalesBoostService(session)


SalesBoostServiceDep = Annotated[SalesBoostService, Depends(get_sales_boost_service)]
