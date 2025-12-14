from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
import json

class CustomJSONStorage(JSONStorage):
    def __init__(self, path, **kwargs):
        super().__init__(path, **kwargs)
    
    def write(self, data):
        # Use default=str so datetime -> ISO-like string automatically
        with open(self.path, 'w') as f:
            json.dump(data, f, default=str, ensure_ascii=False, indent=2)

quest_db = TinyDB("questions.json", storage=CachingMiddleware(CustomJSONStorage))
questions_table = quest_db.table("questions")
QuestionQuery = Query()