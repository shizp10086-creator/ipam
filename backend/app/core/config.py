"""
Application Configuration
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # Project Info
    PROJECT_NAME: str = "IPAM System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database Configuration
    MYSQL_HOST: str = "mysql"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "ipam"
    MYSQL_PASSWORD: str = "ipam_password"
    MYSQL_DATABASE: str = "ipam_db"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from components"""
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"  # development, production
    
    # Database Connection Pool Configuration
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # Default Admin User (created on first startup)
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    DEFAULT_ADMIN_EMAIL: str = "admin@ipam.local"
    DEFAULT_ADMIN_FULLNAME: str = "System Administrator"
    
    # Ping Configuration
    USE_PING_PROXY: bool = False
    PING_PROXY_URL: str = "http://localhost:8001"
    PING_SOURCE_IP: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
