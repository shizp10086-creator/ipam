"""
Database Initialization Script

This script handles database initialization on first startup:
1. Runs Alembic migrations to create/update database schema
2. Creates default admin user if it doesn't exist

This should be called when the application starts.
"""
import logging
import sys
import os
from pathlib import Path
from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models.user import User

logger = logging.getLogger(__name__)


def run_migrations():
    """
    Run database migrations / create tables if not exist.
    Uses SQLAlchemy directly to avoid Alembic hanging issues.
    """
    try:
        logger.info("Running database migrations...")

        # Import all models to register them with Base
        from app.models import User, NetworkSegment, IPAddress, Device, OperationLog, Alert, ScanHistory
        from app.core.database import Base, engine
        from sqlalchemy import text, inspect

        # Create all tables that don't exist yet (safe - won't drop existing tables)
        Base.metadata.create_all(bind=engine)

        # Handle column additions for existing tables (schema migrations)
        with engine.connect() as conn:
            inspector = inspect(engine)

            # Add 'company' column to network_segments if not exists
            existing_cols = [c['name'] for c in inspector.get_columns('network_segments')]
            if 'company' not in existing_cols:
                logger.info("Adding 'company' column to network_segments table...")
                conn.execute(text(
                    "ALTER TABLE network_segments ADD COLUMN company VARCHAR(100) NULL COMMENT '所属公司'"
                ))
                conn.commit()
                logger.info("Column 'company' added successfully")

        logger.info("Database migrations completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error running database migrations: {e}")
        logger.exception(e)
        return False


def create_default_admin(db: Session) -> bool:
    """
    Create the default admin user if it doesn't exist.

    Args:
        db: Database session

    Returns:
        bool: True if admin was created or already exists, False on error
    """
    try:
        # Check if admin user already exists
        admin = db.query(User).filter(User.username == settings.DEFAULT_ADMIN_USERNAME).first()

        if admin:
            logger.info(f"Default admin user '{settings.DEFAULT_ADMIN_USERNAME}' already exists")
            return True

        # Create admin user
        logger.info(f"Creating default admin user: {settings.DEFAULT_ADMIN_USERNAME}")

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

        logger.info(f"Default admin user created successfully: {settings.DEFAULT_ADMIN_USERNAME}")
        logger.info(f"Default admin password: {settings.DEFAULT_ADMIN_PASSWORD}")
        logger.warning("IMPORTANT: Please change the default admin password after first login!")

        return True

    except Exception as e:
        logger.error(f"Error creating default admin user: {e}")
        logger.exception(e)
        db.rollback()
        return False


def initialize_database():
    """
    Initialize the database on first startup.

    This function:
    1. Runs Alembic migrations to create/update schema
    2. Creates default admin user if needed

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    logger.info("Starting database initialization...")

    # Step 1: Run migrations
    if not run_migrations():
        logger.error("Database migration failed")
        return False

    # Step 2: Create default admin user
    db = SessionLocal()
    try:
        if not create_default_admin(db):
            logger.error("Failed to create default admin user")
            return False
    finally:
        db.close()

    logger.info("Database initialization completed successfully")
    return True


def check_database_connection():
    """
    Check if database connection is working.

    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        from sqlalchemy import text
        # Try to connect to the database
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Check database connection first
    if not check_database_connection():
        print("ERROR: Cannot connect to database. Please check your database configuration.")
        sys.exit(1)

    # Initialize database
    if initialize_database():
        print("✓ Database initialized successfully!")
        print(f"✓ Default admin user: {settings.DEFAULT_ADMIN_USERNAME}")
        print(f"✓ Default admin password: {settings.DEFAULT_ADMIN_PASSWORD}")
        print("⚠ IMPORTANT: Please change the default admin password after first login!")
    else:
        print("✗ Database initialization failed. Check logs for details.")
        sys.exit(1)
