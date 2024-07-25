from nft_service.src.models.auditable import AuditableModel
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from datetime import datetime


class NFTCreatorRel(SQLModel, table=True):
    __tablename__ = "nft_creator_rel"

    nft_id: int = Field(foreign_key="nft.id", primary_key=True)
    creator_id: int = Field(foreign_key="user.id", primary_key=True)


class NFTFile(SQLModel, table=True):
    __tablename__ = "nft_file"

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field()
    hashed_name: str = Field()
    thumbnail: str = Field()


class NFT(AuditableModel, table=True):
    __tablename__ = "nft"

    id: Optional[int] = Field(default=None, primary_key=True)
    creation_date: datetime = Field()
    description: str = Field(max_length=500)
    file_id: int = Field(foreign_key="nft_file.id")
    owner_id: int = Field(foreign_key="user.id")

    # Relation fields
    owner: "User" = Relationship(sa_relationship_kwargs=dict(foreign_keys="[NFT.owner_id]"))  # type: ignore # noqa:
    file: NFTFile = Relationship(sa_relationship_kwargs=dict(foreign_keys="[NFT.file_id]"))
    creators: List["User"] = Relationship(back_populates="nfts", link_model=NFTCreatorRel)  # type: ignore # noqa:
