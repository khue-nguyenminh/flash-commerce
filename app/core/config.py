from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    mssql_sa_password: str
    database_host: str = "127.0.0.1"
    database_port: str = 1433
    database_name: str = "FlashCommercePro"
    database_user: str = "sa"
    
    model_config = SettingsConfigDict (
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra = "ignore",
    )

settings = Settings()