from nft_service.src.schemas.user_schema import UserResponse
from nft_service.src import utils
from pydantic import BaseModel, Field
from datetime import datetime


class TransactionRequest(BaseModel):
    """Transaction Request Schema"""

    buyer: str = Field(description="Username of the buyer")
    seller: str = Field(description="Username of the seller")
    price: float = Field(ge=0)


class TransactionResponse(BaseModel):
    """Transaction Response Schema"""

    id: int = Field()  # despues cambiar por ref number
    creation_date: datetime = Field()
    nft_id: int = Field()
    buyer: UserResponse = Field()
    seller: UserResponse = Field()
    price: float = Field()

    class Config:
        json_encoders = {datetime: utils.format_datetime}
