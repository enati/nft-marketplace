from nft_service.src.models.auditable import AuditableModel
from sqlmodel import Field, Relationship
from sqlalchemy import UniqueConstraint
from typing import Optional, List
from nft_service.src.models.nft import NFTCreatorRel, NFT
from datetime import date


class User(AuditableModel, table=True):
    __tablename__ = "user"
    __table_args__ = (UniqueConstraint("username"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    date_: date = Field()
    username: str = Field()
    # Field to access related nfts
    nfts: List["NFT"] = Relationship(back_populates="creators", link_model=NFTCreatorRel)


User.update_forward_refs(User=User)
