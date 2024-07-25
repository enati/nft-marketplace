from nft_service.src.schemas.transaction_schema import TransactionResponse
from nft_service.src.schemas.user_schema import UserResponse
from nft_service.src.exceptions import InternalError
from nft_service.src.routers import transaction_router
from fastapi.testclient import TestClient
from fastapi import status
import pytest
from typing import Any, List
from fastapi.exceptions import RequestValidationError
from datetime import datetime, date

TRANSACTION_ENDPOINT: str = "/transaction/"


@pytest.mark.asyncio
async def test_get_all_ok(client: TestClient, monkeypatch: Any) -> None:
    fake_nft_id = 99
    buyer_dict = dict(id=1, username="test-buyer", date_=date.today())
    seller_dict = dict(id=2, username="test-seller", date_=date.today())

    # We are testing only the endpoint so we mock de service
    async def get_all(*args, **kargs) -> List[TransactionResponse]:  # type: ignore
        return [
            TransactionResponse(
                id=1,
                creation_date=datetime.now(),
                nft_id=fake_nft_id,
                buyer=UserResponse(**buyer_dict),
                seller=UserResponse(**seller_dict),
                price=100,
            )
        ]

    monkeypatch.setattr(transaction_router.TransactionService, "get_all", get_all)

    response = client.get(TRANSACTION_ENDPOINT)

    # Verify endpoint returns 200
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert len(response_json) == 1
    assert response_json[0]["id"] == 1
    assert response_json[0]["nft_id"] == fake_nft_id
    assert response_json[0]["buyer"]["id"] == buyer_dict["id"]
    assert response_json[0]["seller"]["id"] == seller_dict["id"]
    assert response_json[0]["price"] == 100


@pytest.mark.asyncio
async def test_get_all_422_err(client: TestClient, monkeypatch: Any) -> None:
    # We are testing only the endpoint so we mock de service
    async def get_all(*args, **kargs) -> List[TransactionResponse]:  # type: ignore
        raise RequestValidationError(errors=[])

    monkeypatch.setattr(transaction_router.TransactionService, "get_all", get_all)

    response = client.get(TRANSACTION_ENDPOINT)

    # Verify endpoint returns 422
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_all_500_err(client: TestClient, monkeypatch: Any) -> None:
    # We are testing only the endpoint so we mock de service
    async def get_all(*args, **kargs) -> List[TransactionResponse]:  # type: ignore
        raise InternalError(details="dummy exception")

    monkeypatch.setattr(transaction_router.TransactionService, "get_all", get_all)

    response = client.get(TRANSACTION_ENDPOINT)

    # Verify endpoint returns 500
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
