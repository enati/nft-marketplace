from nft_service.src.db.repositories.base import BaseRepository
from nft_service.src.models.nft import NFT
from nft_service.src.models.user import User
from nft_service.src.exceptions import NotFound, InternalError
from sqlmodel import select
from typing import List, Optional
from datetime import datetime
from sqlalchemy.exc import NoResultFound


class NFTRepository(BaseRepository):
    async def get_all(self, offset: int, limit: int) -> List[NFT]:
        sql_query = select(NFT).offset(offset).limit(limit).order_by(NFT.creation_date.desc())
        return self.session.exec(sql_query).all()

    async def get_by_id(self, id: int) -> NFT:
        try:
            sql_query = select(NFT).where(NFT.id == id)
            return self.session.exec(sql_query).one()
        except NoResultFound as e:
            raise NotFound(details=str(e), extra={"model": "NFT", "field": "id", "value": id})

    async def create(
        self, owner_id: int, description: str, creators: List[int], file_id: int, commit: bool, **kargs
    ) -> NFT:
        usersList: List[User] = []
        for user_id in creators:
            sql_query = select(User).where(User.id == user_id)
            user: User = self.session.exec(sql_query).one()
            usersList.append(user)

        nft_obj = NFT(
            owner_id=owner_id,
            description=description,
            file_id=file_id,
            creators=usersList,
            creation_date=datetime.now(),
        )

        self.add_auditable_fields(nft_obj)

        try:
            self.session.add(nft_obj)
            if commit:
                self.session.commit()
                self.session.refresh(nft_obj)
            else:
                self.session.flush()
        except Exception as e:
            raise InternalError(details=str(e))
        return nft_obj

    async def update(
        self,
        id: int,
        owner_id: int,
        description: str,
        creators: Optional[List[User]],
        file_id: int,
        created_at: datetime,
        created_by: str,
        creation_date: datetime,
        commit: bool = True,
        **kwargs
    ) -> NFT:
        sql_query = select(NFT).where(NFT.id == id)
        nft_obj = self.session.exec(sql_query).one()
        nft_obj.owner_id = owner_id
        nft_obj.description = description
        nft_obj.creators = creators
        nft_obj.file_id = file_id
        nft_obj.creation_date = creation_date
        nft_obj.created_at = created_at

        self.update_auditable_fields(nft_obj)

        for creator in creators:
            self.update_auditable_fields(creator)

        try:
            self.session.add(nft_obj)
            if commit:
                self.session.commit()
                self.session.refresh(nft_obj)
            else:
                self.session.flush()

        except Exception as e:
            raise InternalError(details="Error trying to update nft", exception=str(e))
        return nft_obj
