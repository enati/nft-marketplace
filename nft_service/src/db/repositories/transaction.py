from nft_service.src.db.repositories.base import BaseRepository
from nft_service.src.models.transaction import Transaction
from nft_service.src.exceptions import InternalError
from sqlmodel import select
from typing import List
from datetime import datetime


class TransactionRepository(BaseRepository):
    async def get_all(self, offset: int, limit: int) -> List[Transaction]:
        return self.session.exec(
            select(Transaction).offset(offset).limit(limit).order_by(Transaction.creation_date.desc())
        ).all()

    async def create(
        self, nft_id: int, buyer_id: int, seller_id: int, price: float, commit: bool = False, **kwargs
    ) -> Transaction:
        transaction_obj = Transaction(
            buyer_id=buyer_id, seller_id=seller_id, price=price, nft_id=nft_id, creation_date=datetime.now()
        )
        self.add_auditable_fields(transaction_obj)

        try:
            self.session.add(transaction_obj)
            if commit:
                self.session.commit()
                self.session.refresh(transaction_obj)
            else:
                self.session.flush()
        except Exception as e:
            raise InternalError(details=str(e))

        return transaction_obj
