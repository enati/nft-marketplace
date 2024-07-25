from nft_service.src.routers import routers
from nft_service.src.main import app
from nft_service.src.db.events import get_session
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
import pytest
from fastapi.testclient import TestClient
from typing import Any
import os

DB_URI: str = "mysql://test:test@localhost:3306/testdb"
RESOURCES_PATH: str = os.path.join(os.path.dirname(__file__), "resources/static/")


@pytest.fixture(name="session")
def session_fixture() -> Any:
    engine = create_engine(DB_URI, poolclass=StaticPool)
    # engine.execute
    SQLModel.metadata.create_all(engine)

    # _setup_test_data(engine)
    routers._setup_routers(app)
    routers._setup_handlers(app)

    with Session(engine) as session:
        yield session

    _clear_static_folder()
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Any:
    def get_session_override() -> Session:
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


def _clear_static_folder() -> None:
    for filename in os.listdir(RESOURCES_PATH):
        file_path = os.path.join(RESOURCES_PATH, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))
