from fastapi import FastAPI, HTTPException
from schemas.question import QuestionCreate, QuestionBase, Question as QuestionSchema
from database.question import quest_db, questions_table, QuestionQuery
from typing import List
from datetime import datetime

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI(title="Quiz Service - Questions API")

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
    new_q = QuestionSchema(**q.dict())
    questions_table.insert(new_q.dict())
    return new_q

# TODO: Implement READ ALL endpoint
# GET /questions/
# - Retrieve all questions from questions_table
# - Return list of all questions
@app.get("/questions/", response_model=QuestionSchema)
def list_questions():
    q = questions_table.all()
    if not q:
        raise HTTPException(status_code=404, detail="There are no questions found")
    return q

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
    questions_table.update(updated.dict(), QuestionQuery.id == question_id)
    return updated

# TODO: Implement DELETE endpoint
# DELETE /questions/{question_id}
# - Check if question exists (return 404 if not found)
# - Remove question from questions_table
# - Return success message like {"detail": "Question deleted"}

# Flush database
@app.post("/flush")
def flush_db():
    quest_db.storage.close()  # Ensure all cached data is written
    return {"detail": "DB flushed"}

