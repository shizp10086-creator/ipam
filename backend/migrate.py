#!/usr/bin/env python
"""
Database Migration Helper Script

This script provides a simple interface for running database migrations.
It can be used for development and testing purposes.

Usage:
    python migrate.py upgrade    # Apply all pending migrations
    python migrate.py downgrade  # Rollback one migration
    python migrate.py current    # Show current migration
    python migrate.py history    # Show migration history
    python migrate.py init       # Initialize database (run migrations + create admin)
"""
import sys
import logging
from pathlib import Path
from alembic.config import Config
from alembic import command

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.utils.db_init import initialize_database, check_database_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_alembic_config():
    """Get Alembic configuration"""
    backend_dir = Path(__file__).parent
    alembic_ini_path = backend_dir / "alembic.ini"
    
    if not alembic_ini_path.exists():
        logger.error(f"Alembic configuration file not found at {alembic_ini_path}")
        sys.exit(1)
    
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    
    return alembic_cfg


def upgrade():
    """Apply all pending migrations"""
    logger.info("Applying migrations...")
    alembic_cfg = get_alembic_config()
    command.upgrade(alembic_cfg, "head")
    logger.info("✓ Migrations applied successfully")


def downgrade():
    """Rollback one migration"""
    logger.info("Rolling back one migration...")
    alembic_cfg = get_alembic_config()
    command.downgrade(alembic_cfg, "-1")
    logger.info("✓ Migration rolled back successfully")


def current():
    """Show current migration"""
    logger.info("Current migration:")
    alembic_cfg = get_alembic_config()
    command.current(alembic_cfg)


def history():
    """Show migration history"""
    logger.info("Migration history:")
    alembic_cfg = get_alembic_config()
    command.history(alembic_cfg, verbose=True)


def init():
    """Initialize database (run migrations + create admin)"""
    logger.info("Initializing database...")
    
    # Check database connection
    if not check_database_connection():
        logger.error("✗ Cannot connect to database")
        sys.exit(1)
    
    # Initialize database
    if initialize_database():
        logger.info("✓ Database initialized successfully")
        logger.info(f"✓ Default admin user: {settings.DEFAULT_ADMIN_USERNAME}")
        logger.info(f"✓ Default admin password: {settings.DEFAULT_ADMIN_PASSWORD}")
        logger.warning("⚠ IMPORTANT: Please change the default admin password after first login!")
    else:
        logger.error("✗ Database initialization failed")
        sys.exit(1)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [upgrade|downgrade|current|history|init]")
        print()
        print("Commands:")
        print("  upgrade    - Apply all pending migrations")
        print("  downgrade  - Rollback one migration")
        print("  current    - Show current migration")
        print("  history    - Show migration history")
        print("  init       - Initialize database (run migrations + create admin)")
        sys.exit(1)
    
    command_name = sys.argv[1].lower()
    
    commands = {
        'upgrade': upgrade,
        'downgrade': downgrade,
        'current': current,
        'history': history,
        'init': init,
    }
    
    if command_name not in commands:
        print(f"Unknown command: {command_name}")
        print(f"Available commands: {', '.join(commands.keys())}")
        sys.exit(1)
    
    try:
        commands[command_name]()
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
