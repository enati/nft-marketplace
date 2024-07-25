from nft_service.src.schemas.user_schema import UserResponse
from nft_service.src.routers import user_router
from nft_service.src.exceptions import InternalError, NotFound
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from fastapi import status
import pytest
from datetime import date
from typing import List, Any

USER_ENDPOINT: str = "/user/"


@pytest.mark.asyncio
async def test_get_all_ok(client: TestClient, monkeypatch: Any) -> None:
    # We are testing only the endpoint so we mock de service
    async def get_all(*args, **kargs) -> List[UserResponse]:  # type: ignore
        return [
            UserResponse(id=1, date_=date.today(), username="dummy-user-1"),
            UserResponse(id=2, date_=date.today(), username="dummy-user-2"),
        ]

    monkeypatch.setattr(user_router.UserService, "get_all", get_all)

    response = client.get(USER_ENDPOINT)

    # Verify endpoint returns 200
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert len(response_json) == 2


@pytest.mark.asyncio
async def test_get_all_422_err(client: TestClient, monkeypatch: Any) -> None:
    # We are testing only the endpoint so we mock de service
    async def get_all(*args, **kargs) -> List[UserResponse]:  # type: ignore
        raise RequestValidationError(errors=[])

    monkeypatch.setattr(user_router.UserService, "get_all", get_all)

    response = client.get(USER_ENDPOINT)

    # Verify endpoint returns 422
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_all_500_err(client: TestClient, monkeypatch: Any) -> None:
    # We are testing only the endpoint so we mock de service
    async def get_all(*args, **kargs) -> List[UserResponse]:  # type: ignore
        raise InternalError(details="dummy exception")

    monkeypatch.setattr(user_router.UserService, "get_all", get_all)

    response = client.get(USER_ENDPOINT)

    # Verify endpoint returns 500
    response_json = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_json["detail"] == "dummy exception"


@pytest.mark.asyncio
async def test_get_fetch_ok(client: TestClient, monkeypatch: Any) -> None:
    fake_user_id = 99

    # We are testing only the endpoint so we mock de service
    async def fetch(*args, **kargs) -> UserResponse:  # type: ignore
        return UserResponse(id=fake_user_id, date_=date.today(), username="dummy-user-1")

    monkeypatch.setattr(user_router.UserService, "fetch", fetch)

    response = client.get(f"{USER_ENDPOINT}{fake_user_id}")

    # Verify endpoint returns 200
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_json["id"] == fake_user_id
    assert response_json["username"] == "dummy-user-1"


@pytest.mark.asyncio
async def test_get_fetch_404_err(client: TestClient, monkeypatch: Any) -> None:
    fake_user_id = 99

    # We are testing only the endpoint so we mock de service
    async def fetch(*args, **kargs) -> UserResponse:  # type: ignore
        raise NotFound(details="dummy exception")

    monkeypatch.setattr(user_router.UserService, "fetch", fetch)

    response = client.get(f"{USER_ENDPOINT}{fake_user_id}")

    # Verify endpoint returns 404
    response_json = response.json()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_json["detail"] == "dummy exception"
