from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
import json

class CustomJSONStorage(JSONStorage):
    """
    Subclass JSONStorage and ensure the base initializer runs so attributes like
    `self.path` exist. Override write() to use json.dump with default=str so
    datetimes and other non-JSON-native objects are serialized safely.
    """
    def __init__(self, path: str) -> None:
        # Ensure JSONStorage sets up internal attributes (e.g. self.path)
        super().__init__(path)

    def write(self, data: Any) -> None:
        # Use the underlying path set by JSONStorage
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, default=str, ensure_ascii=False, indent=2)

quest_db = TinyDB("questions.json", storage=CachingMiddleware(CustomJSONStorage))
questions_table = quest_db.table("questions")
QuestionQuery = Query()