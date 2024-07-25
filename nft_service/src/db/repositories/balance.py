from nft_service.src.db.repositories.base import BaseRepository
from nft_service.src.models.balance import UserBalance
from nft_service.src.exceptions import NotFound, InternalError
from sqlalchemy.exc import NoResultFound
from sqlmodel import select
from typing import List
from datetime import datetime


class BalanceRepository(BaseRepository):
    async def get_all(self, offset: int, limit: int) -> List[UserBalance]:
        return self.session.exec(
            select(UserBalance).offset(offset).limit(limit).order_by(UserBalance.creation_date.desc())
        ).all()

    async def get_by_user_id(self, user_id: int, offset: int = 0, limit: int = 100) -> List[UserBalance]:
        try:
            obj = self.session.exec(
                select(UserBalance)
                .where(UserBalance.user_id == user_id)
                .offset(offset)
                .limit(limit)
                .order_by(UserBalance.creation_date.desc())
            ).all()
            return obj
        except NoResultFound as e:
            raise NotFound(
                details="Balance not found for user",
                extra={"model": "UserBalance", "field": "user_id", "value": user_id},
                exception=str(e),
            )

    async def create(
        self,
        user_id: int,
        transaction_id: int,
        initial_amount: float,
        final_amount: float,
        commit: bool = False,
        **kwargs
    ) -> UserBalance:
        balance_obj = UserBalance(
            creation_date=datetime.now(),
            user_id=user_id,
            transaction_id=transaction_id,
            initial_amount=initial_amount,
            final_amount=final_amount,
        )
        self.add_auditable_fields(balance_obj)

        try:
            self.session.add(balance_obj)
            if (commit):
                self.session.commit()
                self.session.refresh(balance_obj)
            else:
                self.session.flush()
        except Exception as e:
            raise InternalError(details="Error updating balance", exception=str(e))

        return balance_obj
