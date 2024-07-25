from nft_service.src.schemas.user_schema import UserResponse
from pydantic import BaseModel, Field
from datetime import datetime
from nft_service.src import utils
from typing import Optional


class BalanceResponse(BaseModel):
    """Balance Response Schema"""

    creation_date: datetime = Field()
    user: UserResponse = Field()
    transaction_id: Optional[int] = Field(default=0, description="Id of the transaction asociated")
    initial_amount: float = Field(description="Balance before the transaction that originated this movement")
    final_amount: float = Field(description="Balance after the transaction that originated this movement")

    class Config:
        json_encoders = {datetime: utils.format_datetime}
