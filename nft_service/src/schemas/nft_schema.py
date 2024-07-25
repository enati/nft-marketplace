from nft_service.src import utils
from nft_service.src.schemas.user_schema import UserResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class NFTThumbnailResponse(BaseModel):
    """NFT File Thumbnail Response Schema"""

    filename: str = Field()
    thumbnail: str = Field(description="base64 representation of the file thumbnail")


class NFTFileResponse(BaseModel):
    """NFT File Response Schema"""

    filename: str = Field()
    file: str = Field(description="base64 representation of the file")


class NFTRequest(BaseModel):
    """NFT Request Schema"""

    description: str = Field(description="Some text describing the NFT")
    creators: Optional[List[str]] = Field(description="List of creators of the NFT")


class NFTResponse(BaseModel):
    """NFT Response Schema"""

    id: int = Field()
    creation_date: datetime = Field(format="mm-DD-yyyy hh:MM:ss")
    description: str = Field(description="Some text describing the NFT", max_length=500)
    owner: UserResponse = Field(decription="User who owns the NFT")
    creators: List[UserResponse] = Field(default=[], description="List of creators of the NFT")
    file: NFTThumbnailResponse = Field(description="NFT thumbnail file")

    class Config:
        json_encoders = {datetime: utils.format_datetime}


class NFTFetchResponse(BaseModel):
    """NFT Fetch Response Schema"""

    id: int = Field()
    creation_date: datetime = Field(format="mm-DD-yyyy hh:MM:ss")
    description: str = Field(description="Some text describing the NFT", max_length=500)
    owner: UserResponse = Field(decription="User who owns the NFT")
    creators: List[UserResponse] = Field(default=[], description="List of creators of the NFT")
    file: NFTFileResponse = Field(description="NFT file")

    class Config:
        json_encoders = {datetime: utils.format_datetime}
