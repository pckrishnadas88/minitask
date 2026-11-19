
import sqlite3
from contextlib import contextmanager


class Database:
    def __init__(self, path):
        self.path = path
        self.initialize()

    def connect(self):
        connection = sqlite3.connect(
            self.path,
            timeout=10
        )
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def connection(self):
        connection = self.connect()

        try:
            yield connection
            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def initialize(self):
        with self.connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    
                )
                """
            )
