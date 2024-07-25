from nft_service.src.schemas.transaction_schema import TransactionResponse
from nft_service.src.schemas.request_schema import SearchRequest
from nft_service.src.db.events import get_session
from nft_service.src.services.transaction_service import TransactionService
from nft_service.src.context import Context
from nft_service.src.models.exception import InternalServerError
from typing import List
from fastapi import APIRouter, Depends

ENDPOINT: str = "/transaction"
router = APIRouter()


@router.get("/", response_model=List[TransactionResponse], responses={"500": {"model": InternalServerError}})
async def get_history(
    search_request: SearchRequest = Depends(), db: get_session = Depends()
) -> List[TransactionResponse]:
    context = Context.default_context
    response: List[TransactionResponse] = await TransactionService(db, context).get_all(search_request)
    return response
