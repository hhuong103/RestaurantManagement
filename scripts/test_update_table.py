import sqlite3

DB_PATH = 'database.db'

def test_update_table():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Update table 1
        cursor.execute("""
            UPDATE restaurant_tables
            SET status = 'Reserved', reserved_by = 'Test User', reserved_at = '2026-01-10T15:00'
            WHERE id = 1
        """)
        conn.commit()
        print("Updated table 1")
    except sqlite3.Error as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_update_table()