from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

quest_db = TinyDB("questions.json", storage=CachingMiddleware(JSONStorage))
questions_table = quest_db.table("questions")
QuestionQuery = Query()