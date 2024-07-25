from nft_service.src.schemas.user_schema import UserResponse
from nft_service.src.schemas.request_schema import SearchRequest
from nft_service.src.db.events import get_session
from nft_service.src.services.user_service import UserService
from nft_service.src.context import Context
from nft_service.src.models.exception import NotFoundError, InternalServerError
from typing import List
from fastapi import APIRouter, Depends

ENDPOINT: str = "/user"
router = APIRouter()


@router.get("/", response_model=List[UserResponse], responses={"500": {"model": InternalServerError}})
async def get_all(search_request: SearchRequest = Depends(), db: get_session = Depends()) -> List[UserResponse]:
    context = Context.default_context
    response: List[UserResponse] = await UserService(db, context).get_all(search_request)
    return response


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    responses={"404": {"model": NotFoundError}, "500": {"model": InternalServerError}},
)
async def get_user(user_id: int, db: get_session = Depends()) -> UserResponse:
    context = Context.default_context
    response: UserResponse = await UserService(db, context).fetch(user_id)
    return response
