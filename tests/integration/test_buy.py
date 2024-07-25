from fastapi.testclient import TestClient
from fastapi import status
import pytest
import pkg_resources
import os
from typing import Any
from sqlmodel import Session, select
from datetime import datetime
from tests import utils
from nft_service.src.models.nft import NFT
from nft_service.src.models.transaction import Transaction
from nft_service.src.models.balance import UserBalance
from nft_service.src.models.user import User
from nft_service.src.routers import nft_router
from nft_service.src.context import Context
from nft_service.src.services import nft_service


RESOURCES_PATH: str = os.path.join(os.path.dirname(__file__), "../resources/static/")
MINT_ENDPOINT: str = "/nft/mint/"
BUY_ENDPOINT: str = "/nft/buy/"


@pytest.mark.asyncio
async def test_buy_nft_ok(client: TestClient, session: Session, monkeypatch: Any) -> None:
    """
    - Login with test-logged-user
    - Mint an NFT (owner will be test-logged-user)
    - Login with test-buyer-user (only logged user can buy)
    - Buy the NFT minted (new owner is buyer)
    - Check new transaccion is generated
    - Check balances are updated
    """

    logged_username: str = ""

    # First we mock the context so that then we can change the logged user
    def mocked_default_context() -> Any:
        context: Context = Context(username=logged_username, system_date=datetime.now(), user_ip="localhost")
        return context

    monkeypatch.setattr(nft_router.Context, "default_context", mocked_default_context)
    monkeypatch.setattr(nft_service.cf, "STATIC_PATH", RESOURCES_PATH)

    # Persist some users
    logged_user: User = utils.persist_new_user(username="test-logged-user", session=session)
    buyer_user: User = utils.persist_new_user(username="test-buyer-user", session=session)
    cocreator_user: User = utils.persist_new_user(username="test-cocreator-user", session=session)

    # Add balance for users
    utils.persist_new_user_balance(
        user_id=logged_user.id, initial_amount=0, final_amount=100, session=session  # type: ignore[arg-type]
    )
    utils.persist_new_user_balance(
        user_id=buyer_user.id, initial_amount=0, final_amount=100, session=session  # type: ignore[arg-type]
    )
    utils.persist_new_user_balance(
        user_id=cocreator_user.id, initial_amount=0, final_amount=100, session=session  # type: ignore[arg-type]
    )

    # Change the logged user
    logged_username = logged_user.username

    # Mint an NFT. This operation will persist a new NFT owned by test-logged-user
    with open(pkg_resources.resource_filename("tests.resources", "puppy.jpg"), "rb") as fo:
        files = {"file": fo}
        data = {"description": "dummy_description", "creators": [cocreator_user.username]}
        response = client.post(MINT_ENDPOINT, files=files, data=data)

    # Verify endpoint returns 200
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK

    nft_id = response_json["id"]
    # Verify it was correctly persisted in db
    assert session.exec(select(NFT).where(NFT.id == nft_id)).one()

    # Now we login with the buyer user
    logged_username = buyer_user.username

    # Buy the NFT (logged_user is the owner so it becames the seller)
    json_data = {"buyer": buyer_user.username, "seller": logged_user.username, "price": 10}
    response = client.post(f"{BUY_ENDPOINT}{nft_id}", json=json_data)

    # Verify endpoints returns 200
    assert response.status_code == status.HTTP_200_OK

    # Check NFT owner was updated
    nft_result = session.exec(select(NFT).where(NFT.id == nft_id)).one()
    assert nft_result
    assert nft_result.owner_id == buyer_user.id

    # Check new transaction was created
    trx_result = session.exec(select(Transaction).where(Transaction.nft_id == nft_id)).one()
    assert trx_result
    assert trx_result.buyer_id == buyer_user.id
    assert trx_result.seller_id == logged_user.id
    assert trx_result.price == 10

    # Check balances were updated
    buyer_balance_res = session.exec(
        select(UserBalance)
        .where(UserBalance.user_id == buyer_user.id)
        .order_by(UserBalance.id.desc())  # type: ignore[union-attr]
    ).first()
    seller_balance_res = session.exec(
        select(UserBalance)
        .where(UserBalance.user_id == logged_user.id)
        .order_by(UserBalance.id.desc())  # type: ignore[union-attr]
    ).first()
    cocreator_balance_res = session.exec(
        select(UserBalance)
        .where(UserBalance.user_id == cocreator_user.id)
        .order_by(UserBalance.id.desc())  # type: ignore[union-attr]
    ).first()

    assert buyer_balance_res
    assert buyer_balance_res.initial_amount == 100
    assert buyer_balance_res.final_amount == 90  # 100 - 10 = 90

    assert seller_balance_res
    assert seller_balance_res.initial_amount == 100
    assert seller_balance_res.final_amount == 108  # 100 + 10*0.8 = 108

    assert cocreator_balance_res
    assert cocreator_balance_res.initial_amount == 100
    assert cocreator_balance_res.final_amount == 102  # 100 + 10*0.2 = 102


@pytest.mark.asyncio
async def test_buy_nft_when_buy_has_no_money_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    """
    - Login with test-logged-user
    - Mint an NFT (owner will be test-logged-user)
    - Login with test-buyer-user (only logged user can buy)
    - Buy the NFT minted for $200 (initial balance is $100)
    - Check that bought fails
    """

    logged_username: str = ""

    # First we mock the context so that then we can change the logged user
    def mocked_default_context() -> Any:
        context: Context = Context(username=logged_username, system_date=datetime.now(), user_ip="localhost")
        return context

    monkeypatch.setattr(nft_router.Context, "default_context", mocked_default_context)
    monkeypatch.setattr(nft_service.cf, "STATIC_PATH", RESOURCES_PATH)

    # Persist some users
    logged_user: User = utils.persist_new_user(username="test-logged-user", session=session)
    buyer_user: User = utils.persist_new_user(username="test-buyer-user", session=session)
    cocreator_user: User = utils.persist_new_user(username="test-cocreator-user", session=session)

    # Add balance for users
    utils.persist_new_user_balance(
        user_id=logged_user.id, initial_amount=0, final_amount=100, session=session  # type: ignore[arg-type]
    )
    utils.persist_new_user_balance(
        user_id=buyer_user.id, initial_amount=0, final_amount=100, session=session  # type: ignore[arg-type]
    )
    utils.persist_new_user_balance(
        user_id=cocreator_user.id, initial_amount=0, final_amount=100, session=session  # type: ignore[arg-type]
    )

    # Change the logged user
    logged_username = logged_user.username

    # Mint an NFT. This operation will persist a new NFT owned by test-logged-user
    with open(pkg_resources.resource_filename("tests.resources", "puppy.jpg"), "rb") as fo:
        files = {"file": fo}
        data = {"description": "dummy_description", "creators": [cocreator_user.username]}
        response = client.post(MINT_ENDPOINT, files=files, data=data)

    # Verify endpoint returns 200
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK

    nft_id = response_json["id"]
    # Verify it was correctly persisted in db
    assert session.exec(select(NFT).where(NFT.id == nft_id)).one()

    # Now we login with the buyer user
    logged_username = buyer_user.username

    # Buy the NFT (logged_user is the owner so it becames the seller)
    json_data = {"buyer": buyer_user.username, "seller": logged_user.username, "price": 200}
    response = client.post(f"{BUY_ENDPOINT}{nft_id}", json=json_data)

    response_json = response.json()
    # Verify endpoints returns 400
    assert response.status_code == 400
    assert response_json["detail"] == "Buyer cannot have negative balance"

    # Check NFT owner was not updated
    owner_id = session.exec(select(NFT.owner_id).where(NFT.id == nft_id)).one()
    assert owner_id != buyer_user.id

    # Check new transaction was not created
    trx_result = session.exec(select(Transaction).where(Transaction.nft_id == nft_id)).all()
    assert not trx_result

    # Check balances were not updated
    buyer_balance_res = session.exec(
        select(UserBalance)
        .where(UserBalance.user_id == buyer_user.id)
        .order_by(UserBalance.id.desc())  # type: ignore[union-attr]
    ).first()
    seller_balance_res = session.exec(
        select(UserBalance)
        .where(UserBalance.user_id == logged_user.id)
        .order_by(UserBalance.id.desc())  # type: ignore[union-attr]
    ).first()
    cocreator_balance_res = session.exec(
        select(UserBalance)
        .where(UserBalance.user_id == cocreator_user.id)
        .order_by(UserBalance.id.desc())  # type: ignore[union-attr]
    ).first()

    assert buyer_balance_res
    assert buyer_balance_res.initial_amount == 0
    assert buyer_balance_res.final_amount == 100

    assert seller_balance_res
    assert seller_balance_res.initial_amount == 0
    assert seller_balance_res.final_amount == 100

    assert cocreator_balance_res
    assert cocreator_balance_res.initial_amount == 0
    assert cocreator_balance_res.final_amount == 100


@pytest.mark.asyncio
async def test_buy_nft_when_simulating_other_user_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    """
    - Login with test-logged-user
    - Mint an NFT (owner will be test-logged-user)
    - Login with test-buyer-user (only logged user can buy)
    - Request buy endpoint sending buyer as another user
    - Check that bought fails
    """

    logged_username: str = ""

    # First we mock the context so that then we can change the logged user
    def mocked_default_context() -> Any:
        context: Context = Context(username=logged_username, system_date=datetime.now(), user_ip="localhost")
        return context

    monkeypatch.setattr(nft_router.Context, "default_context", mocked_default_context)
    monkeypatch.setattr(nft_service.cf, "STATIC_PATH", RESOURCES_PATH)

    # Persist some users
    logged_user: User = utils.persist_new_user(username="test-logged-user", session=session)
    buyer_user: User = utils.persist_new_user(username="test-buyer-user", session=session)
    seller_user: User = utils.persist_new_user(username="test-seller-user", session=session)
    cocreator_user: User = utils.persist_new_user(username="test-cocreator-user", session=session)

    # Add balance for users
    utils.persist_new_user_balance(
        user_id=logged_user.id, initial_amount=0, final_amount=100, session=session  # type: ignore[arg-type]
    )
    utils.persist_new_user_balance(
        user_id=buyer_user.id, initial_amount=0, final_amount=100, session=session  # type: ignore[arg-type]
    )
    utils.persist_new_user_balance(
        user_id=seller_user.id, initial_amount=0, final_amount=100, session=session  # type: ignore[arg-type]
    )
    utils.persist_new_user_balance(
        user_id=cocreator_user.id, initial_amount=0, final_amount=100, session=session  # type: ignore[arg-type]
    )

    # Change the logged user
    logged_username = logged_user.username

    # Mint an NFT. This operation will persist a new NFT owned by test-logged-user
    with open(pkg_resources.resource_filename("tests.resources", "puppy.jpg"), "rb") as fo:
        files = {"file": fo}
        data = {"description": "dummy_description", "creators": [cocreator_user.username]}
        response = client.post(MINT_ENDPOINT, files=files, data=data)

    # Verify endpoint returns 200
    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK

    nft_id = response_json["id"]
    # Verify it was correctly persisted in db
    assert session.exec(select(NFT).where(NFT.id == nft_id)).one()

    # Now we login with the buyer user
    logged_username = buyer_user.username

    # Buy the NFT with wrong buyer
    json_data = {"buyer": logged_user.username, "seller": seller_user.username, "price": 200}
    response = client.post(f"{BUY_ENDPOINT}{nft_id}", json=json_data)

    response_json = response.json()
    # Verify endpoints returns 400
    assert response.status_code == 400
    assert response_json["detail"] == "Either Buyer or Seller is invalid"

    # Check NFT owner was not updated
    owner_id = session.exec(select(NFT.owner_id).where(NFT.id == nft_id)).one()
    assert owner_id != buyer_user.id

    # Check new transaction was not created
    trx_result = session.exec(select(Transaction).where(Transaction.nft_id == nft_id)).all()
    assert not trx_result

    # Check balances were not updated
    buyer_balance_res = session.exec(
        select(UserBalance)
        .where(UserBalance.user_id == buyer_user.id)
        .order_by(UserBalance.id.desc())  # type: ignore[union-attr]
    ).first()
    seller_balance_res = session.exec(
        select(UserBalance)
        .where(UserBalance.user_id == seller_user.id)
        .order_by(UserBalance.id.desc())  # type: ignore[union-attr]
    ).first()
    cocreator_balance_res = session.exec(
        select(UserBalance)
        .where(UserBalance.user_id == cocreator_user.id)
        .order_by(UserBalance.id.desc())  # type: ignore[union-attr]
    ).first()

    assert buyer_balance_res
    assert buyer_balance_res.initial_amount == 0
    assert buyer_balance_res.final_amount == 100

    assert seller_balance_res
    assert seller_balance_res.initial_amount == 0
    assert seller_balance_res.final_amount == 100

    assert cocreator_balance_res
    assert cocreator_balance_res.initial_amount == 0
    assert cocreator_balance_res.final_amount == 100
