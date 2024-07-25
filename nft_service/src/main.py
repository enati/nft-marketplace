from nft_service.src.routers.routers import _setup_routers, _setup_handlers
from nft_service.src.db.events import create_db_and_tables
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

app = FastAPI(
    title="MB Challenge",
    version="1.0.0",
    description="",
    docs_url=None,
    redoc_url="/docs",
    openapi_url="/docs/openapi.json",
    default_response_class=ORJSONResponse,
)


@app.on_event("startup")
async def startup() -> None:
    create_db_and_tables()
    _setup_routers(app)
    _setup_handlers(app)
