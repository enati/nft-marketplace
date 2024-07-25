from nft_service.src.models.auditable import AuditableModel
from nft_service.src.context import Context
from sqlmodel import Session


class BaseService:
    def __init__(self, db: Session, context: Context):
        self.db = db
        self.context = context

    def add_auditable_fields(self, obj: AuditableModel) -> None:
        obj.created_at = self.context.system_date
        obj.modified_at = self.context.system_date
        obj.created_by = self.context.username
        obj.modified_by = self.context.username
        obj.version = 1
