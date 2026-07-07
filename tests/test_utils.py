import sqlite3
import random
from pathlib import Path
import os

# Global variable to hold in-memory database path for the session
_IN_MEMORY_DB_PATH = None


def create_test_database(num_records=10000):
    """
    Create a test database with random sample data for testing purposes.

    Args:
        num_records (int): Number of records to sample from original database

    Returns:
        str: Path to the created database file
    """
    # Get absolute path to main database  
    # Use the directory of this script to find the main db
    current_dir = Path(__file__).resolve().parent
    # Go up one level to get to project root, then find log_processor.db
    project_root = current_dir.parent
    main_db_path = project_root / "log_processor.db"

    if not main_db_path.exists():
        raise FileNotFoundError(f"Main database not found at {main_db_path}")

    # Make sure we're using the temporary directory
    temp_db_path = Path("/tmp") / f"test_db_{random.randint(10000, 99999)}.db"
    temp_db_path = str(temp_db_path)

    # Connect to original database
    main_conn = sqlite3.connect(main_db_path)

    try:
        # Get record count
        cursor = main_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        total_records = cursor.fetchone()[0]

        if num_records > total_records:
            num_records = total_records

        # Select random records using SQL ORDER BY RANDOM()
        cursor.execute(f"SELECT * FROM events ORDER BY RANDOM() LIMIT {num_records}")
        sample_data = cursor.fetchall()

        # Get column names
        cursor.execute("PRAGMA table_info(events)")
        columns = [col[1] for col in cursor.fetchall()]

        # Create a new database
        conn = sqlite3.connect(temp_db_path)

        # Get table structure from the original and recreate it
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='events'"
        )
        table_sql = cursor.fetchone()

        if table_sql:
            create_table_sql = table_sql[0]
            conn.execute(create_table_sql)
        else:
            # Fallback to simple structure
            conn.execute(
                "CREATE TABLE events (source_ip TEXT, event_type TEXT, status_code INTEGER, user_agent TEXT, url TEXT, date_time TEXT)"
            )

        # Insert sample data
        placeholders = ", ".join(["?" for _ in columns])
        insert_sql = f"INSERT INTO events VALUES ({placeholders})"

        for row in sample_data:
            conn.execute(insert_sql, row)

        conn.commit()
        conn.close()

    finally:
        main_conn.close()

    return temp_db_path


def get_in_memory_db_path():
    """
    Get or create the in-memory database path for current pytest session.

    Returns:
        str: Path to the temporary in-memory database file
    """
    global _IN_MEMORY_DB_PATH

    if _IN_MEMORY_DB_PATH is None:
        # Create new test database with sample data
        _IN_MEMORY_DB_PATH = create_test_database(10000)

    return _IN_MEMORY_DB_PATH
