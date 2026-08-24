from typing import Annotated

from fastapi import Depends

from app.core.deps import SessionDep
from app.scraping.category_service import AmazonCategoryService
from app.scraping.service import RunService


def get_run_service(session: SessionDep) -> RunService:
    return RunService(session)


RunServiceDep = Annotated[RunService, Depends(get_run_service)]


def get_amazon_category_service(session: SessionDep) -> AmazonCategoryService:
    return AmazonCategoryService(session)


AmazonCategoryServiceDep = Annotated[AmazonCategoryService, Depends(get_amazon_category_service)]
