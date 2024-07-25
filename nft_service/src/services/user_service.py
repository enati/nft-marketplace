from nft_service.src.services.base_service import BaseService
from nft_service.src.models.user import User
from nft_service.src.schemas.user_schema import UserResponse
from nft_service.src.schemas.request_schema import SearchRequest
from nft_service.src.context import Context
from nft_service.src.db.repositories.user import UserRepository
from nft_service.src.exceptions import InternalError
from sqlmodel import Session
from typing import List


class UserService(BaseService):
    def __init__(self, session: Session, context: Context):
        super().__init__(session, context)
        self.user_repo = UserRepository(session, context)

    async def get_all(self, search_request: SearchRequest) -> List[UserResponse]:
        try:
            userList: List[User] = await self.user_repo.get_all(search_request.offset, search_request.limit)
            return [UserResponse(**u.dict()) for u in userList]
        except Exception as e:
            raise InternalError(detail="Error retrieving Users list", exception=str(e))

    async def fetch(self, user_id: int) -> UserResponse:
        user: User = await self.user_repo.get_by_id(user_id)
        return UserResponse(**user.dict())

    async def fetch_logged_user(self) -> UserResponse:
        user: User = await self.user_repo.get_by_username(self.context.username)
        return UserResponse(**user.dict())

    async def fetch_by_username(self, username: str) -> UserResponse:
        user: User = await self.user_repo.get_by_username(username)
        return UserResponse(**user.dict())
