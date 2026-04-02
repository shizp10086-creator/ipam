# Database Migrations Guide

This document explains how to manage database migrations for the IPAM system using Alembic.

## Overview

The IPAM system uses Alembic for database schema migrations. Migrations are automatically applied on application startup, but you can also manage them manually for development purposes.

## Automatic Migration on Startup

When the application starts, it automatically:
1. Checks database connectivity
2. Runs all pending migrations to bring the schema up to date
3. Creates the default admin user if it doesn't exist

This is handled by the `app/utils/db_init.py` module and is called from `app/main.py` during application startup.

## Manual Migration Management

### Prerequisites

Make sure you have the required dependencies installed:
```bash
pip install -r requirements.txt
```

### Common Commands

#### Check Current Migration Status
```bash
cd backend
alembic current
```

#### View Migration History
```bash
alembic history --verbose
```

#### Apply All Pending Migrations
```bash
alembic upgrade head
```

#### Rollback One Migration
```bash
alembic downgrade -1
```

#### Rollback to Specific Revision
```bash
alembic downgrade <revision_id>
```

#### Create a New Migration (Auto-generate)
```bash
alembic revision --autogenerate -m "Description of changes"
```

#### Create a New Migration (Manual)
```bash
alembic revision -m "Description of changes"
```

## Migration Files

Migration files are stored in `backend/alembic/versions/`. Each migration file contains:
- `upgrade()`: Function to apply the migration
- `downgrade()`: Function to rollback the migration

### Initial Migration

The initial migration (`001_initial_schema.py`) creates all the base tables:
- `users` - User accounts and authentication
- `network_segments` - Network segment definitions
- `devices` - Device inventory
- `ip_addresses` - IP address allocations
- `operation_logs` - Audit logs
- `alerts` - System alerts
- `scan_history` - IP scan history

## Database Initialization Script

You can also run the database initialization script manually:

```bash
cd backend
python -m app.utils.db_init
```

This script will:
1. Check database connectivity
2. Run all pending migrations
3. Create the default admin user

## Default Admin User

On first startup, the system creates a default admin user with credentials from the environment variables:

- Username: `DEFAULT_ADMIN_USERNAME` (default: admin)
- Password: `DEFAULT_ADMIN_PASSWORD` (default: admin123)
- Email: `DEFAULT_ADMIN_EMAIL` (default: admin@ipam.local)
- Full Name: `DEFAULT_ADMIN_FULLNAME` (default: System Administrator)

**⚠️ IMPORTANT**: Change the default admin password immediately after first login!

## Configuration

Database connection settings are configured in `.env` file:

```env
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=ipam
MYSQL_PASSWORD=ipam_password
MYSQL_DATABASE=ipam_db
```

The Alembic configuration (`alembic.ini`) is automatically configured to use these settings through `alembic/env.py`.

## Troubleshooting

### Migration Fails with "Table already exists"

If you have an existing database with tables created by SQLAlchemy's `create_all()`, you need to:

1. Backup your data
2. Drop all tables
3. Run migrations from scratch

Or, stamp the database with the current migration:
```bash
alembic stamp head
```

### Cannot Connect to Database

Check that:
1. MySQL is running
2. Database credentials in `.env` are correct
3. Database exists (create it if needed: `CREATE DATABASE ipam_db;`)
4. User has proper permissions

### Migration History is Out of Sync

To reset the migration history:
```bash
# Backup your data first!
alembic downgrade base  # Rollback all migrations
alembic upgrade head    # Reapply all migrations
```

## Best Practices

1. **Always backup data** before running migrations in production
2. **Test migrations** in a development environment first
3. **Review auto-generated migrations** - they may need manual adjustments
4. **Never edit applied migrations** - create a new migration instead
5. **Keep migrations small** - one logical change per migration
6. **Write reversible migrations** - always implement `downgrade()`

## Docker Environment

When running in Docker, migrations are automatically applied on container startup. The application will wait for the database to be ready before applying migrations.

To manually run migrations in Docker:
```bash
docker-compose exec backend alembic upgrade head
```

To check migration status in Docker:
```bash
docker-compose exec backend alembic current
```

## Development Workflow

1. Make changes to models in `app/models/`
2. Generate migration: `alembic revision --autogenerate -m "Add new field"`
3. Review the generated migration file
4. Test the migration: `alembic upgrade head`
5. Test the rollback: `alembic downgrade -1`
6. Commit the migration file to version control

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FastAPI with Alembic](https://fastapi.tiangolo.com/tutorial/sql-databases/#alembic-note)
