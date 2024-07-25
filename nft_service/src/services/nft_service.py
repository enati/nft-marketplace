from nft_service.src.services.base_service import BaseService
from nft_service.src.services.balance_service import BalanceService
from nft_service.src.services.transaction_service import TransactionService
from nft_service.src.services.user_service import UserService
from nft_service.src.schemas.nft_schema import (
    NFTRequest,
    NFTResponse,
    NFTFetchResponse,
    NFTThumbnailResponse,
    NFTFileResponse,
)
from nft_service.src.schemas.user_schema import UserResponse
from nft_service.src.schemas.transaction_schema import (
    TransactionResponse,
    TransactionRequest,
)
from nft_service.src.schemas.request_schema import SearchRequest
from nft_service.src.models.nft import NFT, NFTFile
from nft_service.src.models.user import User
from nft_service.src.models.transaction import Transaction
from nft_service.src import config as cf
from nft_service.src.exceptions import InternalError, NotFound, BadRequest
from nft_service.src.db.repositories.nft import NFTRepository
from nft_service.src.context import Context
from fastapi import UploadFile
from typing import List
from sqlmodel import Session
import os
import secrets
import base64
from PIL import Image

from nft_service.src.handlers.handler import BaseHandler


class MintNFTSUseCase(BaseHandler):

    async def handle(self, req: NFTRequest) -> NFTFetchResponse:
        # Get logged user from context, this will be the owner of the NFT
        loggedUser: UserResponse = await self.user_service.fetch_logged_user()

        creatorList: List[UserResponse] = []
        for username in req.creators:
            user_response: UserResponse = await self.user_service.fetch_by_username(username)
            creatorList.append(user_response)

        try:
            file_obj: NFTFile = await self._process_file(file)
        except Exception as e:
            raise InternalError(details="Error trying to process the file", exception=e)

        try:
            # Create NFT with the file attached
            nft_obj: NFT = await self.nft_repo.create(
                owner_id=loggedUser.id,
                description=req.description,
                creators=[u.id for u in creatorList],
                file_id=file_obj.id,
                commit=True,
            )
            base64_img: str = await self._image_to_base64(f"{cf.STATIC_PATH}{file_obj.hashed_name}")
        except Exception as e:
            # If anywhing goes wrong, remove the persisted file.
            self.db.rollback()
            os.unlink(f"{cf.STATIC_PATH}{file_obj.hashed_name}")
            os.unlink(f"{cf.STATIC_PATH}{file_obj.thumbnail}")
            raise InternalError(details="Error trying to mint NFT", exception=e)

        return NFTFetchResponse(
            file=NFTFileResponse(filename=nft_obj.file.filename, file=base64_img),
            owner=UserResponse(**nft_obj.owner.dict()),
            creators=creatorList,
            **nft_obj.dict(),
        )


class NFTService(BaseService):
    def __init__(self, session: Session, context: Context):
        super().__init__(session, context)
        self.nft_repo = NFTRepository(session, context)
        self.user_service = UserService(session, self.context)
        self.trx_service = TransactionService(session, self.context)
        self.balance_service = BalanceService(session, self.context)

    async def _image_to_base64(self, path: str) -> str:
        with open(path, "rb") as fo:
            base64_img = base64.b64encode(fo.read()).decode()
        return base64_img

    async def _process_file(self, file: UploadFile) -> NFTFile:
        # First persist the file locally
        filename = file.filename
        # test.png >> ["test", "png]
        extension = filename.split(".")[1]

        # /static/images/3cda3e6df79c9ee99f41.png
        hashed_name = secrets.token_hex(10) + "." + extension
        file_path = f"{cf.STATIC_PATH}{hashed_name}"
        file_content = await file.read()

        with open(file_path, "wb") as fo:
            fo.write(file_content)

        # Save also a thumbnail to avoid passing the entire image from the get_all endpoint
        with Image.open(file_path) as img:
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            # /static/images/thumb-3cda3e6df79c9ee99f41.png
            thumb_hashed_name = "thumb-" + hashed_name
            thumb_path = f"{cf.STATIC_PATH}{thumb_hashed_name}"
            img.save(thumb_path)

        file_obj = NFTFile(filename=filename, hashed_name=hashed_name, thumbnail=thumb_hashed_name)
        self.db.add(file_obj)
        self.db.flush()
        return file_obj

    async def add(self, request: NFTRequest, file: UploadFile) -> NFTFetchResponse:
        # Get logged user from context, this will be the owner of the NFT
        loggedUser: UserResponse = await self.user_service.fetch_logged_user()

        creatorList: List[UserResponse] = []
        for username in request.creators:
            user_response: UserResponse = await self.user_service.fetch_by_username(username)
            creatorList.append(user_response)

        try:
            file_obj: NFTFile = await self._process_file(file)
        except Exception as e:
            raise InternalError(details="Error trying to process the file", exception=e)

        try:
            # Create NFT with the file attached
            nft_obj: NFT = await self.nft_repo.create(
                owner_id=loggedUser.id,
                description=request.description,
                creators=[u.id for u in creatorList],
                file_id=file_obj.id,
                commit=True,
            )
            base64_img: str = await self._image_to_base64(f"{cf.STATIC_PATH}{file_obj.hashed_name}")
        except Exception as e:
            # If anywhing goes wrong, remove the persisted file.
            self.db.rollback()
            os.unlink(f"{cf.STATIC_PATH}{file_obj.hashed_name}")
            os.unlink(f"{cf.STATIC_PATH}{file_obj.thumbnail}")
            raise InternalError(details="Error trying to mint NFT", exception=e)

        return NFTFetchResponse(
            file=NFTFileResponse(filename=nft_obj.file.filename, file=base64_img),
            owner=UserResponse(**nft_obj.owner.dict()),
            creators=creatorList,
            **nft_obj.dict(),
        )

    async def fetch(self, nft_id: int) -> NFTFetchResponse:
        nft_obj = await self.nft_repo.get_by_id(nft_id)
        base64_img: str = await self._image_to_base64(f"{cf.STATIC_PATH}{nft_obj.file.hashed_name}")

        return NFTFetchResponse(
            **nft_obj.dict(),
            file=NFTFileResponse(filename=nft_obj.file.filename, file=base64_img),
            owner=UserResponse(**nft_obj.owner.dict()),
        )

    async def get_all(self, search_request: SearchRequest) -> List[NFTResponse]:
        try:
            response: List[NFTResponse] = []
            nft_list: List[NFT] = await self.nft_repo.get_all(search_request.offset, search_request.limit)

            for nft_obj in nft_list:
                base64_img: str = await self._image_to_base64(f"{cf.STATIC_PATH}{nft_obj.file.thumbnail}")

                nft_resp = NFTResponse(
                    id=nft_obj.id,
                    creation_date=nft_obj.creation_date,
                    description=nft_obj.description,
                    creators=[UserResponse(**u.dict()) for u in nft_obj.creators],
                    owner=UserResponse(**nft_obj.owner.dict()),
                    file=NFTThumbnailResponse(filename=nft_obj.file.filename, thumbnail=base64_img),
                )
                response.append(nft_resp)
        except Exception as e:
            raise InternalError(detail="Error retrieving NFT list", exception=str(e))
        return response

    async def trade_nft(self, nft_id: int, request: TransactionRequest, is_buy: bool) -> TransactionResponse:
        nft_obj: NFT = await self.nft_repo.get_by_id(nft_id)

        buyer_obj: User = await self.user_service.fetch_by_username(request.buyer)
        seller_obj: User = await self.user_service.fetch_by_username(request.seller)

        if is_buy:
            # The logged user is the only who can buy NFTs.
            self._validate_buy_data(buyer_obj, seller_obj, nft_obj)
        else:
            # In case of a sell the seller must be the owner of the NFT and must match the logged user
            self._validate_seller(seller_obj, nft_obj)

        if buyer_obj.username == seller_obj.username:
            raise BadRequest(details="Buyer and Seller must be different users")
        try:
            nft_obj.owner_id = buyer_obj.id
            await self.nft_repo.update(**nft_obj.dict(), creators=nft_obj.creators, commit=False)

            transaction_obj: Transaction = await self.trx_service.add(nft_obj.id, request, commit=False)
            await self.balance_service.update_balance(transaction_obj, nft_obj)

            buyer_response = UserResponse(**transaction_obj.buyer.dict())
            seller_response = UserResponse(**transaction_obj.seller.dict())

            result = TransactionResponse(
                id=transaction_obj.id,
                creation_date=transaction_obj.creation_date,
                nft_id=nft_obj.id,
                buyer=buyer_response,
                seller=seller_response,
                price=transaction_obj.price,
            )
            self.db.commit()
        except (BadRequest, NotFound) as e:
            self.db.rollback()
            raise e
        except Exception as e:
            self.db.rollback()
            raise InternalError(details="Internal Server Error", exception=str(e))
        return result

    def _validate_buy_data(self, buyer: User, seller: User, nft: NFT) -> None:
        # Check if buyer matched logged user and seller matches nft owner
        if buyer.username != self.context.username or seller.id != nft.owner_id:
            raise BadRequest(details="Either Buyer or Seller is invalid")
        # Check if buyer already own the nft
        if buyer.id == nft.owner_id:
            raise BadRequest(details=f"User {buyer.username} cannot buy requested NFT")

    def _validate_seller(self, user: User, nft: NFT) -> None:
        # Check if seller matched logged user
        if user.username != self.context.username:
            raise BadRequest(details="Seller is invalid")
        # Validated that the seller owns the NFT
        if user.id != nft.owner_id:
            raise BadRequest(details=f"User {user.username} cannot sell requested NFT")
