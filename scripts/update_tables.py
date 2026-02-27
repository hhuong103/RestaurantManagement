import sqlite3

DB_PATH = 'database.db'

def update_existing_tables():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT id, name FROM restaurant_tables")
        tables = cursor.fetchall()
        
        for table_id, name in tables:
            # Assign type and capacity based on name or random
            if 'VIP' in name.upper():
                type = 'VIP'
                capacity = 4
            elif 'Family' in name.upper() or 'Group' in name.upper():
                type = 'Family'
                capacity = 6
            else:
                type = 'Standard'
                capacity = 2
            
            cursor.execute("""
                UPDATE restaurant_tables
                SET type = ?, capacity = ?
                WHERE id = ?
            """, (type, capacity, table_id))
        
        conn.commit()
        print("Updated existing tables with type and capacity.")
    except sqlite3.Error as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_existing_tables()