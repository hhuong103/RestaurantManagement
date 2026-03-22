import sqlite3


class MenuModel:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self.initialize_db()

    def initialize_db(self):
        """
        Creates the 'menus' table if it doesn't exist and ensures needed columns exist.
        """
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS menus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                image TEXT,
                rating REAL DEFAULT 5.0,
                category TEXT DEFAULT 'Main Course'
            )
            """
        )

        # Ensure columns exist for backward compatibility
        cursor.execute("PRAGMA table_info(menus)")
        columns = [column[1] for column in cursor.fetchall()]

        if "rating" not in columns:
            cursor.execute("ALTER TABLE menus ADD COLUMN rating REAL DEFAULT 5.0")
        if "category" not in columns:
            cursor.execute("ALTER TABLE menus ADD COLUMN category TEXT DEFAULT 'Main Course'")

        connection.commit()
        connection.close()

    def store_menu(self, name, price, description, image_filename=None, rating=5.0, category="Main Course"):
        """
        Insert a new menu item into the 'menus' table.
        """
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO menus (name, price, description, image, rating, category)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, price, description, image_filename, rating, category),
        )

        connection.commit()
        connection.close()

    def get_menu(self):
        """
        Fetch all menu items.
        """
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        cursor.execute("SELECT id, name, price, description, image, rating, category FROM menus")
        results = cursor.fetchall()

        connection.close()

        menu_items = []
        for row in results:
            item_id, name, price, description, image, rating, category = row
            menu_items.append(
                {
                    "id": item_id,
                    "name": name,
                    "price": price,
                    "description": description,
                    "image": image,
                    "rating": rating,
                    "category": category,
                }
            )
        return menu_items

    def edit_menu(self, item_id, name, price, description, rating=5.0):
        """
        Update an existing menu item in the 'menus' table.
        """
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE menus
            SET name = ?, price = ?, description = ?, rating = ?
            WHERE id = ?
            """,
            (name, price, description, rating, item_id),
        )

        connection.commit()
        connection.close()

    def update_menu_item(self, item_id, name, price, description, image_filename, rating=5.0, category=None):
        """
        Update an existing menu item. If category is None, keep the current category.
        """
        connection = None
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()

            # Check if the menu item exists before updating
            cursor.execute("SELECT id, category FROM menus WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Menu item with ID {item_id} does not exist.")
            current_category = row[1] if len(row) > 1 else "Main Course"

            if category is None:
                category = current_category

            cursor.execute(
                """
                UPDATE menus
                SET name = ?, price = ?, description = ?, image = ?, rating = ?, category = ?
                WHERE id = ?
                """,
                (name, price, description, image_filename, rating, category, item_id),
            )

            connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            if connection:
                connection.close()

    def delete_menu(self, item_id):
        """
        Delete a menu item by ID.
        """
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM menus WHERE id = ?", (item_id,))
        connection.commit()
        connection.close()

    def get_menu_item_by_id(self, item_id):
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, name, price, description, image, rating, category
            FROM menus WHERE id = ?
            """,
            (item_id,),
        )
        result = cursor.fetchone()
        connection.close()

        if result:
            item_id, name, price, description, image, rating, category = result
            return {
                "id": item_id,
                "name": name,
                "price": price,
                "description": description,
                "image": image,
                "rating": rating,
                "category": category,
            }
        return None

    def search_menu(self, keyword=None, category=None):
        """
        Search menu items by keyword and/or category.
        - keyword: matches name (and description as a bonus)
        - category: exact match (use None/'All'/'' to disable)
        """
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        sql = "SELECT id, name, price, description, image, rating, category FROM menus WHERE 1=1"
        params = []

        if keyword:
            kw = f"%{keyword}%"
            sql += " AND (name LIKE ? OR COALESCE(description, '') LIKE ?)"
            params.extend([kw, kw])

        if category and str(category).strip() and str(category).lower() not in {"all", "all topics", "all categories"}:
            sql += " AND category = ?"
            params.append(category)

        cursor.execute(sql, params)
        results = cursor.fetchall()
        connection.close()

        menu_items = []
        for row in results:
            item_id, name, price, description, image, rating, category = row
            menu_items.append(
                {
                    "id": item_id,
                    "name": name,
                    "price": price,
                    "description": description,
                    "image": image,
                    "rating": rating,
                    "category": category,
                }
            )
        return menu_items

    def get_top_rated(self, limit=5):
        """
        Fetch top rated menu items.
        """
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, name, price, description, image, rating, category FROM menus ORDER BY rating DESC LIMIT ?",
            (limit,),
        )
        results = cursor.fetchall()
        connection.close()

        menu_items = []
        for row in results:
            item_id, name, price, description, image, rating, category = row
            menu_items.append(
                {
                    "id": item_id,
                    "name": name,
                    "price": price,
                    "description": description,
                    "image": image,
                    "rating": rating,
                    "category": category,
                }
            )
        return menu_items

    def get_all_menu_items(self):
        """
        Retrieve all menu items from the 'menus' table.
        """
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM menus ORDER BY name")
        items = cursor.fetchall()

        connection.close()
        return items

    def get_distinct_categories(self):
        """
        Return list of available categories (topics) from DB.
        """
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT category FROM menus WHERE category IS NOT NULL AND TRIM(category) != '' ORDER BY category")
        rows = cursor.fetchall()
        connection.close()
        return [r[0] for r in rows]


    