import sqlite3

class Database:
    def __init__(self, path: str):
        self.path = path 
        self.initialize()

    def connect(self):
        connection = sqlite3.connect(
            self.path,
            timeout= 10
        )
        connection.row_factory = sqlite3.Row
        return connection
    def initialize(self):
        with self.connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                started_at TEXT,
                completed_at TEXT
                )
            """)