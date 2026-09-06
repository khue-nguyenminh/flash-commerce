from fastapi import FastAPI, HTTPException 
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import engine

app =  FastAPI(title = "Flash Commerce API")

@app.get("/")
def read_root():
    return{"message": "Flash Commerce API is running"}

@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
        }
    except SQLAlchemyError:
        raise HTTPException(
            status_code = 503,
            detail = "Database is unavailable",
        )