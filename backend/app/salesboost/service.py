from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.salesboost.models import PastProduct
from app.salesboost.schemas import PastProductCreate


class SalesBoostService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[PastProduct]:
        statement = select(PastProduct).order_by(PastProduct.created_at.desc())
        return list(await self._session.scalars(statement))

    async def add(self, payload: PastProductCreate) -> PastProduct:
        past_product = PastProduct(**payload.model_dump())
        self._session.add(past_product)
        await self._session.commit()
        await self._session.refresh(past_product)
        return past_product

    async def add_many(self, payloads: Sequence[PastProductCreate]) -> int:
        if not payloads:
            return 0
        self._session.add_all([PastProduct(**payload.model_dump()) for payload in payloads])
        await self._session.commit()
        return len(payloads)

    async def delete(self, past_product_id: int) -> bool:
        past_product = await self._session.get(PastProduct, past_product_id)
        if past_product is None:
            return False
        await self._session.delete(past_product)
        await self._session.commit()
        return True
