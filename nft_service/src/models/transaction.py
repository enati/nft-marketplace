from nft_service.src.models.auditable import AuditableModel
from nft_service.src.models.user import User
from sqlmodel import Field, Relationship
from typing import Optional
from datetime import datetime


class Transaction(AuditableModel, table=True):
    __tablename__ = "transaction"

    id: Optional[int] = Field(default=None, primary_key=True)
    creation_date: datetime = Field()
    nft_id: int = Field(foreign_key="nft.id")
    buyer_id: int = Field(foreign_key="user.id")
    seller_id: int = Field(foreign_key="user.id")
    price: float = Field(default=0)

    # Relation fields
    buyer: User = Relationship(sa_relationship_kwargs=dict(foreign_keys="[Transaction.buyer_id]"))  # type: ignore # noqa:
    seller: User = Relationship(sa_relationship_kwargs=dict(foreign_keys="[Transaction.seller_id]"))  # type: ignore # noqa:
