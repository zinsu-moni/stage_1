from database import init_db, drop_db, engine
from sqlalchemy import text


def create_database():
    print("Creating database tables...")
    init_db()
    print("✓ Database tables created successfully!")


def reset_database():
    print("WARNING: This will delete all data!")
    response = input("Are you sure you want to reset the database? (yes/no): ")
    
    if response.lower() == "yes":
        print("Dropping existing tables...")
        drop_db()
        print("Creating new tables...")
        init_db()
        print("✓ Database reset successfully!")
    else:
        print("Database reset cancelled.")


def check_connection():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful!")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("String Analysis API - Database Setup")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python setup_db.py init    - Create database tables")
        print("  python setup_db.py reset   - Reset database (delete all data)")
        print("  python setup_db.py check   - Check database connection")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "init":
        create_database()
    elif command == "reset":
        reset_database()
    elif command == "check":
        check_connection()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)