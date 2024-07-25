from nft_service.src.models.user import User
from nft_service.src.schemas.balance_schema import BalanceResponse
from nft_service.src.schemas.user_schema import UserResponse
from nft_service.src.routers import balance_router
from nft_service.src.exceptions import InternalError
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from fastapi import status
import pytest
from typing import List
from typing import Any
from sqlmodel import Session
from datetime import datetime
from tests import utils

BALANCE_ENDPOINT: str = "/balance/"


@pytest.mark.asyncio
async def test_get_all_ok(client: TestClient, session: Session, monkeypatch: Any) -> None:
    # First persist some user to acts as logged user
    logged_user: User = utils.persist_new_user(username="test-logged-user", session=session)

    # We are testing only the endpoint so we mock de service
    async def get_all_history(*args, **kargs) -> List[BalanceResponse]:  # type: ignore
        return [
            BalanceResponse(
                creation_date=datetime.now(),
                user=UserResponse(**logged_user.dict()),
                initial_amount=0,
                final_amount=100,
            ),
            BalanceResponse(
                creation_date=datetime.now(),
                user=UserResponse(**logged_user.dict()),
                initial_amount=100,
                final_amount=200,
            ),
        ]

    monkeypatch.setattr(balance_router.BalanceService, "get_all_history", get_all_history)

    response = client.get(BALANCE_ENDPOINT)

    # Verify endpoint returns 200
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert len(response_json) == 2


@pytest.mark.asyncio
async def test_get_all_422_err(client: TestClient, monkeypatch: Any) -> None:
    # We are testing only the endpoint so we mock de service
    async def get_all_history(*args, **kargs) -> List[BalanceResponse]:  # type: ignore
        raise RequestValidationError(errors=[])

    monkeypatch.setattr(balance_router.BalanceService, "get_all_history", get_all_history)

    response = client.get(BALANCE_ENDPOINT)

    # Verify endpoint returns 422
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_all_500_err(client: TestClient, monkeypatch: Any) -> None:
    # We are testing only the endpoint so we mock de service
    async def get_all_history(*args, **kargs) -> List[BalanceResponse]:  # type: ignore
        raise InternalError(details="dummy exception")

    monkeypatch.setattr(balance_router.BalanceService, "get_all_history", get_all_history)

    response = client.get(BALANCE_ENDPOINT)

    response_json = response.json()
    # Verify endpoint returns 500
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_json["detail"] == "dummy exception"


@pytest.mark.asyncio
async def test_get_all_by_user_ok(client: TestClient, session: Session, monkeypatch: Any) -> None:
    # First persist some user to acts as logged user
    logged_user: User = utils.persist_new_user(username="test-logged-user", session=session)

    # We are testing only the endpoint so we mock de service
    async def get_all_history_for_user(*args, **kargs) -> List[BalanceResponse]:  # type: ignore
        return [
            BalanceResponse(
                creation_date=datetime.now(),
                user=UserResponse(**logged_user.dict()),
                initial_amount=0,
                final_amount=100,
            ),
            BalanceResponse(
                creation_date=datetime.now(),
                user=UserResponse(**logged_user.dict()),
                initial_amount=100,
                final_amount=200,
            ),
        ]

    monkeypatch.setattr(balance_router.BalanceService, "get_all_history_for_user", get_all_history_for_user)

    response = client.get(f"{BALANCE_ENDPOINT}{logged_user.id}")

    # Verify endpoint returns 200
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert len(response_json) == 2


@pytest.mark.asyncio
async def test_get_all_by_user_422_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    fake_user_id = 99

    # We are testing only the endpoint so we mock de service
    async def get_all_history_for_user(*args, **kargs) -> List[BalanceResponse]:  # type: ignore
        raise RequestValidationError(errors=[])

    monkeypatch.setattr(balance_router.BalanceService, "get_all_history_for_user", get_all_history_for_user)

    response = client.get(f"{BALANCE_ENDPOINT}{fake_user_id}")

    # Verify endpoint returns 500
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_all_by_user_500_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    fake_user_id = 99

    # We are testing only the endpoint so we mock de service
    async def get_all_history_for_user(*args, **kargs) -> List[BalanceResponse]:  # type: ignore
        raise InternalError(details="dummy exception")

    monkeypatch.setattr(balance_router.BalanceService, "get_all_history_for_user", get_all_history_for_user)

    response = client.get(f"{BALANCE_ENDPOINT}{fake_user_id}")

    response_json = response.json()
    # Verify endpoint returns 500
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_json["detail"] == "dummy exception"
