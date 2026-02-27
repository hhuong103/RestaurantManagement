import sqlite3
import bcrypt

class UserModel:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self._create_table()

    
    def create_user(self, username, password, role="customer"):
        """Create a new user with hashed password."""
        if not password or not isinstance(password, str):
            raise ValueError("Invalid password")
        hashed = bcrypt.hashpw(password[:72].encode('utf-8'), bcrypt.gensalt())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, (username, hashed.decode('utf-8'), role))
        conn.commit()
        conn.close()

    def find_user_by_username(self, username):
        """Return user record by username or None if not found."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        return user

    def verify_password(self, plain_password, hashed_password):
        """Compare plain password with stored hashed password."""
        if not plain_password or not isinstance(plain_password, str):
            return False
        return bcrypt.checkpw(plain_password[:72].encode('utf-8'), hashed_password.encode('utf-8'))




    def _create_table(self):
        """
        Create the users table if it doesn't exist.
        """
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)
        connection.commit()
        connection.close()

   
    
    
    def get_all_users(self):
        """
        Retrieve all users from the database.
        """
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT id, username, password, role FROM users")
        results = cursor.fetchall()
        connection.close()

        users = []
        for row in results:
            user_id, username, password, role = row
            users.append({
                "id": user_id,
                "username": username,
                "password": password,
                "role": role
            })
        return users

    def get_user_by_id(self, user_id):
        """
        Retrieve a specific user by their ID.
        """
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT id, username, password, role FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        connection.close()

        if result:
            user_id, username, password, role = result
            return {
                "id": user_id,
                "username": username,
                "password": password,
                "role": role
            }
        return None

    

    def update_user(self, user_id, username, password=None, role=None):
        """
        Update user information in the database.
        """
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            if password:  # Update all fields
                hashed_password = bcrypt.hash(password)
                cursor.execute("""
                    UPDATE users
                    SET username = ?, password = ?, role = ?
                    WHERE id = ?
                """, (username, hashed_password, role, user_id))
            else:  # Don't update password
                cursor.execute("""
                    UPDATE users
                    SET username = ?, role = ?
                    WHERE id = ?
                """, (username, role, user_id))
            connection.commit()

    def delete_user(self, user_id):
        """
        Delete a user from the database by their ID.
        """
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        connection.commit()
        connection.close()
   
    