from nft_service.src.models.auditable import AuditableModel
from nft_service.src.models.user import User
from sqlmodel import Field
from typing import Optional
from datetime import datetime
from sqlmodel import Relationship


class UserBalance(AuditableModel, table=True):
    __tablename__ = "user_balance"

    id: Optional[int] = Field(default=None, primary_key=True)
    creation_date: datetime = Field()
    user_id: int = Field(foreign_key="user.id")
    transaction_id: Optional[int] = Field(default=None, foreign_key="transaction.id")
    initial_amount: float = Field(ge=0)
    final_amount: float = Field(ge=0)

    # Relation fields
    user: User = Relationship(sa_relationship_kwargs=dict(foreign_keys="[UserBalance.user_id]"))  # type: ignore # noqa: