from datetime import datetime
from fastapi import Header


def format_datetime(dt: datetime) -> str:
    return dt.strftime("%d-%m-%Y %H:%M:%S")


def format_date(dt: datetime) -> str:
    return dt.strftime("%d-%m-%Y")


# Dont allow files greater than ~1.5MB
async def valid_content_length(content_length: int = Header(..., lt=1_500_000)) -> int:
    print(content_length)
    return content_length
