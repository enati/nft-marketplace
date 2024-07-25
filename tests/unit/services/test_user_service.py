from nft_service.src.schemas.user_schema import UserResponse
from nft_service.src.services.user_service import UserService
from nft_service.src.schemas.request_schema import SearchRequest
from nft_service.src.models.user import User
from nft_service.src.exceptions import NotFound
import pytest
from sqlmodel import Session
from tests import utils
from nft_service.src.context import Context
from typing import List
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_get_all_ok(client: TestClient, session: Session) -> None:
    # First persist some users
    user_1: User = utils.persist_new_user(username="test-user-1", session=session)
    user_2: User = utils.persist_new_user(username="test-user-2", session=session)

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(user_1.username)
    assert context.username == "test-user-1"

    response: List[UserResponse] = await UserService(session, context).get_all(SearchRequest())
    assert len(response) == 2
    assert response[0].id == user_1.id
    assert response[1].id == user_2.id


@pytest.mark.asyncio
async def test_get_all_paginated_ok(client: TestClient, session: Session) -> None:
    # First persist some users
    user_1: User = utils.persist_new_user(username="test-user-1", session=session)
    utils.persist_new_user(username="test-user-2", session=session)

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(user_1.username)
    assert context.username == "test-user-1"

    response: List[UserResponse] = await UserService(session, context).get_all(SearchRequest(offset=0, limit=1))
    assert len(response) == 1


@pytest.mark.asyncio
async def test_fetch_ok(client: TestClient, session: Session) -> None:
    # First persist some users
    user_1: User = utils.persist_new_user(username="test-user-1", session=session)

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(user_1.username)
    assert context.username == "test-user-1"

    response: UserResponse = await UserService(session, context).fetch(user_1.id)  # type: ignore
    assert response.id == user_1.id


@pytest.mark.asyncio
async def test_fetch_404_err(client: TestClient, session: Session) -> None:
    fake_user_id = 99
    # First persist some users
    user_1: User = utils.persist_new_user(username="test-user-1", session=session)

    # Create context and simulate that one of the created users is logged in
    context = Context.default_context()
    context.impersonate(user_1.username)
    assert context.username == "test-user-1"

    with pytest.raises(NotFound):
        await UserService(session, context).fetch(fake_user_id)
