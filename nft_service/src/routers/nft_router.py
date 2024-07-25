from nft_service.src.schemas.nft_schema import NFTRequest, NFTResponse, NFTFetchResponse
from nft_service.src.schemas.transaction_schema import TransactionRequest, TransactionResponse
from nft_service.src.schemas.request_schema import SearchRequest
from nft_service.src.db.events import get_session
from nft_service.src.services.nft_service import NFTService
from nft_service.src.context import Context
from nft_service.src.models.exception import BadRequestError, InternalServerError, NotFoundError
from nft_service.src.exceptions import BadRequest
from nft_service.src.utils import valid_content_length
from typing import List
from fastapi import APIRouter, Depends, UploadFile, Form

ENDPOINT: str = "/nft"
router = APIRouter()


@router.get("/", response_model=List[NFTResponse], responses={"500": {"model": InternalServerError}})
async def get_all(search_request: SearchRequest = Depends(), db: get_session = Depends()) -> List[NFTResponse]:
    context = Context.default_context
    response: List[NFTResponse] = await NFTService(db, context).get_all(search_request)
    return response


@router.get(
    "/{nft_id}",
    response_model=NFTFetchResponse,
    responses={"404": {"model": NotFoundError}, "500": {"model": InternalServerError}},
)
async def fetch(nft_id: int, db: get_session = Depends()) -> NFTFetchResponse:
    context = Context.default_context
    response: NFTFetchResponse = await NFTService(db, context).fetch(nft_id)
    return response


@router.post(
    "/mint/",
    response_model=NFTFetchResponse,
    responses={400: {"model": BadRequestError}, 500: {"model": InternalServerError}},
)
async def mint_nft(
    file: UploadFile,
    file_size: int = Depends(valid_content_length),
    description: str = Form(),
    creators: List[str] = Form(default=[], description="List of co-creators username"),
    db: get_session = Depends(),
) -> NFTFetchResponse:
    context = Context.default_context()

    # Only accept jpeg and png images for simplicity
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise BadRequest(details="File extension not allowed")

    request = NFTRequest(description=description, creators=creators)
    response = await NFTService(db, context).add(request, file)
    return response


@router.post(
    "/buy/{nft_id}",
    response_model=TransactionResponse,
    responses={400: {"model": BadRequestError}, 404: {"model": NotFoundError}, 500: {"model": InternalServerError}},
)
async def buy_nft(nft_id: int, request: TransactionRequest, db: get_session = Depends()) -> TransactionResponse:
    context = Context.default_context()
    response = await NFTService(db, context).trade_nft(nft_id, request, is_buy=True)
    return response


@router.post(
    "/sell/{nft_id}",
    response_model=TransactionResponse,
    responses={400: {"model": BadRequestError}, 404: {"model": NotFoundError}, 500: {"model": InternalServerError}},
)
async def sell_nft(nft_id: int, request: TransactionRequest, db: get_session = Depends()) -> TransactionResponse:
    context = Context.default_context()
    response = await NFTService(db, context).trade_nft(nft_id, request, is_buy=False)
    return response
