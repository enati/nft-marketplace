from starlette.config import Config
import os

config = Config(".env")

ROOT_PATH: str = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../..")
STATIC_PATH: str = ROOT_PATH + "/static/images/"

DB_HOST: str = config("DB_HOST", cast=str, default="localhost")
DB_USER = config("DB_USER", cast=str, default="root")
DB_PASSWORD = config("DB_PASSWORD", cast=str, default="root")
DB_NAME = config.get("DB_NAME", cast=str, default="mb_challenge")
DB_PORT = config.get("DB_PORT", cast=str, default="3306")

DB_URI: str = f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

COCREATOR_FEE: float = 0.20  # Mint operation fee equally divided between cocreators
OWNER_FEE: float = 0.80  # Mint operation fee that goes to the owner of the nft
