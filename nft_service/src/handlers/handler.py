from abc import ABC, abstractmethod
from nft_service.src.schemas.base_schema import BaseRequest

class BaseHandler(ABC):

    @abstractmethod
    async def handle(self, req: BaseRequest):
        pass