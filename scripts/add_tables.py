import sqlite3

DB_PATH = 'database.db'

def add_more_tables():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Add more tables
        new_tables = ['Table 6', 'Table 7', 'Table 8', 'Table 9', 'Table 10', 'Table 11', 'Table 12', 'Table 13', 'Table 14', 'Table 15']
        for table in new_tables:
            cursor.execute("""
                INSERT OR IGNORE INTO restaurant_tables (name, status)
                VALUES (?, 'Available')
            """, (table,))
        conn.commit()
        print("Added more tables successfully.")
    except sqlite3.Error as e:
        print(f"Error adding tables: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_more_tables()