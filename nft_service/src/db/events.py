from typing import Any
from loguru import logger
from sqlmodel import Session, SQLModel, create_engine, text
from nft_service.src.config import DB_URI
from nft_service.src.db.constants import (
    COUNT_USER_QUERY,
    INSERT_USER_QUERY,
    COUNT_USER_BALANCE_QUERY,
    INSERT_USER_BALANCE_QUERY,
    INITIAL_USERS,
    INITIAL_BALANCES,
)
from sqlalchemy.exc import IntegrityError

engine = create_engine(DB_URI, echo=False)


def create_db_and_tables() -> None:
    logger.info("Connecting to database")
    SQLModel.metadata.create_all(bind=engine)
    setup_initial_data()


def get_session() -> Any:
    with Session(engine) as session:
        yield session


def setup_initial_data() -> None:
    with engine.connect() as conn:
        logger.info("Initialicing table users")
        result = conn.execute(text(COUNT_USER_QUERY))
        if result.rowcount > 0 and result.first()[0] > 0:
            logger.info("Users already initialized")
        else:
            for user_data in INITIAL_USERS:
                try:
                    conn.execute(text(INSERT_USER_QUERY), user_data)
                except IntegrityError:
                    logger.error("Error trying to insert user")
                    break
            conn.commit()

        logger.info("Initialicing table balances")
        result = conn.execute(text(COUNT_USER_BALANCE_QUERY))
        if result.rowcount > 0 and result.first()[0] > 0:
            logger.info("Balances already initialized")
        else:
            for balance_data in INITIAL_BALANCES:
                try:
                    conn.execute(text(INSERT_USER_BALANCE_QUERY), balance_data)
                except IntegrityError:
                    logger.error("Error trying to insert balance")
                    break
        conn.commit()
