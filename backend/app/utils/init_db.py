"""
Database Initialization Utility

This module provides functions to initialize the database schema
and create default data (like the default admin user).
"""
from sqlalchemy.orm import Session
from app.core.database import Base, engine
from app.models import User, NetworkSegment, IPAddress, Device, OperationLog, Alert, ScanHistory
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def create_tables():
    """
    Create all database tables based on the defined models.
    This should be called on first startup or for testing.
    """
    try:
        # Import all models to ensure they are registered
        from app.models import (
            User, NetworkSegment, IPAddress, Device,
            OperationLog, Alert, ScanHistory
        )

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def create_default_admin(db: Session) -> User:
    """
    Create the default admin user if it doesn't exist.

    Args:
        db: Database session

    Returns:
        User: The created or existing admin user
    """
    from app.core.security import get_password_hash

    # Check if admin user already exists
    admin = db.query(User).filter(User.username == settings.DEFAULT_ADMIN_USERNAME).first()

    if admin:
        logger.info(f"Admin user '{settings.DEFAULT_ADMIN_USERNAME}' already exists")
        return admin

    # Create admin user
    admin = User(
        username=settings.DEFAULT_ADMIN_USERNAME,
        hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
        email=settings.DEFAULT_ADMIN_EMAIL,
        full_name=settings.DEFAULT_ADMIN_FULLNAME,
        role="admin",
        is_active=True
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    logger.info(f"Default admin user created: {settings.DEFAULT_ADMIN_USERNAME}")
    return admin


def init_db(db: Session):
    """
    Initialize the database with tables and default data.

    Args:
        db: Database session
    """
    # Create tables
    create_tables()

    # Create default admin user
    create_default_admin(db)

    logger.info("Database initialization completed")


if __name__ == "__main__":
    # This allows running the script directly for testing
    from app.core.database import SessionLocal

    logging.basicConfig(level=logging.INFO)

    db = SessionLocal()
    try:
        init_db(db)
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        db.close()
