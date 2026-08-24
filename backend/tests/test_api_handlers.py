from datetime import UTC, datetime
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, Response, UploadFile

from app.auth.deps import get_current_user
from app.auth.models import User
from app.auth.router import login, logout, me
from app.auth.schemas import LoginRequest
from app.core.security import issue_token
from app.products.router import list_categories, list_products
from app.products.schemas import ProductPage, ProductQuery
from app.salesboost import router as salesboost_router
from app.salesboost.router import (
    add_past_product,
    delete_past_product,
    import_past_products,
    list_past_products,
)
from app.salesboost.schemas import PastProductCreate
from app.scraping import category_router
from app.scraping import router as runs_router
from app.scraping.category_service import UnknownCategoryError
from app.scraping.enums import RunKind, RunStatus
from app.scraping.schemas import AmazonCategorySelection

NOW = datetime.now(UTC)
USER = User(id=1, username="admin", password_hash="hash")


def past_product(product_id: int = 1):
    return SimpleNamespace(
        id=product_id,
        title="Garden Hose",
        category="Garden",
        keywords="hose,garden",
        note=None,
        created_at=NOW,
    )


async def test_login_sets_cookie_and_resets_limiter() -> None:
    response = Response()
    auth = SimpleNamespace(authenticate=AsyncMock(return_value=USER))
    limiter = SimpleNamespace(
        is_blocked=AsyncMock(return_value=False),
        register_attempt=AsyncMock(),
        reset=AsyncMock(),
    )

    result = await login(
        LoginRequest(username="admin", password="admin123"), response, auth, limiter
    )

    assert result.username == "admin"
    assert "trendscout_access=" in response.headers["set-cookie"]
    limiter.reset.assert_awaited_once_with("admin")


async def test_login_rejects_invalid_credentials() -> None:
    response = Response()
    auth = SimpleNamespace(authenticate=AsyncMock(return_value=None))
    limiter = SimpleNamespace(
        is_blocked=AsyncMock(return_value=False),
        register_attempt=AsyncMock(),
        reset=AsyncMock(),
    )

    with pytest.raises(HTTPException) as raised:
        await login(LoginRequest(username="admin", password="wrong"), response, auth, limiter)

    assert raised.value.status_code == 401
    limiter.register_attempt.assert_awaited_once_with("admin")


async def test_login_rejects_blocked_username() -> None:
    limiter = SimpleNamespace(is_blocked=AsyncMock(return_value=True))

    with pytest.raises(HTTPException) as raised:
        await login(
            LoginRequest(username="admin", password="wrong"),
            Response(),
            SimpleNamespace(),
            limiter,
        )

    assert raised.value.status_code == 429


async def test_current_user_requires_valid_cookie() -> None:
    auth = SimpleNamespace(get_by_username=AsyncMock(return_value=USER))

    with pytest.raises(HTTPException) as missing:
        await get_current_user(auth, None)
    with pytest.raises(HTTPException) as forged:
        await get_current_user(auth, "forged")

    assert missing.value.status_code == 401
    assert forged.value.status_code == 401
    assert await get_current_user(auth, issue_token("admin")) is USER


async def test_session_endpoints_return_user_and_clear_cookie() -> None:
    response = Response()

    assert (await me(USER)).username == "admin"
    await logout(response)

    assert "trendscout_access=" in response.headers["set-cookie"]


async def test_product_handlers_delegate_validated_query() -> None:
    page = ProductPage(items=[], total=0, limit=24, offset=0)
    products = SimpleNamespace(
        list_page=AsyncMock(return_value=page),
        categories=AsyncMock(return_value=["Home & Kitchen"]),
    )
    query = ProductQuery(limit=24)

    assert await list_products(USER, products, query) == page
    assert await list_categories(USER, products) == ["Home & Kitchen"]
    products.list_page.assert_awaited_once_with(query)


async def test_category_handlers_list_and_save_selection() -> None:
    rows = [SimpleNamespace(slug="home-garden", name="Home & Kitchen", enabled=True)]
    categories = SimpleNamespace(
        list_available=AsyncMock(return_value=rows),
        set_enabled=AsyncMock(return_value=rows),
    )

    listed = await category_router.list_amazon_categories(USER, categories)
    selected = await category_router.select_amazon_categories(
        AmazonCategorySelection(slugs=["home-garden"]), USER, categories
    )

    assert listed[0].name == "Home & Kitchen"
    assert selected[0].enabled is True


async def test_category_handler_reports_unknown_slug() -> None:
    categories = SimpleNamespace(set_enabled=AsyncMock(side_effect=UnknownCategoryError("missing")))

    with pytest.raises(HTTPException) as raised:
        await category_router.select_amazon_categories(
            AmazonCategorySelection(slugs=["missing"]), USER, categories
        )

    assert raised.value.status_code == 422


async def test_run_handlers_list_queue_and_reject_conflicts(monkeypatch) -> None:
    run = SimpleNamespace(
        id=1,
        kind=RunKind.AMAZON,
        status=RunStatus.SUCCESS,
        items_collected=20,
        detail=None,
        created_at=NOW,
        finished_at=NOW,
    )
    runs = SimpleNamespace(
        recent=AsyncMock(return_value=[run]), active=AsyncMock(return_value=None)
    )
    task = SimpleNamespace(kiq=AsyncMock(return_value=SimpleNamespace(task_id="task-1")))
    monkeypatch.setitem(runs_router._JOB_BY_KIND, RunKind.AMAZON, task)

    listed = await runs_router.list_runs(USER, runs)
    triggered = await runs_router.trigger_run(RunKind.AMAZON, USER, runs)

    assert listed[0].status is RunStatus.SUCCESS
    assert triggered.task_id == "task-1"

    runs.active.return_value = SimpleNamespace(kind=RunKind.TRENDS)
    with pytest.raises(HTTPException) as raised:
        await runs_router.trigger_run(RunKind.AMAZON, USER, runs)
    assert raised.value.status_code == 409


async def test_sales_boost_handlers_manage_records(monkeypatch) -> None:
    record = past_product()
    service = SimpleNamespace(
        list_all=AsyncMock(return_value=[record]),
        add=AsyncMock(return_value=record),
        delete=AsyncMock(return_value=True),
    )
    scoring_task = SimpleNamespace(kiq=AsyncMock())
    monkeypatch.setattr(salesboost_router, "score_products", scoring_task)

    listed = await list_past_products(USER, service)
    created = await add_past_product(
        PastProductCreate(title="Garden Hose", category="Garden"), USER, service
    )
    await delete_past_product(1, USER, service)

    assert listed[0].id == 1
    assert created.title == "Garden Hose"
    assert scoring_task.kiq.await_count == 2


async def test_sales_boost_delete_reports_missing_record() -> None:
    service = SimpleNamespace(delete=AsyncMock(return_value=False))

    with pytest.raises(HTTPException) as raised:
        await delete_past_product(999, USER, service)

    assert raised.value.status_code == 404


async def test_sales_boost_import_queues_rescore(monkeypatch) -> None:
    service = SimpleNamespace(add_many=AsyncMock(return_value=1))
    scoring_task = SimpleNamespace(kiq=AsyncMock())
    monkeypatch.setattr(salesboost_router, "score_products", scoring_task)
    file = UploadFile(
        filename="winners.csv",
        file=BytesIO(b"title,category,keywords\nGarden Hose,Garden,hose\n"),
    )

    report = await import_past_products(USER, service, file)

    assert report.imported == 1
    scoring_task.kiq.assert_awaited_once_with(rescore_all=True)
