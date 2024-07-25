from nft_service.src.schemas.balance_schema import BalanceResponse
from nft_service.src.schemas.request_schema import SearchRequest
from nft_service.src.services.base_service import BaseService
from nft_service.src.models.balance import UserBalance
from nft_service.src.exceptions import BadRequest
from nft_service.src.config import COCREATOR_FEE, OWNER_FEE
from nft_service.src.models.nft import NFT
from nft_service.src.models.transaction import Transaction
from nft_service.src.context import Context
from nft_service.src.db.repositories.balance import BalanceRepository
from nft_service.src.exceptions import InternalError
from sqlmodel import Session
from typing import List


class BalanceService(BaseService):
    def __init__(self, session: Session, context: Context):
        super().__init__(session, context)
        self.balance_repo = BalanceRepository(session, context)

    async def update_balance(self, transaction: Transaction, nft: NFT) -> None:
        try:
            # Update buyer balance
            await self._generate_balance_movement(
                transaction.id, transaction.buyer_id, transaction.price, is_buy=True, commit=False
            )

            # Update co-creators balance
            if nft.creators:
                fee = COCREATOR_FEE * transaction.price / len(nft.creators)
                for cocreator_obj in nft.creators:
                    await self._generate_balance_movement(
                        transaction.id, cocreator_obj.id, fee, is_buy=False, commit=False
                    )

            # Update sellers balance
            await self._generate_balance_movement(
                transaction.id, transaction.seller_id, transaction.price * OWNER_FEE, is_buy=False, commit=True
            )

        except Exception as e:
            self.db.rollback()
            raise e

    async def get_all_history(self, search_request: SearchRequest) -> List[BalanceResponse]:
        try:
            balance_rows = await self.balance_repo.get_all(search_request.offset, search_request.limit)
            return [BalanceResponse(**balance_row.dict(), user=balance_row.user) for balance_row in balance_rows]
        except Exception as e:
            raise InternalError(detail="Error retrieving historic balance", exception=str(e))

    async def get_all_history_for_user(self, user_id: int, search_request: SearchRequest) -> List[BalanceResponse]:
        try:
            balance_rows = await self.balance_repo.get_by_user_id(user_id, search_request.offset, search_request.limit)
            return [BalanceResponse(**balance_row.dict(), user=balance_row.user) for balance_row in balance_rows]
        except Exception as e:
            raise InternalError(detail="Error retrieving user historic balance", exception=str(e))

    async def _generate_balance_movement(
        self, transaction_id: int, user_id: int, amount_operated: float, is_buy: bool, commit: int
    ) -> UserBalance:
        user_balance_rows: List[UserBalance] = await self.balance_repo.get_by_user_id(user_id)

        last_balance: UserBalance = user_balance_rows[-1]

        amount_operated = -amount_operated if is_buy else amount_operated
        new_amount = last_balance.final_amount + amount_operated

        if new_amount < 0:
            raise BadRequest(details="Buyer cannot have negative balance")

        balance_obj = await self.balance_repo.create(
            user_id=user_id,
            transaction_id=transaction_id,
            initial_amount=last_balance.final_amount,
            final_amount=new_amount,
            commit=commit,
        )
        return balance_obj
