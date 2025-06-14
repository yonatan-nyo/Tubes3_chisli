import mysql.connector
from mysql.connector import Error
from sqlalchemy import inspect, text
from .database import Base, engine, DATABASE_HOST, DATABASE_USER, DATABASE_PASSWORD, DATABASE_NAME


def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    try:
        # Connect without database to create it
        temp_connection = mysql.connector.connect(
            host=DATABASE_HOST,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD
        )
        cursor = temp_connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}")
        temp_connection.commit()
        cursor.close()
        temp_connection.close()
        print(f"Database '{DATABASE_NAME}' ensured to exist")
        return True
    except Error as e:
        print(f"Error creating database: {e}")
        return False


def auto_migrate_schema():
    """Automatically detect and migrate schema changes using SQLAlchemy"""
    try:
        # Import all models to ensure they're registered
        from . import applicant

        # Get database inspector
        inspector = inspect(engine)

        # Check if tables exist
        existing_tables = inspector.get_table_names()
        print(f"Existing tables: {existing_tables}")

        # Get model metadata
        model_tables = Base.metadata.tables.keys()
        print(f"Required tables: {list(model_tables)}")

        with engine.connect() as conn:
            # For each model table, check schema differences
            for table_name in model_tables:
                if table_name in existing_tables:
                    print(f"Checking schema for table '{table_name}'...")

                    # Get existing columns
                    existing_columns = {
                        col['name']: col for col in inspector.get_columns(table_name)}

                    # Get required columns from model
                    model_table = Base.metadata.tables[table_name]
                    required_columns = {
                        col.name: col for col in model_table.columns}

                    # Find missing columns
                    missing_columns = set(
                        required_columns.keys()) - set(existing_columns.keys())

                    if missing_columns:
                        print(
                            f"Adding missing columns to '{table_name}': {missing_columns}")

                        for col_name in missing_columns:
                            col = required_columns[col_name]

                            # Build column definition
                            col_type = col.type.compile(engine.dialect)
                            nullable = "" if col.nullable else " NOT NULL"
                            default = ""

                            if col.default is not None:
                                if hasattr(col.default, 'arg'):
                                    if callable(col.default.arg):
                                        default = " DEFAULT CURRENT_TIMESTAMP"
                                    else:
                                        default = f" DEFAULT '{col.default.arg}'"

                            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}{nullable}{default}"

                            try:
                                conn.execute(text(alter_sql))
                                print(f"  Added column: {col_name}")
                            except Exception as e:
                                print(
                                    f"  Failed to add column {col_name}: {e}")
                    else:
                        print(f"  Table '{table_name}' schema is up to date")
                else:
                    print(
                        f"Table '{table_name}' doesn't exist, will be created")

            # Commit changes
            conn.commit()

        # Create any missing tables
        print("Creating missing tables...")
        Base.metadata.create_all(bind=engine, checkfirst=True)

        print("Schema migration completed successfully")
        return True

    except Exception as e:
        print(f"Error during schema migration: {e}")
        return False


def init_db(force_recreate: bool = False):
    """Initialize database with automatic migration

    Args:
        force_recreate: If True, will drop all tables and recreate them (DELETES ALL DATA!)
                       Only use this for initial setup or when absolutely necessary.
    """
    try:
        # Create database if needed
        if not create_database_if_not_exists():
            raise Exception("Failed to create database")

        if force_recreate:
            print("⚠️  WARNING: Force recreating all tables - THIS WILL DELETE ALL DATA!")
            # Check if there's existing data to warn user
            has_data = check_existing_data()
            if has_data:
                print(
                    "⚠️  EXISTING DATA DETECTED! This operation will permanently delete all your data!")
                print(
                    "⚠️  Only proceed if you're sure you want to lose all existing data!")

            # Drop all tables and recreate
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            print("All tables recreated successfully")
        else:
            # Use automatic migration
            print("Running automatic schema migration...")
            if not auto_migrate_schema():
                print("❌ Schema migration failed!")
                print(
                    "💡 If you need a fresh database, manually run with force_recreate=True")
                print("💡 Otherwise, please check your database configuration and schema")
                raise Exception(
                    "Schema migration failed - please check database manually")
                # Don't automatically force recreate - this deletes all data!
                # If you really need to recreate, run with force_recreate=True manually

        print("Database initialization completed successfully")
        return True

    except Exception as e:
        print(f"Error initializing database: {e}")
        return False


def get_schema_info():
    """Get current database schema information for debugging"""
    try:
        inspector = inspect(engine)
        schema_info = {}

        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            schema_info[table_name] = {
                'columns': {col['name']: str(col['type']) for col in columns},
                'column_count': len(columns)
            }

        return schema_info

    except Exception as e:
        print(f"Error getting schema info: {e}")
        return {}


def check_existing_data():
    """Check if there's existing data in the database"""
    try:
        from . import applicant
        from .database import SessionLocal

        db = SessionLocal()
        try:
            profile_count = db.query(applicant.ApplicantProfile).count()
            detail_count = db.query(applicant.ApplicantDetail).count()

            if profile_count > 0 or detail_count > 0:
                print(
                    f"📊 Found existing data: {profile_count} applicant profiles, {detail_count} application details")
                return True
            else:
                print("📊 No existing data found in database")
                return False
        finally:
            db.close()

    except Exception as e:
        print(f"Could not check existing data: {e}")
        return False
