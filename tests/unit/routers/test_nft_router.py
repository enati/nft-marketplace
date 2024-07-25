from nft_service.src.schemas.transaction_schema import TransactionResponse
from nft_service.src.schemas.nft_schema import NFTFetchResponse, NFTFileResponse, NFTResponse, NFTThumbnailResponse
from nft_service.src.schemas.user_schema import UserResponse
from nft_service.src.models.nft import NFTFile
from nft_service.src.models.user import User
from nft_service.src.routers import nft_router
from nft_service.src.context import Context
from nft_service.src.exceptions import NotFound, InternalError, BadRequest
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from fastapi import status
import pytest
import os
import pkg_resources
from typing import Any, List
from sqlmodel import Session
from datetime import datetime
from tests import utils
from datetime import date

NFT_ENDPOINT: str = "/nft/"
MINT_ENDPOINT: str = "/nft/mint/"
BUY_ENDPOINT: str = "/nft/buy/"
SELL_ENDPOINT: str = "/nft/sell/"
RESOURCES_PATH: str = os.path.join(os.path.dirname(__file__), "../resources/static/")


@pytest.mark.asyncio
async def test_fetch_nft_ok(client: TestClient, session: Session, monkeypatch: Any) -> None:
    nft_fake_id = 99

    user_dict = dict(id=1, username="dummy-user", date_=date.today())

    # We are testing only the endpoint so we mock de service
    async def fetch(*args, **kargs) -> NFTFetchResponse:  # type: ignore
        return NFTFetchResponse(
            id=1,
            creation_date=datetime.now(),
            description="dummy_description",
            owner=UserResponse(**user_dict),
            creators=[],
            file=NFTFileResponse(filename="puppy.jpg", file="dummy-base64"),
        )

    monkeypatch.setattr(nft_router.NFTService, "fetch", fetch)

    response = client.get(f"{NFT_ENDPOINT}{nft_fake_id}")

    # Verify endpoint returns 200
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_json["description"] == "dummy_description"
    assert response_json["file"]["filename"] == "puppy.jpg"
    assert response_json["creators"] == []


@pytest.mark.asyncio
async def test_fetch_nft_404_err(client: TestClient, monkeypatch: Any) -> None:
    nft_fake_id = 99

    # We are testing only the endpoint so we mock de service
    async def fetch(*args, **kargs) -> NFTFetchResponse:  # type: ignore
        raise NotFound(details="dummy exception")

    monkeypatch.setattr(nft_router.NFTService, "fetch", fetch)

    response = client.get(f"{NFT_ENDPOINT}{nft_fake_id}")

    # Verify endpoint returns 404
    response_json = response.json()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_json["detail"] == "dummy exception"


@pytest.mark.asyncio
async def test_fetch_nft_422_err(client: TestClient, monkeypatch: Any) -> None:
    nft_fake_id = 99

    # We are testing only the endpoint so we mock de service
    async def fetch(*args, **kargs) -> NFTFetchResponse:  # type: ignore
        raise RequestValidationError(errors=[])

    monkeypatch.setattr(nft_router.NFTService, "fetch", fetch)

    response = client.get(f"{NFT_ENDPOINT}{nft_fake_id}")

    # Verify endpoint returns 422
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_fetch_nft_500_err(client: TestClient, monkeypatch: Any) -> None:
    nft_fake_id = 99

    # We are testing only the endpoint so we mock de service
    async def fetch(*args, **kargs) -> NFTFetchResponse:  # type: ignore
        raise InternalError(details="dummy exception")

    monkeypatch.setattr(nft_router.NFTService, "fetch", fetch)

    response = client.get(f"{NFT_ENDPOINT}{nft_fake_id}")

    # Verify endpoint returns 500
    response_json = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_json["detail"] == "dummy exception"


@pytest.mark.asyncio
async def test_nft_get_all_ok(client: TestClient, monkeypatch: Any) -> None:
    user_dict = dict(id=1, username="dummy-user", date_=date.today())

    # We are testing only the endpoint so we mock de service
    async def get_all(*args, **kargs) -> List[NFTResponse]:  # type: ignore
        return [
            NFTResponse(
                id=1,
                creation_date=datetime.now(),
                description="dummy_description",
                owner=UserResponse(**user_dict),
                creators=[],
                file=NFTThumbnailResponse(filename="puppy.jpg", thumbnail="dummy-base64"),
            ),
            NFTResponse(
                id=2,
                creation_date=datetime.now(),
                description="dummy_description",
                owner=UserResponse(**user_dict),
                creators=[],
                file=NFTThumbnailResponse(filename="puppy.jpg", thumbnail="dummy-base64"),
            ),
        ]

    monkeypatch.setattr(nft_router.NFTService, "get_all", get_all)

    response = client.get(NFT_ENDPOINT)

    # Verify endpoint returns 200
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert len(response_json) == 2


@pytest.mark.asyncio
async def test_nft_get_all_422_err(client: TestClient, monkeypatch: Any) -> None:
    # We are testing only the endpoint so we mock de service
    async def get_all(*args, **kargs) -> List[NFTResponse]:  # type: ignore
        raise RequestValidationError(errors=[])

    monkeypatch.setattr(nft_router.NFTService, "get_all", get_all)

    response = client.get(NFT_ENDPOINT)

    # Verify endpoint returns 422
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_nft_get_all_500_err(client: TestClient, monkeypatch: Any) -> None:
    # We are testing only the endpoint so we mock de service
    async def get_all(*args, **kargs) -> List[NFTResponse]:  # type: ignore
        raise InternalError(details="dummy exception")

    monkeypatch.setattr(nft_router.NFTService, "get_all", get_all)

    response = client.get(NFT_ENDPOINT)

    # Verify endpoint returns 500
    response_json = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_json["detail"] == "dummy exception"


@pytest.mark.asyncio
async def test_mint_nft_ok(client: TestClient, session: Session, monkeypatch: Any) -> None:
    # First persist some user to acts as logged user
    user: User = utils.persist_new_user(username="test-user", session=session)

    # Mock the context to simulate loggin
    def mocked_default_context() -> Any:
        context: Context = Context(username=user.username, system_date=datetime.now(), user_ip="localhost")
        return context

    monkeypatch.setattr(nft_router.Context, "default_context", mocked_default_context)

    data = {"description": "dummy_description"}

    # We are testing only the endpoint so we mock de service
    async def add(*args, **kargs) -> NFTFetchResponse:  # type: ignore
        return NFTFetchResponse(
            id=1,
            creation_date=datetime.now(),
            description=data["description"],
            owner=UserResponse(**user.dict()),
            creators=[],
            file=NFTFileResponse(filename="puppy.jpg", file="dummy-base64"),
        )

    monkeypatch.setattr(nft_router.NFTService, "add", add)

    with open(pkg_resources.resource_filename("tests.resources", "puppy.jpg"), "rb") as fo:
        files = {"file": fo}
        response = client.post(MINT_ENDPOINT, files=files, data=data)

        # Verify endpoint returns 200
        response_json = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_json["description"] == "dummy_description"
        assert response_json["file"]["filename"] == "puppy.jpg"
        assert response_json["creators"] == []


@pytest.mark.asyncio
async def test_mint_nft_400_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    # First persist some user to acts as logged user
    user: User = utils.persist_new_user(username="test-user", session=session)

    # Mock the context to simulate loggin
    def mocked_default_context() -> Any:
        context: Context = Context(username=user.username, system_date=datetime.now(), user_ip="localhost")
        return context

    monkeypatch.setattr(nft_router.Context, "default_context", mocked_default_context)

    data = {"description": "dummy_description"}

    # We are testing only the endpoint so we mock de service
    async def add(*args, **kargs) -> NFTFetchResponse:  # type: ignore
        raise BadRequest(details="dummy exception")

    monkeypatch.setattr(nft_router.NFTService, "add", add)

    with open(pkg_resources.resource_filename("tests.resources", "puppy.jpg"), "rb") as fo:
        files = {"file": fo}
        response = client.post(MINT_ENDPOINT, files=files, data=data)

        # Verify endpoint returns 400
        response_json = response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_json["detail"] == "dummy exception"


@pytest.mark.asyncio
async def test_mint_nft_422_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    # First persist some user to acts as logged user
    user: User = utils.persist_new_user(username="test-user", session=session)

    # Mock the context to simulate loggin
    def mocked_default_context() -> Any:
        context: Context = Context(username=user.username, system_date=datetime.now(), user_ip="localhost")
        return context

    monkeypatch.setattr(nft_router.Context, "default_context", mocked_default_context)

    data = {"description": "dummy_description"}

    # We are testing only the endpoint so we mock de service
    async def add(*args, **kargs) -> NFTFetchResponse:  # type: ignore
        raise RequestValidationError(errors=[])

    monkeypatch.setattr(nft_router.NFTService, "add", add)

    with open(pkg_resources.resource_filename("tests.resources", "puppy.jpg"), "rb") as fo:
        files = {"file": fo}
        response = client.post(MINT_ENDPOINT, files=files, data=data)

        # Verify endpoint returns 422
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_mint_nft_500_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    # First persist some user to acts as logged user
    user: User = utils.persist_new_user(username="test-user", session=session)

    # Mock the context to simulate loggin
    def mocked_default_context() -> Any:
        context: Context = Context(username=user.username, system_date=datetime.now(), user_ip="localhost")
        return context

    monkeypatch.setattr(nft_router.Context, "default_context", mocked_default_context)

    data = {"description": "dummy_description"}

    # We are testing only the endpoint so we mock de service
    async def add(*args, **kargs) -> NFTFetchResponse:  # type: ignore
        raise InternalError(details="dummy exception")

    monkeypatch.setattr(nft_router.NFTService, "add", add)

    with open(pkg_resources.resource_filename("tests.resources", "puppy.jpg"), "rb") as fo:
        files = {"file": fo}
        response = client.post(MINT_ENDPOINT, files=files, data=data)

        # Verify endpoint returns 500
        response_json = response.json()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response_json["detail"] == "dummy exception"


@pytest.mark.asyncio
async def test_mint_nft_without_required_fields_err(client: TestClient, monkeypatch: Any) -> None:
    response = client.post(MINT_ENDPOINT, data={})

    # We are testing only the endpoint so we mock de service
    async def add(*args, **kargs) -> Any:  # type: ignore
        return None

    monkeypatch.setattr(nft_router.NFTService, "add", add)

    response_json = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert len(response_json["detail"]) == 2
    assert response_json["detail"][0]["loc"] == ["body", "file"]
    assert response_json["detail"][0]["msg"] == "field required"
    assert response_json["detail"][1]["loc"] == ["body", "description"]
    assert response_json["detail"][1]["msg"] == "field required"


@pytest.mark.asyncio
async def test_mint_nft_with_wrong_file_format_err(client: TestClient, monkeypatch: Any) -> None:
    # We are testing only the endpoint so we mock de service
    async def add(*args, **kargs) -> Any:  # type: ignore
        return None

    monkeypatch.setattr(nft_router.NFTService, "add", add)

    with open(pkg_resources.resource_filename("tests.resources", "bad_nft_format.txt"), "rb") as fo:
        files = {"file": fo}
        data = {"description": "dummy_description"}
        response = client.post(MINT_ENDPOINT, files=files, data=data)

        response_json = response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_json["error"] == "invalid_request"
        assert response_json["detail"] == "File extension not allowed"


@pytest.mark.asyncio
async def test_buy_nft_ok(client: TestClient, session: Session, monkeypatch: Any) -> None:
    # First persist some user to acts as logged user
    buyer_user: User = utils.persist_new_user(username="test-buyer", session=session)
    seller_user: User = utils.persist_new_user(username="test-seller", session=session)

    # Persis new nft in db
    file_obj: NFTFile = utils.persist_new_file("puppy.jpg", session)
    nft_obj = utils._new_NFT(file_id=file_obj.id, owner_id=seller_user.id, session=session)  # type: ignore

    # Mock the context to simulate loggin
    def mocked_default_context() -> Any:
        context: Context = Context(username=buyer_user.username, system_date=datetime.now(), user_ip="localhost")
        return context

    monkeypatch.setattr(nft_router.Context, "default_context", mocked_default_context)

    # We are testing only the endpoint so we mock de service
    async def trade_nft(*args, **kargs) -> TransactionResponse:  # type: ignore
        return TransactionResponse(
            id=1,
            creation_date=datetime.now(),
            nft_id=nft_obj.id,
            buyer=UserResponse(**buyer_user.dict()),
            seller=UserResponse(**seller_user.dict()),
            price=100,
        )

    monkeypatch.setattr(nft_router.NFTService, "trade_nft", trade_nft)
    request = dict(buyer=buyer_user.username, seller=seller_user.username, price=100)
    response = client.post(f"{BUY_ENDPOINT}{nft_obj.id}", json=request)

    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_json["id"] == 1
    assert response_json["nft_id"] == nft_obj.id
    assert response_json["buyer"]["id"] == buyer_user.id
    assert response_json["seller"]["id"] == seller_user.id


@pytest.mark.asyncio
async def test_buy_400_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    fake_nft_id = 99

    # We are testing only the endpoint so we mock de service
    async def trade_nft(*args, **kargs) -> TransactionResponse:  # type: ignore
        raise BadRequest(details="dummy exception")

    monkeypatch.setattr(nft_router.NFTService, "trade_nft", trade_nft)
    request = dict(buyer="dummy-buyer", seller="dummy-seller", price=100)
    response = client.post(f"{BUY_ENDPOINT}{fake_nft_id}", json=request)

    response_json = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_json["detail"] == "dummy exception"


@pytest.mark.asyncio
async def test_buy_404_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    fake_nft_id = 99

    # We are testing only the endpoint so we mock de service
    async def trade_nft(*args, **kargs) -> TransactionResponse:  # type: ignore
        raise NotFound(details="dummy exception")

    monkeypatch.setattr(nft_router.NFTService, "trade_nft", trade_nft)
    request = dict(buyer="dummy-buyer", seller="dummy-seller", price=100)
    response = client.post(f"{BUY_ENDPOINT}{fake_nft_id}", json=request)

    response_json = response.json()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_json["detail"] == "dummy exception"


@pytest.mark.asyncio
async def test_buy_422_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    fake_nft_id = 99

    # We are testing only the endpoint so we mock de service
    async def trade_nft(*args, **kargs) -> TransactionResponse:  # type: ignore
        raise RequestValidationError(errors=[])

    monkeypatch.setattr(nft_router.NFTService, "trade_nft", trade_nft)
    request = dict(buyer="dummy-buyer", seller="dummy-seller", price=100)
    response = client.post(f"{BUY_ENDPOINT}{fake_nft_id}", json=request)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_buy_500_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    fake_nft_id = 99

    # We are testing only the endpoint so we mock de service
    async def trade_nft(*args, **kargs) -> TransactionResponse:  # type: ignore
        raise InternalError(details="dummy exception")

    monkeypatch.setattr(nft_router.NFTService, "trade_nft", trade_nft)
    request = dict(buyer="dummy-buyer", seller="dummy-seller", price=100)
    response = client.post(f"{BUY_ENDPOINT}{fake_nft_id}", json=request)

    response_json = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_json["detail"] == "dummy exception"


@pytest.mark.asyncio
async def test_sell_nft_endpoint_ok(client: TestClient, session: Session, monkeypatch: Any) -> None:
    # First persist some user to acts as logged user
    buyer_user: User = utils.persist_new_user(username="test-buyer", session=session)
    seller_user: User = utils.persist_new_user(username="test-seller", session=session)

    # Persis new nft in db
    file_obj: NFTFile = utils.persist_new_file("puppy.jpg", session)
    nft_obj = utils._new_NFT(file_id=file_obj.id, owner_id=buyer_user.id, session=session)  # type: ignore

    # Mock the context to simulate loggin
    def mocked_default_context() -> Any:
        context: Context = Context(username=seller_user.username, system_date=datetime.now(), user_ip="localhost")
        return context

    monkeypatch.setattr(nft_router.Context, "default_context", mocked_default_context)

    # We are testing only the endpoint so we mock de service
    async def trade_nft(*args, **kargs) -> TransactionResponse:  # type: ignore
        return TransactionResponse(
            id=1,
            creation_date=datetime.now(),
            nft_id=nft_obj.id,
            buyer=UserResponse(**buyer_user.dict()),
            seller=UserResponse(**seller_user.dict()),
            price=100,
        )

    monkeypatch.setattr(nft_router.NFTService, "trade_nft", trade_nft)
    request = dict(buyer=buyer_user.username, seller=seller_user.username, price=100)
    response = client.post(f"{SELL_ENDPOINT}{nft_obj.id}", json=request)

    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_json["id"] == 1
    assert response_json["nft_id"] == nft_obj.id
    assert response_json["buyer"]["id"] == buyer_user.id
    assert response_json["seller"]["id"] == seller_user.id


@pytest.mark.asyncio
async def test_sell_nft_400_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    fake_nft_id = 99

    # We are testing only the endpoint so we mock de service
    async def trade_nft(*args, **kargs) -> TransactionResponse:  # type: ignore
        raise BadRequest(details="dummy exception")

    monkeypatch.setattr(nft_router.NFTService, "trade_nft", trade_nft)
    request = dict(buyer="dummy-buyer", seller="dummy-seller", price=100)
    response = client.post(f"{SELL_ENDPOINT}{fake_nft_id}", json=request)

    response_json = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_json["detail"] == "dummy exception"


@pytest.mark.asyncio
async def test_sell_nft_404_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    fake_nft_id = 99

    # We are testing only the endpoint so we mock de service
    async def trade_nft(*args, **kargs) -> TransactionResponse:  # type: ignore
        raise NotFound(details="dummy exception")

    monkeypatch.setattr(nft_router.NFTService, "trade_nft", trade_nft)
    request = dict(buyer="dummy-buyer", seller="dummy-seller", price=100)
    response = client.post(f"{SELL_ENDPOINT}{fake_nft_id}", json=request)

    response_json = response.json()
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_json["detail"] == "dummy exception"


@pytest.mark.asyncio
async def test_sell_nft_422_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    fake_nft_id = 99

    # We are testing only the endpoint so we mock de service
    async def trade_nft(*args, **kargs) -> TransactionResponse:  # type: ignore
        raise RequestValidationError(errors=[])

    monkeypatch.setattr(nft_router.NFTService, "trade_nft", trade_nft)
    request = dict(buyer="dummy-buyer", seller="dummy-seller", price=100)
    response = client.post(f"{SELL_ENDPOINT}{fake_nft_id}", json=request)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_sell_nft_500_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    fake_nft_id = 99

    # We are testing only the endpoint so we mock de service
    async def trade_nft(*args, **kargs) -> TransactionResponse:  # type: ignore
        raise InternalError(details="dummy exception")

    monkeypatch.setattr(nft_router.NFTService, "trade_nft", trade_nft)
    request = dict(buyer="dummy-buyer", seller="dummy-seller", price=100)
    response = client.post(f"{SELL_ENDPOINT}{fake_nft_id}", json=request)

    response_json = response.json()
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response_json["detail"] == "dummy exception"
