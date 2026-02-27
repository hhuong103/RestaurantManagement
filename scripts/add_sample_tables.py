import sqlite3

DB_PATH = 'database.db'

def add_sample_tables():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Add sample tables
        sample_tables = [
            ('VIP Table 1', 'VIP', 4, 'Premium service, Private seating', 'Available'),
            ('Family Table 1', 'Family', 6, 'Kids menu, High chairs', 'Available'),
            ('Group Table 1', 'Group', 10, 'Large group seating, Special events', 'Available'),
            ('VIP Table 2', 'VIP', 4, 'Premium service, Ocean view', 'Available'),
            ('Family Table 2', 'Family', 6, 'Kids menu, Coloring books', 'Available'),
        ]
        
        for name, type, capacity, services, status in sample_tables:
            cursor.execute("""
                INSERT OR IGNORE INTO restaurant_tables (name, type, capacity, services, status)
                VALUES (?, ?, ?, ?, ?)
            """, (name, type, capacity, services, status))
        
        conn.commit()
        print("Added sample tables.")
    except sqlite3.Error as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_sample_tables()