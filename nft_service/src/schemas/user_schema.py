from nft_service.src import utils
from pydantic import BaseModel, Field
from datetime import date


class UserResponse(BaseModel):
    """User Response Schema"""

    id: int = Field()
    date_: date = Field()
    username: str = Field()

    class Config:
        json_encoders = {date: utils.format_date}
