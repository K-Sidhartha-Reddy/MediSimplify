from collections.abc import Generator
import certifi
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from app.core.config import get_settings

settings = get_settings()

client = MongoClient(settings.mongodb_url, tlsCAFile=certifi.where())
db = client[settings.mongodb_db_name]


def get_users_collection(database: Database | None = None) -> Collection:
    target = database or db
    return target["users"]


def get_reports_collection(database: Database | None = None) -> Collection:
    target = database or db
    return target["reports"]


def ensure_indexes() -> None:
    users = get_users_collection()
    reports = get_reports_collection()
    users.create_index([("email", ASCENDING)], unique=True)
    reports.create_index([("user_id", ASCENDING)])
    reports.create_index([("created_at", DESCENDING)])


def get_db() -> Generator[Database, None, None]:
    yield db
