"""Database initialization utilities."""
import os
from sqlalchemy import text
from database.session import engine, Base


def init_db():
    """Initialize database - create tables."""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


def drop_db():
    """Drop all tables - WARNING: Destructive operation."""
    print("⚠️  WARNING: This will drop all tables!")
    response = input("Type 'yes' to confirm: ").strip().lower()

    if response == "yes":
        print("Dropping database tables...")
        try:
            Base.metadata.drop_all(bind=engine)
            print("✅ All tables dropped!")
            return True
        except Exception as e:
            print(f"❌ Error dropping tables: {e}")
            return False
    else:
        print("Cancelled.")
        return False


def reset_db():
    """Reset database - drop and recreate all tables."""
    print("Resetting database...")
    if drop_db():
        return init_db()
    return False


def check_connection():
    """Check database connection."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nMake sure PostgreSQL is running and configured:")
        print("  DB_HOST:", os.getenv("DB_HOST", "localhost"))
        print("  DB_PORT:", os.getenv("DB_PORT", "5432"))
        print("  DB_NAME:", os.getenv("DB_NAME", "aurelius"))
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python init_db.py [command]")
        print("\nCommands:")
        print("  init    - Create tables")
        print("  drop    - Drop all tables")
        print("  reset   - Drop and recreate all tables")
        print("  check   - Check database connection")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "init":
        init_db()
    elif command == "drop":
        drop_db()
    elif command == "reset":
        reset_db()
    elif command == "check":
        check_connection()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
