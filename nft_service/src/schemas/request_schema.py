from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Schema to support pagination"""

    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=0, lte=50)

    def __init__(
        self,
        offset: int = 0,
        limit: int = 50
    ):
        super().__init__(offset=offset, limit=limit)
