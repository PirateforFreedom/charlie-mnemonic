import sqlite3
import bcrypt
import os
import binascii

class Authentication:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def open(self):
        self.conn = sqlite3.connect("users.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            session_token TEXT NOT NULL
        )
        """)

    def register(self, username, password):
        self.open()
        try:
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            # Convert hashed_password to string
            hashed_password_str = hashed_password.decode("utf-8")
            session_token = binascii.hexlify(os.urandom(24)).decode()
            self.cursor.execute("INSERT INTO users (username, password, session_token) VALUES (?, ?, ?)", (username, hashed_password_str, session_token))
            self.conn.commit()
            return session_token
        except sqlite3.IntegrityError:
            return False
        finally:
            self.close()

    def login(self, username, password):
        self.open()
        self.cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = self.cursor.fetchone()

        if result is not None:
            stored_password = result[0]
            # Make sure stored_password is a string before encoding it to bytes
            if isinstance(stored_password, bytes):
                stored_password = stored_password.decode("utf-8")
            stored_password_bytes = stored_password.encode("utf-8")
            if bcrypt.checkpw(password.encode("utf-8"), stored_password_bytes):
                # If password is correct, generate a session token
                session_token = binascii.hexlify(os.urandom(24)).decode()
                # Store the session token in the database
                self.cursor.execute("UPDATE users SET session_token = ? WHERE username = ?", (session_token, username))
                self.conn.commit()
                self.close()
                print(f'User: {username} - Session token: {session_token}')
                # Return the session token
                return session_token
            else:
                return False
        else:
            return False
        
    def logout(self, username, session_token):
        self.open()
        self.cursor.execute("SELECT session_token FROM users WHERE username = ?", (username,))
        result = self.cursor.fetchone()

        if result is not None:
            stored_token = result[0]
            if stored_token == session_token:
                # If the session token is correct, delete it from the database
                self.cursor.execute("UPDATE users SET session_token = NULL WHERE username = ?", (username,))
                self.conn.commit()
                self.close()
                return True
            else:
                return False
        else:
            return False

    def check_token(self, username, session_token):
        self.open()
        self.cursor.execute("SELECT session_token FROM users WHERE username = ?", (username,))
        result = self.cursor.fetchone()

        if result is not None:
            stored_token = result[0]
            self.close()
            if stored_token == session_token:
                return True
        return False

if __name__ == "__main__":
    auth = Authentication()