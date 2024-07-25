from nft_service.src.schemas.nft_schema import NFTRequest
from nft_service.src.models.nft import NFTFile, NFT
from nft_service.src.models.user import User
from nft_service.src.models.balance import UserBalance
from nft_service.src.context import Context
from nft_service.src.services import nft_service
from nft_service.src.exceptions import BadRequest, InternalError, NotFound
from nft_service.src.schemas.transaction_schema import TransactionRequest
from nft_service.src.schemas.nft_schema import NFTFetchResponse
import tests.utils as utils
import pkg_resources
import pytest
from typing import Any
from fastapi.testclient import TestClient
import os
from fastapi import UploadFile
from sqlmodel import Session, select

RESOURCES_PATH: str = os.path.join(os.path.dirname(__file__), "../../resources/static/")


@pytest.mark.asyncio
async def test_mint_nft_persisted_ok(client: TestClient, session: Session, monkeypatch: Any) -> None:
    # First persist some user to acts as logged user
    user: User = utils.persist_new_user(username="test-user", session=session)

    #  Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(user.username)
    assert context.username == "test-user"

    filename: str = "puppy.jpg"
    monkeypatch.setattr(nft_service.cf, "STATIC_PATH", RESOURCES_PATH)

    with open(pkg_resources.resource_filename("tests.resources", filename), "rb") as fo:
        file = UploadFile(filename=filename, file=fo)
        request = dict(description="dummy_description", creators=[])
        nft_obj: NFTFetchResponse = await nft_service.NFTService(session, context).add(NFTRequest(**request), file=file)

        # Verify that the nft was correctly persisted in db
        query_nft = session.exec(select(NFT).where(NFT.id == nft_obj.id)).one()
        assert query_nft
        assert query_nft.description == "dummy_description"
        assert query_nft.owner_id == user.id


@pytest.mark.asyncio
async def test_mint_nft_save_file_locally_ok(client: TestClient, session: Session, monkeypatch: Any) -> None:
    # Persist one user in the db to be used as the owner of the nft
    owner_obj: User = utils.persist_new_user("test-owner-user", session)
    assert session.exec(select(User).where(User.username == "test-owner-user")).one()

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(owner_obj.username)
    assert context.username == "test-owner-user"

    filename: str = "puppy.jpg"
    monkeypatch.setattr(nft_service.cf, "STATIC_PATH", RESOURCES_PATH)
    with open(pkg_resources.resource_filename("tests.resources", filename), "rb") as fo:
        file = UploadFile(filename=filename, file=fo)
        request = dict(description="dummy_description", creators=[])
        await nft_service.NFTService(session, context).add(NFTRequest(**request), file=file)

    nft_file_obj: NFTFile = session.exec(select(NFTFile).where(NFTFile.filename == filename)).one()
    assert os.path.exists(RESOURCES_PATH + nft_file_obj.hashed_name)
    assert os.path.exists(RESOURCES_PATH + nft_file_obj.thumbnail)


@pytest.mark.asyncio
async def test_buy_nft_when_money_available_ok(client: TestClient, session: Session) -> None:
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
    await nft_service.NFTService(session, context).trade_nft(
        nft_id=nft_obj.id, request=transaction_req, is_buy=True  # type: ignore
    )


@pytest.mark.asyncio
async def test_mint_nft_fails_after_save_file_then_remove_it_ok(
    client: TestClient, session: Session, monkeypatch: Any
) -> None:
    # Persist one user in the db to be used as the owner of the nft
    owner_obj: User = utils.persist_new_user("test-owner-user", session)
    assert session.exec(select(User).where(User.username == "test-owner-user")).one()

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(owner_obj.username)
    assert context.username == "test-owner-user"

    monkeypatch.setattr(nft_service.cf, "STATIC_PATH", RESOURCES_PATH)

    def create(*args, **kwargs) -> Any:  # type: ignore
        raise Exception("Ooops!")

    monkeypatch.setattr(nft_service.NFTRepository, "create", create)

    filename: str = "puppy.jpg"
    with open(pkg_resources.resource_filename("tests.resources", filename), "rb") as fo:
        file = UploadFile(filename=filename, file=fo)
        request = dict(description="dummy_description", creators=[])

        with pytest.raises(InternalError):
            await nft_service.NFTService(session, context).add(NFTRequest(**request), file=file)

        nft_file_objs = session.exec(select(NFTFile).where(NFTFile.filename == filename)).all()
        assert not nft_file_objs
        assert len(os.listdir(RESOURCES_PATH)) == 0


@pytest.mark.asyncio
async def test_buy_nft_when_no_money_available_err(client: TestClient, session: Session) -> None:
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

    # Make the transaction price 101 when the buyer balance es 100.
    transaction_req = TransactionRequest(buyer=logged_user_obj.username, seller=owner_obj.username, price=101)

    with pytest.raises(BadRequest) as ex:
        await nft_service.NFTService(session, context).trade_nft(
            nft_id=nft_obj.id, request=transaction_req, is_buy=True  # type: ignore
        )
    assert "Buyer cannot have negative balance" in str(ex.value)


@pytest.mark.asyncio
async def test_buy_nft_twice_err(client: TestClient, session: Session) -> None:
    # Tests that a the buyer user cannot be the owner of the nft.

    # Persis new file in db
    file_obj: NFTFile = utils.persist_new_file("puppy.jpg", session)
    assert session.exec(select(NFTFile).where(NFTFile.filename == "puppy.jpg")).one()

    # Persist only one user due to we will be using same user as owner and logged one
    owner_obj: User = utils.persist_new_user("test-owner-user", session)
    assert session.exec(select(User).where(User.username == "test-owner-user")).one()

    # Add some initial balance to the user
    utils.persist_new_user_balance(owner_obj.id, initial_amount=0, final_amount=100, session=session)  # type: ignore
    assert session.exec(
        select(UserBalance).where(UserBalance.user_id == owner_obj.id).where(UserBalance.final_amount == 100)
    ).one()

    # Persist new NFT
    nft_obj = utils._new_NFT(file_id=file_obj.id, owner_id=owner_obj.id, session=session)  # type: ignore
    session.flush()
    assert session.exec(select(NFT).where(NFT.id == nft_obj.id)).one()

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(owner_obj.username)
    assert context.username == "test-owner-user"

    # Make the transaction price 101 when the buyer balance es 100.
    transaction_req = TransactionRequest(buyer=owner_obj.username, seller=owner_obj.username, price=100)

    with pytest.raises(BadRequest) as ex:
        await nft_service.NFTService(session, context).trade_nft(
            nft_id=nft_obj.id, request=transaction_req, is_buy=True  # type: ignore
        )
    assert f"User {owner_obj.username} cannot buy requested NFT" in str(ex.value)


@pytest.mark.asyncio
async def test_sell_nft_with_bad_user_err(client: TestClient, session: Session) -> None:
    # Try to sell an NFT logged as a user that doesnt owns it

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
    transaction_req = TransactionRequest(buyer=owner_obj.username, seller=logged_user_obj.username, price=100)
    with pytest.raises(BadRequest) as ex:
        await nft_service.NFTService(session, context).trade_nft(
            nft_id=nft_obj.id, request=transaction_req, is_buy=False  # type: ignore
        )
    assert f"User {logged_user_obj.username} cannot sell requested NFT" in str(ex.value)


@pytest.mark.asyncio
async def test_sell_nft_to_buyer_with_no_money_available_err(client: TestClient, session: Session) -> None:
    # Try to sell an NFT to a user that has no money to pay it

    # Persis new file in db
    file_obj: NFTFile = utils.persist_new_file("puppy.jpg", session)
    assert session.exec(select(NFTFile).where(NFTFile.filename == "puppy.jpg")).one()

    # Persist two users in db. One will be the owner of the NFT (and logged user), the other one will be the buyer one
    owner_obj: User = utils.persist_new_user("test-owner-user", session)
    assert session.exec(select(User).where(User.username == "test-owner-user")).one()

    buyer_obj: User = utils.persist_new_user("test-buyer-user", session)
    assert session.exec(select(User).where(User.username == "test-buyer-user")).one()

    # Add some initial balance to both users. In this case buyers balance will be 0.
    utils.persist_new_user_balance(owner_obj.id, initial_amount=0, final_amount=100, session=session)  # type: ignore
    assert session.exec(
        select(UserBalance).where(UserBalance.user_id == owner_obj.id).where(UserBalance.final_amount == 100)
    ).one()
    utils.persist_new_user_balance(buyer_obj.id, initial_amount=0, final_amount=0, session=session)  # type: ignore
    assert session.exec(
        select(UserBalance).where(UserBalance.user_id == buyer_obj.id).where(UserBalance.final_amount == 0)
    ).one()

    # Persist new NFT
    nft_obj = utils._new_NFT(file_id=file_obj.id, owner_id=owner_obj.id, session=session)  # type: ignore
    session.flush()
    assert session.exec(select(NFT).where(NFT.id == nft_obj.id)).one()

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(owner_obj.username)
    assert context.username == "test-owner-user"

    # Simulate request that will come from endpoint
    transaction_req = TransactionRequest(buyer=buyer_obj.username, seller=owner_obj.username, price=100)
    with pytest.raises(BadRequest) as ex:
        await nft_service.NFTService(session, context).trade_nft(
            nft_id=nft_obj.id, request=transaction_req, is_buy=False  # type: ignore
        )
    assert "Buyer cannot have negative balance" in str(ex.value)


@pytest.mark.asyncio
async def test_equal_seller_and_buyer_err(client: TestClient, session: Session) -> None:
    # Persis new file in db
    file_obj: NFTFile = utils.persist_new_file("puppy.jpg", session)
    assert session.exec(select(NFTFile).where(NFTFile.filename == "puppy.jpg")).one()

    # Persist one users in db. In this case we will use the same user as seller and buyer
    logged_user_obj: User = utils.persist_new_user("test-logged-user", session)
    assert session.exec(select(User).where(User.username == "test-logged-user")).one()

    # Add some initial balance to the user
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

    # Simulate request that will come from endpoint (same buyer and seller)
    transaction_req = TransactionRequest(buyer=logged_user_obj.username, seller=logged_user_obj.username, price=100)
    with pytest.raises(BadRequest) as ex:
        await nft_service.NFTService(session, context).trade_nft(
            nft_id=nft_obj.id, request=transaction_req, is_buy=False  # type: ignore
        )
    assert "Buyer and Seller must be different users" in str(ex.value)


@pytest.mark.asyncio
async def test_buy_nft_updates_owner_ok(client: TestClient, session: Session) -> None:
    # When some user buy an NFT the ownerships is updated to match the buyer

    # Persis new file in db
    file_obj: NFTFile = utils.persist_new_file("puppy.jpg", session)
    assert session.exec(select(NFTFile).where(NFTFile.filename == "puppy.jpg")).one()

    # Persist two users in db. One will be the owner of the NFT, the other one will be the logged one (the buyer)
    owner_obj: User = utils.persist_new_user("test-owner-user", session)
    assert session.exec(select(User).where(User.username == "test-owner-user")).one()

    buyer_obj: User = utils.persist_new_user("test-buyer-user", session)
    assert session.exec(select(User).where(User.username == "test-buyer-user")).one()

    # Add some initial balance to both users
    utils.persist_new_user_balance(owner_obj.id, initial_amount=0, final_amount=100, session=session)  # type: ignore
    assert session.exec(
        select(UserBalance).where(UserBalance.user_id == owner_obj.id).where(UserBalance.final_amount == 100)
    ).one()
    utils.persist_new_user_balance(buyer_obj.id, initial_amount=0, final_amount=100, session=session)  # type: ignore
    assert session.exec(
        select(UserBalance).where(UserBalance.user_id == buyer_obj.id).where(UserBalance.final_amount == 100)
    ).one()

    # Persist new NFT
    nft_obj = utils._new_NFT(file_id=file_obj.id, owner_id=owner_obj.id, session=session)  # type: ignore
    session.flush()
    assert session.exec(select(NFT).where(NFT.id == nft_obj.id)).one()

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(buyer_obj.username)
    assert context.username == "test-buyer-user"

    # Simulate request that will come from endpoint
    transaction_req = TransactionRequest(buyer=buyer_obj.username, seller=owner_obj.username, price=10)
    await nft_service.NFTService(session, context).trade_nft(
        nft_id=nft_obj.id, request=transaction_req, is_buy=True  # type: ignore
    )

    # Check that it no new nft was created
    nft_list = session.exec(select(NFT)).all()
    assert len(nft_list) == 1

    # Validate that the new owner is the buyer
    ntf_updated_obj = session.exec(select(NFT).where(NFT.id == nft_obj.id)).one()
    assert ntf_updated_obj.owner_id == buyer_obj.id


@pytest.mark.asyncio
async def test_sell_nft_updates_owner_ok(client: TestClient, session: Session) -> None:
    # When some user sells an NFT is no longer the owner

    # Persis new file in db
    file_obj: NFTFile = utils.persist_new_file("puppy.jpg", session)
    assert session.exec(select(NFTFile).where(NFTFile.filename == "puppy.jpg")).one()

    # Persist two users in db. One will be the owner of the NFT, the other one will be the logged one (the buyer)
    owner_obj: User = utils.persist_new_user("test-owner-user", session)
    assert session.exec(select(User).where(User.username == "test-owner-user")).one()

    buyer_obj: User = utils.persist_new_user("test-buyer-user", session)
    assert session.exec(select(User).where(User.username == "test-buyer-user")).one()

    # Add some initial balance to both users
    utils.persist_new_user_balance(owner_obj.id, initial_amount=0, final_amount=100, session=session)  # type: ignore
    assert session.exec(
        select(UserBalance).where(UserBalance.user_id == owner_obj.id).where(UserBalance.final_amount == 100)
    ).one()
    utils.persist_new_user_balance(buyer_obj.id, initial_amount=0, final_amount=100, session=session)  # type: ignore
    assert session.exec(
        select(UserBalance).where(UserBalance.user_id == buyer_obj.id).where(UserBalance.final_amount == 100)
    ).one()

    # Persist new NFT
    nft_obj = utils._new_NFT(file_id=file_obj.id, owner_id=owner_obj.id, session=session)  # type: ignore
    session.flush()
    assert session.exec(select(NFT).where(NFT.id == nft_obj.id)).one()

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(owner_obj.username)
    assert context.username == "test-owner-user"

    # Simulate request that will come from endpoint
    transaction_req = TransactionRequest(buyer=buyer_obj.username, seller=owner_obj.username, price=10)
    await nft_service.NFTService(session, context).trade_nft(
        nft_id=nft_obj.id, request=transaction_req, is_buy=False  # type: ignore
    )

    # Validate that the new owner is the buyer
    ntf_updated_obj = session.exec(select(NFT).where(NFT.id == nft_obj.id)).one()
    assert ntf_updated_obj.owner_id != owner_obj.id


@pytest.mark.asyncio
async def test_mint_nft_with_creators_ok(client: TestClient, session: Session, monkeypatch: Any) -> None:
    # First persist three users. One to act as logged user and two more to use as nft creators
    user: User = utils.persist_new_user(username="test-user", session=session)
    user_c1: User = utils.persist_new_user(username="test-creator-1", session=session)
    user_c2: User = utils.persist_new_user(username="test-creator-2", session=session)

    #  Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(user.username)
    assert context.username == "test-user"

    filename: str = "puppy.jpg"
    monkeypatch.setattr(nft_service.cf, "STATIC_PATH", RESOURCES_PATH)

    with open(pkg_resources.resource_filename("tests.resources", filename), "rb") as fo:
        file = UploadFile(filename=filename, file=fo)
        request = dict(description="dummy_description", creators=[user_c1.username, user_c2.username])
        nft_obj: NFTFetchResponse = await nft_service.NFTService(session, context).add(NFTRequest(**request), file=file)

        # Verify that the nft was correctly persisted in db
        query_nft = session.exec(select(NFT).where(NFT.id == nft_obj.id)).one()
        assert query_nft
        assert query_nft.description == "dummy_description"
        assert query_nft.owner_id == user.id
        assert len(query_nft.creators) == 2
        assert query_nft.creators[0].id == user_c1.id
        assert query_nft.creators[1].id == user_c2.id


@pytest.mark.asyncio
async def test_mint_nft_with_bad_username_creator_err(client: TestClient, session: Session, monkeypatch: Any) -> None:
    # First persist some user to acts as logged user
    user: User = utils.persist_new_user(username="test-user", session=session)

    #  Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(user.username)
    assert context.username == "test-user"

    filename: str = "puppy.jpg"
    monkeypatch.setattr(nft_service.cf, "STATIC_PATH", RESOURCES_PATH)

    with open(pkg_resources.resource_filename("tests.resources", filename), "rb") as fo:
        file = UploadFile(filename=filename, file=fo)
        request = dict(description="dummy_description", creators=["bad-username"])

        with pytest.raises(NotFound):
            await nft_service.NFTService(session, context).add(NFTRequest(**request), file=file)
