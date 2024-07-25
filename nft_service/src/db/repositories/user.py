from nft_service.src.db.repositories.base import BaseRepository
from nft_service.src.models.user import User
from nft_service.src.exceptions import NotFound
from sqlalchemy.exc import NoResultFound
from sqlmodel import select
from typing import List


class UserRepository(BaseRepository):
    async def get_all(self, offset: int, limit: int) -> List[User]:
        return self.session.exec(select(User).offset(offset).limit(limit).order_by(User.date_.desc())).all()

    async def get_by_id(self, id: int) -> User:
        try:
            obj = self.session.exec(select(User).where(User.id == id)).one()
            return obj
        except NoResultFound as e:
            raise NotFound(
                details="Resource not found",
                extra={"model": "User", "field": "user_id", "value": id},
                exception=str(e),
            )

    async def get_by_username(self, username: str) -> User:
        try:
            obj = self.session.exec(select(User).where(User.username == username)).one()
            return obj
        except NoResultFound as e:
            raise NotFound(
                details="Resource not found",
                extra={"model": "User", "field": "username", "value": username},
                exception=str(e),
            )
