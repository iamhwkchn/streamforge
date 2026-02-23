from fastapi import FastAPI

app = FastAPI(title="StreamForge API")

@app.get("/")
def read_root():
    return {"message": "Welcome to StreamForge API"}

