from datetime import datetime
from typing import Any

DEFAULT_USER: str = "default-user"
DEFAULT_IP: str = "127.0.0.1"


class Context:
    def __init__(self, username: str, system_date: datetime, user_ip: str):
        self.username = username
        self.system_date = system_date
        self.user_ip = user_ip

    @classmethod
    def default_context(cls) -> Any:
        system_date = datetime.now()
        return cls(DEFAULT_USER, system_date, DEFAULT_IP)

    def impersonate(self, username: str) -> None:
        self.username = username
