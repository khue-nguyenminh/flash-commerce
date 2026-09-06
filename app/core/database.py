from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

database_url = URL.create(
    drivername = "mssql+pyodbc",
    username = settings.database_user,
    password = settings.mssql_sa_password,
    host = settings.database_host,
    port = settings.database_port,
    database = settings.database_name,
    query = {
        "driver": "ODBC Driver 18 for SQL Server",
        "Encrypt": "yes",
        "TrustServerCertificate": "yes",
        },
)

engine = create_engine(
    database_url,
    pool_pre_ping = True,
)

SessionLocal = sessionmaker(
    bind = engine,
    autocommit = False,
    autoflush = False,
)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()