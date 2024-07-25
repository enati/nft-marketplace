from nft_service.src.models.nft import NFTFile, NFT
from nft_service.src.models.user import User
from nft_service.src.models.balance import UserBalance
from nft_service.src.context import Context
from nft_service.src.services.nft_service import NFTService
from nft_service.src.services.balance_service import BalanceService
from nft_service.src.schemas.transaction_schema import TransactionRequest
from nft_service.src.schemas.balance_schema import BalanceResponse
from nft_service.src.schemas.request_schema import SearchRequest
import tests.utils as utils
import pytest
from fastapi.testclient import TestClient
from typing import List
from sqlmodel import Session, select


@pytest.mark.asyncio
async def test_owner_balance_affected_on_nft_sell_ok(client: TestClient, session: Session) -> None:
    """When the owner sells an NFT his balance has to be incremented with the 80% of the price
    In this case:
        owner balance = 100
        sell price = 10

        new owner balance = 108
    """
    # Persis new file in db
    file_obj: NFTFile = utils.persist_new_file("puppy.jpg", session)
    assert session.exec(select(NFTFile).where(NFTFile.filename == "puppy.jpg")).one()

    # Persist two users in db. One will be the owner of the NFT, the other one will be the logged one
    owner_obj: User = utils.persist_new_user("test-owner-user", session)
    assert session.exec(select(User).where(User.username == "test-owner-user")).one()

    logged_user_obj: User = utils.persist_new_user("test-logged-user", session)
    assert session.exec(select(User).where(User.username == "test-logged-user")).one()

    # Add some initial balance to both users
    utils.persist_new_user_balance(owner_obj.id, initial_amount=0, final_amount=100, session=session)  # type: ignore
    assert session.exec(
        select(UserBalance).where(UserBalance.user_id == owner_obj.id).where(UserBalance.final_amount == 100)
    ).one()
    utils.persist_new_user_balance(
        logged_user_obj.id, initial_amount=0, final_amount=100, session=session  # type: ignore
    )
    assert session.exec(
        select(UserBalance).where(UserBalance.user_id == logged_user_obj.id).where(UserBalance.final_amount == 100)
    ).one()

    # Persist new NFT
    nft_obj = utils._new_NFT(file_id=file_obj.id, owner_id=owner_obj.id, session=session)  # type: ignore
    session.flush()
    assert session.exec(select(NFT).where(NFT.id == nft_obj.id)).one()

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(logged_user_obj.username)
    assert context.username == "test-logged-user"

    # Simulate request that will come from endpoint
    transaction_req = TransactionRequest(buyer=logged_user_obj.username, seller=owner_obj.username, price=10)
    await NFTService(session, context).trade_nft(
        nft_id=nft_obj.id, request=transaction_req, is_buy=True  # type: ignore
    )

    # Check owners balance
    balance_obj = session.exec(
        select(UserBalance).where(UserBalance.user_id == owner_obj.id).order_by(UserBalance.id.desc())  # type: ignore
    ).first()
    assert balance_obj
    assert balance_obj.initial_amount == 100
    assert balance_obj.final_amount == 108


@pytest.mark.asyncio
async def test_buyer_balance_affected_on_nft_sell_ok(client: TestClient, session: Session) -> None:
    """When the owner sells an NFT the buyers balance has to be decreased with the price
    In this case:
        buyer balance = 100
        sell price = 10

        new buyer balance = 90
    """
    # Persis new file in db
    file_obj: NFTFile = utils.persist_new_file("puppy.jpg", session)
    assert session.exec(select(NFTFile).where(NFTFile.filename == "puppy.jpg")).one()

    # Persist two users in db. One will be the buyer of the NFT, the other one will be the logged one
    buyer_obj: User = utils.persist_new_user("test-buyer-user", session)
    assert session.exec(select(User).where(User.username == "test-buyer-user")).one()

    logged_user_obj: User = utils.persist_new_user("test-logged-user", session)
    assert session.exec(select(User).where(User.username == "test-logged-user")).one()

    # Add some initial balance to both users
    utils.persist_new_user_balance(buyer_obj.id, initial_amount=0, final_amount=100, session=session)  # type: ignore
    assert session.exec(
        select(UserBalance).where(UserBalance.user_id == buyer_obj.id).where(UserBalance.final_amount == 100)
    ).one()
    utils.persist_new_user_balance(
        logged_user_obj.id, initial_amount=0, final_amount=100, session=session  # type: ignore
    )
    assert session.exec(
        select(UserBalance).where(UserBalance.user_id == logged_user_obj.id).where(UserBalance.final_amount == 100)
    ).one()

    # Persist new NFT
    nft_obj = utils._new_NFT(file_id=file_obj.id, owner_id=logged_user_obj.id, session=session)  # type: ignore
    session.flush()
    assert session.exec(select(NFT).where(NFT.id == nft_obj.id)).one()

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(logged_user_obj.username)
    assert context.username == "test-logged-user"

    # Simulate request that will come from endpoint
    transaction_req = TransactionRequest(buyer=buyer_obj.username, seller=logged_user_obj.username, price=10)
    await NFTService(session, context).trade_nft(
        nft_id=nft_obj.id, request=transaction_req, is_buy=False  # type: ignore
    )

    # Check owners balance
    balance_obj = session.exec(
        select(UserBalance).where(UserBalance.user_id == buyer_obj.id).order_by(UserBalance.id.desc())  # type: ignore
    ).first()
    assert balance_obj
    assert balance_obj.initial_amount == 100
    assert balance_obj.final_amount == 90


@pytest.mark.asyncio
async def test_cocreators_balances_affected_on_nft_sell_ok(client: TestClient, session: Session) -> None:
    """When the owner sells an NFT the buyers balance has to be increased
        with the 20% of the price divided between all cocreators
    In this case:
        cocreator_1 balance = 100
        cocreator_2 balance = 50
        sell price = 10

        new cocreator_1 balance = 101
        new cocreator_2 balance = 51
    """
    # Persis new file in db
    file_obj: NFTFile = utils.persist_new_file("puppy.jpg", session)
    assert session.exec(select(NFTFile).where(NFTFile.filename == "puppy.jpg")).one()

    # Persist four users in db. Buyer, seller and two cocreators
    buyer_obj: User = utils.persist_new_user("test-buyer-user", session)
    assert session.exec(select(User).where(User.username == "test-buyer-user")).one()

    logged_user_obj: User = utils.persist_new_user("test-logged-user", session)
    assert session.exec(select(User).where(User.username == "test-logged-user")).one()

    cocreator_1: User = utils.persist_new_user("test-cocreator-1-user", session)
    assert session.exec(select(User).where(User.username == "test-cocreator-1-user")).one()

    cocreator_2: User = utils.persist_new_user("test-cocreator-2-user", session)
    assert session.exec(select(User).where(User.username == "test-cocreator-2-user")).one()

    # Add some initial balance to all users
    utils.persist_new_user_balance(buyer_obj.id, initial_amount=0, final_amount=100, session=session)  # type: ignore
    assert session.exec(
        select(UserBalance).where(UserBalance.user_id == buyer_obj.id).where(UserBalance.final_amount == 100)
    ).one()
    utils.persist_new_user_balance(
        logged_user_obj.id, initial_amount=0, final_amount=100, session=session  # type: ignore
    )
    assert session.exec(
        select(UserBalance).where(UserBalance.user_id == logged_user_obj.id).where(UserBalance.final_amount == 100)
    ).one()
    utils.persist_new_user_balance(cocreator_1.id, initial_amount=0, final_amount=100, session=session)  # type: ignore
    assert session.exec(
        select(UserBalance).where(UserBalance.user_id == cocreator_1.id).where(UserBalance.final_amount == 100)
    ).one()
    utils.persist_new_user_balance(cocreator_2.id, initial_amount=0, final_amount=50, session=session)  # type: ignore
    assert session.exec(
        select(UserBalance).where(UserBalance.user_id == cocreator_2.id).where(UserBalance.final_amount == 50)
    ).one()

    # Persist new NFT
    cocreatorsList: List[User] = []
    cocreatorsList.append(cocreator_1)
    cocreatorsList.append(cocreator_2)
    nft_obj = utils._new_NFT(
        file_id=file_obj.id, owner_id=logged_user_obj.id, cocreators=cocreatorsList, session=session  # type: ignore
    )
    session.flush()
    assert session.exec(select(NFT).where(NFT.id == nft_obj.id)).one()

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(logged_user_obj.username)
    assert context.username == "test-logged-user"

    # Simulate request that will come from endpoint
    transaction_req = TransactionRequest(buyer=buyer_obj.username, seller=logged_user_obj.username, price=10)
    await NFTService(session, context).trade_nft(
        nft_id=nft_obj.id, request=transaction_req, is_buy=False  # type: ignore
    )

    # Check cocreators balance
    balance_obj_co_1 = session.exec(
        select(UserBalance).where(UserBalance.user_id == cocreator_1.id).order_by(UserBalance.id.desc())  # type: ignore
    ).first()
    assert balance_obj_co_1
    assert balance_obj_co_1.initial_amount == 100
    assert balance_obj_co_1.final_amount == 101

    balance_obj_co_2 = session.exec(
        select(UserBalance).where(UserBalance.user_id == cocreator_2.id).order_by(UserBalance.id.desc())  # type: ignore
    ).first()
    assert balance_obj_co_2
    assert balance_obj_co_2.initial_amount == 50
    assert balance_obj_co_2.final_amount == 51


@pytest.mark.asyncio
async def test_get_all_ok(client: TestClient, session: Session) -> None:
    # First persist some users
    user_1: User = utils.persist_new_user(username="test-user-1", session=session)
    user_2: User = utils.persist_new_user(username="test-user-2", session=session)

    # Add some initial balance
    utils.persist_new_user_balance(user_1.id, initial_amount=0, final_amount=100, session=session)  # type: ignore
    utils.persist_new_user_balance(user_1.id, initial_amount=100, final_amount=140, session=session)  # type: ignore
    utils.persist_new_user_balance(user_2.id, initial_amount=140, final_amount=200, session=session)  # type: ignore

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(user_1.username)
    assert context.username == "test-user-1"

    response: List[BalanceResponse] = await BalanceService(session, context).get_all_history(SearchRequest())
    assert len(response) == 3


@pytest.mark.asyncio
async def test_get_all_paginated_ok(client: TestClient, session: Session) -> None:
    # First persist some users
    user_1: User = utils.persist_new_user(username="test-user-1", session=session)
    user_2: User = utils.persist_new_user(username="test-user-2", session=session)

    # Add some initial balance
    utils.persist_new_user_balance(user_1.id, initial_amount=0, final_amount=100, session=session)  # type: ignore
    utils.persist_new_user_balance(user_1.id, initial_amount=100, final_amount=140, session=session)  # type: ignore
    utils.persist_new_user_balance(user_2.id, initial_amount=140, final_amount=200, session=session)  # type: ignore

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(user_1.username)
    assert context.username == "test-user-1"

    response: List[BalanceResponse] = await BalanceService(session, context).get_all_history(
        SearchRequest(offset=0, limit=1)
    )
    assert len(response) == 1


@pytest.mark.asyncio
async def test_get_all_for_user_ok(client: TestClient, session: Session) -> None:
    # First persist some users
    user_1: User = utils.persist_new_user(username="test-user-1", session=session)
    user_2: User = utils.persist_new_user(username="test-user-2", session=session)

    # Add some initial balance
    utils.persist_new_user_balance(user_1.id, initial_amount=0, final_amount=100, session=session)  # type: ignore
    utils.persist_new_user_balance(user_1.id, initial_amount=100, final_amount=140, session=session)  # type: ignore
    utils.persist_new_user_balance(user_2.id, initial_amount=140, final_amount=200, session=session)  # type: ignore

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(user_1.username)
    assert context.username == "test-user-1"

    response: List[BalanceResponse] = await BalanceService(session, context).get_all_history_for_user(
        user_1.id, SearchRequest()  # type: ignore
    )
    assert len(response) == 2  # Note that the las balance added is for user_2


@pytest.mark.asyncio
async def test_get_all_for_user_paginated_ok(client: TestClient, session: Session) -> None:
    # First persist some users
    user_1: User = utils.persist_new_user(username="test-user-1", session=session)
    user_2: User = utils.persist_new_user(username="test-user-2", session=session)

    # Add some initial balance
    utils.persist_new_user_balance(user_1.id, initial_amount=0, final_amount=100, session=session)  # type: ignore
    utils.persist_new_user_balance(user_1.id, initial_amount=100, final_amount=140, session=session)  # type: ignore
    utils.persist_new_user_balance(user_2.id, initial_amount=140, final_amount=200, session=session)  # type: ignore

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(user_1.username)
    assert context.username == "test-user-1"

    response: List[BalanceResponse] = await BalanceService(session, context).get_all_history_for_user(
        user_1.id, SearchRequest(offset=1, limit=50)  # type: ignore
    )
    assert len(response) == 1  # Note that the las balance added is for user_2
