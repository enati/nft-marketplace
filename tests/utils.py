from nft_service.src.models.auditable import AuditableModel
from nft_service.src.models.nft import NFT, NFTFile
from nft_service.src.models.balance import UserBalance
from nft_service.src.models.transaction import Transaction
from nft_service.src.models.user import User
from tests import utils
import base64
import secrets
from sqlmodel import Session
from datetime import datetime, date
from typing import List


async def image_to_base64(path: str) -> str:
    with open(path, "rb") as fo:
        base64_img = base64.b64encode(fo.read()).decode()
    return base64_img


def hash_filename(filename: str) -> str:
    filename, extension = filename.split(".")
    hashed_name = secrets.token_hex(10) + "." + extension
    return hashed_name


def fill_obj_with_audit_data(obj: AuditableModel) -> None:
    obj.created_at = datetime.today()
    obj.modified_at = datetime.today()
    obj.created_by = "default-user"
    obj.modified_by = "default-user"
    obj.version = 1


def persist_new_file(filename: str, session: Session) -> NFTFile:
    dummy_hashed_name = utils.hash_filename(filename)
    dummy_thumb_hashed_name = utils.hash_filename(f"thumb-{filename}")
    file_obj = NFTFile(filename=filename, hashed_name=dummy_hashed_name, thumbnail=dummy_thumb_hashed_name)

    session.add(file_obj)
    session.commit()

    return file_obj


def persist_new_user(username: str, session: Session) -> User:
    user_obj = User(date_=date.today(), username=username)
    utils.fill_obj_with_audit_data(user_obj)

    session.add(user_obj)
    session.commit()
    session.refresh(user_obj)

    return user_obj


def persist_new_user_balance(user_id: int, initial_amount: float, final_amount: float, session: Session) -> UserBalance:
    balance_obj = UserBalance(
        creation_date=datetime.now(), user_id=user_id, initial_amount=initial_amount, final_amount=final_amount
    )
    utils.fill_obj_with_audit_data(balance_obj)

    session.add(balance_obj)
    session.commit()
    session.refresh(balance_obj)

    return balance_obj


def persist_new_transaction(buyer_id: int, seller_id: int, nft_id: int, price: float, session: Session) -> Transaction:
    transaction_obj = Transaction(
        creation_date=datetime.now(), buyer_id=buyer_id, seller_id=seller_id, nft_id=nft_id, price=price
    )
    utils.fill_obj_with_audit_data(transaction_obj)

    session.add(transaction_obj)
    session.commit()
    session.refresh(transaction_obj)

    return transaction_obj


def _new_NFT(file_id: int, owner_id: int, session: Session, cocreators: List[User] = []) -> NFT:
    nft_obj = NFT(
        creation_date=datetime.now(),
        file_id=file_id,
        owner_id=owner_id,
        creators=cocreators,
        description="Some description",
    )
    utils.fill_obj_with_audit_data(nft_obj)
    session.add(nft_obj)
    session.commit()
    session.refresh(nft_obj)

    return nft_obj
