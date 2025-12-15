from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
import os

# need to ensure the data directory exists for docker volume mapping
os.makedirs("data", exist_ok=True)

quest_db = TinyDB("data/questions.json", storage=CachingMiddleware(JSONStorage))
questions_table = quest_db.table("questions")
QuestionQuery = Query()