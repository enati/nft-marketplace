from sqlmodel import Session
from nft_service.src.context import Context
from nft_service.src.models.auditable import AuditableModel


class BaseRepository:
    def __init__(self, session: Session, context: Context) -> None:
        self._session = session
        self._context = context

    @property
    def session(self) -> Session:
        return self._session

    @property
    def context(self) -> Context:
        return self._context

    def add_auditable_fields(self, obj: AuditableModel) -> None:
        obj.created_at = self.context.system_date
        obj.modified_at = self.context.system_date
        obj.created_by = self.context.username
        obj.modified_by = self.context.username
        obj.version = 1

    def update_auditable_fields(self, obj: AuditableModel) -> None:
        obj.modified_at = self.context.system_date
        obj.modified_by = self.context.username
        obj.version += 1
