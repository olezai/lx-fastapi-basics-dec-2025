from fastapi import FastAPI

app = FastAPI(title="My First API")

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/hello/{name}")
def greet_user(name: str):
    return {"message": f"Hello, {name}!"}

