from datetime import datetime
from sqlmodel import Field, SQLModel


class AuditableModel(SQLModel):
    created_at: datetime = Field()
    modified_at: datetime = Field()
    created_by: str = Field()
    modified_by: str = Field()
    version: int = Field(1)
