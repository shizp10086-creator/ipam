"""
Test script to verify Alembic migration setup

This script checks that all required files and configurations are in place.
It does NOT require database connectivity or installed dependencies.
"""
import os
from pathlib import Path


def check_file_exists(filepath, description):
    """Check if a file exists and print result"""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} NOT FOUND: {filepath}")
        return False


def check_directory_exists(dirpath, description):
    """Check if a directory exists and print result"""
    if os.path.isdir(dirpath):
        print(f"✓ {description}: {dirpath}")
        return True
    else:
        print(f"✗ {description} NOT FOUND: {dirpath}")
        return False


def main():
    """Main test function"""
    print("=" * 60)
    print("Alembic Migration Setup Verification")
    print("=" * 60)
    print()
    
    backend_dir = Path(__file__).parent
    all_checks_passed = True
    
    # Check Alembic configuration files
    print("1. Checking Alembic Configuration Files:")
    print("-" * 60)
    all_checks_passed &= check_file_exists(
        backend_dir / "alembic.ini",
        "Alembic configuration file"
    )
    all_checks_passed &= check_file_exists(
        backend_dir / "alembic" / "env.py",
        "Alembic environment file"
    )
    all_checks_passed &= check_file_exists(
        backend_dir / "alembic" / "script.py.mako",
        "Alembic script template"
    )
    all_checks_passed &= check_file_exists(
        backend_dir / "alembic" / "README",
        "Alembic README"
    )
    print()
    
    # Check migration scripts
    print("2. Checking Migration Scripts:")
    print("-" * 60)
    all_checks_passed &= check_directory_exists(
        backend_dir / "alembic" / "versions",
        "Migrations directory"
    )
    all_checks_passed &= check_file_exists(
        backend_dir / "alembic" / "versions" / "001_initial_schema.py",
        "Initial migration script"
    )
    print()
    
    # Check database initialization modules
    print("3. Checking Database Initialization Modules:")
    print("-" * 60)
    all_checks_passed &= check_file_exists(
        backend_dir / "app" / "utils" / "db_init.py",
        "Database initialization module"
    )
    all_checks_passed &= check_file_exists(
        backend_dir / "app" / "utils" / "init_db.py",
        "Legacy init_db module (for reference)"
    )
    print()
    
    # Check helper scripts
    print("4. Checking Helper Scripts:")
    print("-" * 60)
    all_checks_passed &= check_file_exists(
        backend_dir / "migrate.py",
        "Migration management script"
    )
    print()
    
    # Check documentation
    print("5. Checking Documentation:")
    print("-" * 60)
    all_checks_passed &= check_file_exists(
        backend_dir / "MIGRATIONS.md",
        "Migration usage guide"
    )
    all_checks_passed &= check_file_exists(
        backend_dir / "TASK_2.3_SUMMARY.md",
        "Task completion summary"
    )
    print()
    
    # Check main.py for lifespan integration
    print("6. Checking Application Integration:")
    print("-" * 60)
    main_py_path = backend_dir / "app" / "main.py"
    if check_file_exists(main_py_path, "Main application file"):
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'lifespan' in content:
                print("  ✓ Lifespan manager found in main.py")
            else:
                print("  ✗ Lifespan manager NOT found in main.py")
                all_checks_passed = False
            
            if 'initialize_database' in content:
                print("  ✓ Database initialization call found in main.py")
            else:
                print("  ✗ Database initialization call NOT found in main.py")
                all_checks_passed = False
    print()
    
    # Summary
    print("=" * 60)
    if all_checks_passed:
        print("✓ ALL CHECKS PASSED")
        print("Alembic migration setup is complete and ready to use!")
    else:
        print("✗ SOME CHECKS FAILED")
        print("Please review the errors above and fix missing files.")
    print("=" * 60)
    
    return 0 if all_checks_passed else 1


if __name__ == "__main__":
    exit(main())
