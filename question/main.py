from fastapi import FastAPI, HTTPException
from schemas.question import QuestionCreate, QuestionBase, Question as QuestionSchema
from database.question import quest_db, questions_table, QuestionQuery
from typing import List
from datetime import datetime
# from fastapi.encoders import jsonable_encoder

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI(title="Quiz Service - Questions API")

# TODO: Create root endpoint that returns welcome message
@app.get("/")
def read_root():
    return {"message": "Welcome to QuizApp!"}

# TODO: Create health check endpoint
@app.get("/health")
def health_check():
        return {"status": "healthy", "service": "question-service"}

# TODO: Create greeting endpoint that accepts name as path parameter
@app.get("/hello/{name}")
def greet_user(name: str):
    return {"message": f"Hello, {name}!"}

# TODO: Create search endpoint with query parameters (q: str, limit: int = 10)
@app.get("/search/")
def search_items(q: str, limit: int = 10):
    return {
        "query": q,
        "limit": limit,
        "results": f"Searching for '{q}' with limit {limit}"
    }

@app.on_event("shutdown")
def shutdown_db_client():
    print("Closing TinyDB connection...")
    quest_db.close()  # This flushes all cached data to disk
    print("TinyDB closed.")

# -----------------------------
# CRUD Endpoints
# -----------------------------

# Create question
@app.post("/questions/", response_model=QuestionSchema)
def create_question(q: QuestionCreate):
    # new_q = QuestionSchema(**q.model_dump())
    # questions_table.insert(jsonable_encoder(new_q))
    new_q = QuestionSchema(**q.dict())
    questions_table.insert(new_q.model_dump(mode="json"))
    print(f"Created question with ID: {new_q.id}")
    return new_q

# TODO: Implement READ ALL endpoint
# GET /questions/
# - Retrieve all questions from questions_table
# - Return list of all questions
@app.get("/questions/", response_model=List[QuestionSchema])
def list_questions():
    q = questions_table.all()
    return q or []

# Get question by ID
@app.get("/questions/{question_id}", response_model=QuestionSchema)
def get_question(question_id: str):
    q = questions_table.get(QuestionQuery.id == question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q

# Update question
@app.put("/questions/{question_id}", response_model=QuestionSchema)
def update_question(question_id: str, q_update: QuestionCreate):
    q = questions_table.get(QuestionQuery.id == question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    updated = QuestionSchema(
        **q_update.dict(),
        id=question_id,
        created_at=q["created_at"],
        updated_at=datetime.utcnow()
    )
    # questions_table.update(jsonable_encoder(updated), QuestionQuery.id == question_id)
    questions_table.update(updated.model_dump(mode="json"), QuestionQuery.id == question_id)
    return updated

# TODO: Implement DELETE endpoint
# DELETE /questions/{question_id}
# - Check if question exists (return 404 if not found)
# - Remove question from questions_table
# - Return success message like {"detail": "Question deleted"}
@app.delete("/questions/{question_id}", response_model=QuestionSchema)
def delete_question(question_id: str):
    q = questions_table.get(QuestionQuery.id == question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    questions_table.remove(QuestionQuery.id == question_id)
    return {"detail": "Question deleted"}

# Flush database
@app.post("/flush")
def flush_db():
    # Ensure all cached data is written
    # Using the TinyDB CachingMiddleware storage; close underlying storage to flush
    quest_db.close()
    return {"detail": "DB flushed"}

