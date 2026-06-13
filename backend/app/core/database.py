from collections.abc import Generator
import certifi
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from app.core.config import get_settings

settings = get_settings()

# Lazy initialization: MongoDB client is created on first use, not at import time
_client = None
_db = None


def _get_db_client():
    """Get or create MongoDB client (initialized on first call, not at import)."""
    global _client, _db
    if _client is None:
        _client = MongoClient(settings.mongodb_url, tlsCAFile=certifi.where())
        _db = _client[settings.mongodb_db_name]
    return _db


def get_users_collection(database: Database | None = None) -> Collection:
    target = database or _get_db_client()
    return target["users"]


def get_reports_collection(database: Database | None = None) -> Collection:
    target = database or _get_db_client()
    return target["reports"]


def ensure_indexes() -> None:
    users = get_users_collection()
    reports = get_reports_collection()
    users.create_index([("email", ASCENDING)], unique=True)
    reports.create_index([("user_id", ASCENDING)])
    reports.create_index([("created_at", DESCENDING)])


def get_db() -> Generator[Database, None, None]:
    yield _get_db_client()
