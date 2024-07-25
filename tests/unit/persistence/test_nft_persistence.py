from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session, select
from fastapi import status
from nft_service.src.models.nft import NFTFile, NFT
from nft_service.src.models.user import User
from nft_service.src.models.transaction import Transaction
from nft_service.src.models.balance import UserBalance
from nft_service.src.context import Context
from nft_service.src.services import nft_service
import tests.utils as utils
from typing import Any
import os
from datetime import datetime
from nft_service.src.routers import nft_router
import pkg_resources


RESOURCES_PATH: str = os.path.join(os.path.dirname(__file__), "../../resources/static/")
MINT_ENDPOINT: str = "/nft/mint/"


@pytest.mark.asyncio
async def test_mint_nft_persist_ok(client: TestClient, session: Session, monkeypatch: Any) -> None:
    # First persist three users. One to acts as logged user and two for the cocreators
    user: User = utils.persist_new_user(username="test-user", session=session)
    user_c1: User = utils.persist_new_user(username="test-cocreator-1", session=session)
    user_c2: User = utils.persist_new_user(username="test-cocreator-2", session=session)

    # Mock the context to simulate loggin
    def mocked_default_context() -> Any:
        context: Context = Context(username=user.username, system_date=datetime.now(), user_ip="localhost")
        return context

    monkeypatch.setattr(nft_router.Context, "default_context", mocked_default_context)
    monkeypatch.setattr(nft_service.cf, "STATIC_PATH", RESOURCES_PATH)
    with open(pkg_resources.resource_filename("tests.resources", "puppy.jpg"), "rb") as fo:
        files = {"file": fo}
        data = {"description": "dummy_description", "creators": [user_c1.username, user_c2.username]}
        response = client.post(MINT_ENDPOINT, files=files, data=data)

        # Verify endpoint returns 200
        response_json = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_json["description"] == "dummy_description"
        assert response_json["file"]["filename"] == "puppy.jpg"
        assert len(response_json["creators"]) == 2
        assert response_json["creators"][0]["username"] == "test-cocreator-1"
        assert response_json["creators"][1]["username"] == "test-cocreator-2"

    # Check that NFT and NFTFile are persisted correctly
    nft_file_obj = session.exec(select(NFTFile).where(NFTFile.filename == "puppy.jpg")).one()
    assert nft_file_obj

    nft_obj = session.exec(select(NFT).where(NFT.id == response_json["id"])).one()
    assert nft_obj
    assert nft_obj.description == "dummy_description"
    assert nft_obj.file_id == nft_file_obj.id
    assert len(nft_obj.creators) == 2
    assert nft_obj.creators[0].id == user_c1.id
    assert nft_obj.creators[1].id == user_c2.id


@pytest.mark.asyncio
async def test_mint_file_failed_then_nft_not_persisted_ok(
    client: TestClient, session: Session, monkeypatch: Any
) -> None:
    # Test that if the NFT file fails to persist the NFT is not persisted

    # First persist one user to acts as logged user
    user: User = utils.persist_new_user(username="test-user", session=session)

    # Mock the context to simulate loggin
    def mocked_default_context() -> Any:
        context: Context = Context(username=user.username, system_date=datetime.now(), user_ip="localhost")
        return context

    monkeypatch.setattr(nft_router.Context, "default_context", mocked_default_context)

    # Mock the file persistent part to force the failure
    def _process_file(self: Any, file: Any) -> Any:
        raise Exception

    monkeypatch.setattr(nft_service.NFTService, "_process_file", _process_file)

    with open(pkg_resources.resource_filename("tests.resources", "puppy.jpg"), "rb") as fo:
        files = {"file": fo}
        data = {"description": "dummy_description"}
        response = client.post(MINT_ENDPOINT, files=files, data=data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # Check that NFT is not persisted
        result = session.exec(select(NFT)).all()
        assert not result


@pytest.mark.asyncio
async def test_mint_nft_failed_then_image_not_persisted_ok(
    client: TestClient, session: Session, monkeypatch: Any
) -> None:
    # Test that if the NFT fails to persist the file is not persisted

    # First persist one user to acts as logged user
    user: User = utils.persist_new_user(username="test-user", session=session)

    # Mock the context to simulate loggin
    def mocked_default_context() -> Any:
        context: Context = Context(username=user.username, system_date=datetime.now(), user_ip="localhost")
        return context

    monkeypatch.setattr(nft_router.Context, "default_context", mocked_default_context)

    # Mock the nft persistent part to force the failure

    def create(*args, **kwargs) -> Any:  # type: ignore
        raise Exception("Ooops!")

    monkeypatch.setattr(nft_service.NFTRepository, "create", create)

    with open(pkg_resources.resource_filename("tests.resources", "puppy.jpg"), "rb") as fo:
        files = {"file": fo}
        data = {"description": "dummy_description"}
        response = client.post(MINT_ENDPOINT, files=files, data=data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # Check that NFT is not persisted
        result = session.exec(select(NFTFile)).all()
        assert not result


@pytest.mark.asyncio
async def test_mint_nft_dont_create_transactions_ok(client: TestClient, session: Session, monkeypatch: Any) -> None:
    # First persist one user to acts as logged user
    user: User = utils.persist_new_user(username="test-user", session=session)

    # Mock the context to simulate loggin
    def mocked_default_context() -> Any:
        context: Context = Context(username=user.username, system_date=datetime.now(), user_ip="localhost")
        return context

    monkeypatch.setattr(nft_router.Context, "default_context", mocked_default_context)
    monkeypatch.setattr(nft_service.cf, "STATIC_PATH", RESOURCES_PATH)

    with open(pkg_resources.resource_filename("tests.resources", "puppy.jpg"), "rb") as fo:
        files = {"file": fo}
        data = {"description": "dummy_description"}
        response = client.post(MINT_ENDPOINT, files=files, data=data)

        assert response.status_code == status.HTTP_200_OK

        # Check that NFT is not persisted
        result = session.exec(select(Transaction)).all()
        assert not result


@pytest.mark.asyncio
async def test_mint_nft_dont_add_balance_movements_ok(client: TestClient, session: Session, monkeypatch: Any) -> None:
    # First persist one user to acts as logged user
    user: User = utils.persist_new_user(username="test-user", session=session)

    # Mock the context to simulate loggin
    def mocked_default_context() -> Any:
        context: Context = Context(username=user.username, system_date=datetime.now(), user_ip="localhost")
        return context

    monkeypatch.setattr(nft_router.Context, "default_context", mocked_default_context)
    monkeypatch.setattr(nft_service.cf, "STATIC_PATH", RESOURCES_PATH)

    # Check that before mint the balance table was empty
    balance_rows = session.exec(select(UserBalance)).all()
    assert not balance_rows

    with open(pkg_resources.resource_filename("tests.resources", "puppy.jpg"), "rb") as fo:
        files = {"file": fo}
        data = {"description": "dummy_description"}
        response = client.post(MINT_ENDPOINT, files=files, data=data)

        assert response.status_code == status.HTTP_200_OK

    # Check that the balance table is still empty
    result = session.exec(select(UserBalance)).all()
    assert not result
