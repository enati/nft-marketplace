from nft_service.src.schemas.balance_schema import BalanceResponse
from nft_service.src.schemas.request_schema import SearchRequest
from nft_service.src.db.events import get_session
from nft_service.src.services.balance_service import BalanceService
from nft_service.src.context import Context
from nft_service.src.models.exception import InternalServerError
from typing import List
from fastapi import APIRouter, Depends

ENDPOINT: str = "/balance"
router = APIRouter()


@router.get("/", response_model=List[BalanceResponse], responses={"500": {"model": InternalServerError}})
async def get_history(search_request: SearchRequest = Depends(), db: get_session = Depends()) -> List[BalanceResponse]:
    context = Context.default_context
    response: List[BalanceResponse] = await BalanceService(db, context).get_all_history(search_request)
    return response


@router.get("/{user_id}", response_model=List[BalanceResponse], responses={"500": {"model": InternalServerError}})
async def get_user_history(
    user_id: int, search_request: SearchRequest = Depends(), db: get_session = Depends()
) -> List[BalanceResponse]:
    context = Context.default_context
    response: List[BalanceResponse] = await BalanceService(db, context).get_all_history_for_user(
        user_id, search_request
    )
    return response
