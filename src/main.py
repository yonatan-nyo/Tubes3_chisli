from dotenv import load_dotenv
# Load environment variables from .env file FIRST - DO NOT MOVE THIS
load_dotenv()

from database.models.database import DATABASE_URL
import flet as ft
from database import init_db, SessionLocal, Applicant
from database.models.init_database import get_schema_info
from core.cv_processor import CVProcessor
from core.search_engine import SearchEngine
from gui.main_window import MainWindow
import sys
from pathlib import Path
import os

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

# Now import modules that depend on environment variables


def main(page: ft.Page):
    # Page configuration
    page.title = "CV Matching System"
    page.window_width = 1200
    page.window_height = 800
    page.window_resizable = True
    page.theme_mode = ft.ThemeMode.LIGHT

    # Print loaded environment variables for debugging
    print(f"DB_HOST: {os.getenv('DB_HOST', 'localhost')}")
    print(f"DB_PORT: {os.getenv('DB_PORT', '3306')}")
    print(f"DB_NAME: {os.getenv('DB_NAME', 'cv_chisli')}")
    print(f"DB_USER: {os.getenv('DB_USER', 'root')}")
    print(
        f"DB_PASSWORD: {'*' * len(os.getenv('DB_PASSWORD', '')) if os.getenv('DB_PASSWORD') else 'Not set'}")
    print(f"database URL: {DATABASE_URL}")

    try:
        # Initialize database with automatic migration
        print("Initializing database with automatic migration...")
        if not init_db():
            print("Normal initialization failed, trying with force recreation...")
            if not init_db(force_recreate=True):
                raise Exception(
                    "Failed to initialize database even after recreation")

        # Show schema info for debugging
        print("\nCurrent database schema:")
        schema_info = get_schema_info()
        for table, info in schema_info.items():
            print(f"  {table}: {info['column_count']} columns")
            for col_name, col_type in info['columns'].items():
                print(f"    - {col_name}: {col_type}")

        # Test database connection
        print("\nTesting database connection...")
        db = SessionLocal()
        try:
            # Test query
            result = db.query(Applicant).first()
            print("Database connection successful")
            if result:
                print(f"   Found existing applicant: {result.name}")
            else:
                print("   No applicants in database yet")
        except Exception as e:
            print(f"Database test failed: {e}")
            # The auto-migration should have fixed this, but let's try once more
            db.close()
            print("Trying force recreation...")
            init_db(force_recreate=True)
            db = SessionLocal()
            db.query(Applicant).first()
            print("Database connection successful after recreation")
        finally:
            db.close()

        print("Initializing CV processor...")
        cv_processor = CVProcessor()

        print("Initializing search engine...")
        search_engine = SearchEngine()

        try:
            print("Reading CVs")
            cv_processor.process_csv_resumes()
        except Exception as e:
            print(f"Error reading CVs: {e}")
            raise

        print("CV processor initialized successfully")

        print("Creating main window...")
        # Create main window - pass SessionLocal instead of db_manager
        main_window = MainWindow(
            page, SessionLocal, cv_processor, search_engine)

        # Add main window to page
        page.add(main_window.build())
        print("Application initialized successfully!")

    except Exception as e:
        print(f"Error initializing application: {e}")
        # Show error page
        error_content = ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("Application Initialization Error",
                            size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Error: {str(e)}", size=16, color=ft.Colors.RED),
                    ft.Text("Please ensure MySQL is running and check your credentials.",
                            size=14, color=ft.Colors.GREY_600),
                    ft.ElevatedButton(
                        "Retry", on_click=lambda e: page.window_close())
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=50,
                alignment=ft.alignment.center
            )
        ], expand=True)

        page.add(error_content)


if __name__ == "__main__":
    ft.app(target=main)
