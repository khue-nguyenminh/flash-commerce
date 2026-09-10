from fastapi import FastAPI, HTTPException 
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import engine
from app.routers.auth import router as auth_router
from app.routers.addresses import router as addresses_router
from app.routers.categories import router as categories_router
from app.routers.products import router as products_router
from app.routers.orders import router as orders_router
from app.routers.coupons import router as coupons_router
from app.routers.payments import router as payments_router

app =  FastAPI(title = "Flash Commerce API")
app.include_router(auth_router)
app.include_router(addresses_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(coupons_router)
app.include_router(payments_router)

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