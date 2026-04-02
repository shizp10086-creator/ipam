"""
Database Connection and Session Management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=settings.DB_POOL_SIZE,  # Number of connections to maintain
    max_overflow=settings.DB_MAX_OVERFLOW,  # Maximum number of connections beyond pool_size
    pool_timeout=settings.DB_POOL_TIMEOUT,  # Timeout for getting connection from pool
    pool_recycle=settings.DB_POOL_RECYCLE,  # Recycle connections after this many seconds
    echo=False  # Set to True for SQL query logging in development
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session
    Yields a database session and ensures it's closed after use
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
