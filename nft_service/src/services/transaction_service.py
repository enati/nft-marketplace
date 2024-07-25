from nft_service.src.services.base_service import BaseService
from nft_service.src.schemas.user_schema import UserResponse
from nft_service.src.schemas.request_schema import SearchRequest
from nft_service.src.schemas.transaction_schema import TransactionRequest, TransactionResponse
from nft_service.src.models.user import User
from nft_service.src.models.transaction import Transaction
from nft_service.src.db.repositories.user import UserRepository
from nft_service.src.db.repositories.transaction import TransactionRepository
from nft_service.src.exceptions import InternalError
from nft_service.src.context import Context
from sqlmodel import Session
from typing import List


class TransactionService(BaseService):
    def __init__(self, session: Session, context: Context):
        super().__init__(session, context)
        self.trx_repo = TransactionRepository(session, context)
        self.user_repo = UserRepository(session, context)

    async def add(self, nft_id: int, request: TransactionRequest, commit: bool) -> Transaction:
        buyer_obj: User = await self.user_repo.get_by_username(request.buyer)
        seller_obj: User = await self.user_repo.get_by_username(request.seller)

        transaction_obj: Transaction = await self.trx_repo.create(
            buyer_id=buyer_obj.id, seller_id=seller_obj.id, price=request.price, nft_id=nft_id, commit=commit
        )

        return transaction_obj

    async def get_all(self, search_request: SearchRequest) -> List[TransactionResponse]:
        try:
            result: List[TransactionResponse] = []
            transaction_rows: List[Transaction] = await self.trx_repo.get_all(
                search_request.offset, search_request.limit
            )

            for transaction_row in transaction_rows:
                transaction_dict = dict(
                    id=transaction_row.id,
                    creation_date=transaction_row.creation_date,
                    nft_id=transaction_row.nft_id,
                    buyer=UserResponse(**transaction_row.buyer.dict()),
                    seller=UserResponse(**transaction_row.seller.dict()),
                    price=transaction_row.price,
                )
                result.append(TransactionResponse(**transaction_dict))

            return result
        except Exception as e:
            raise InternalError(detail="Error retrieving Transaction list", exception=str(e))
