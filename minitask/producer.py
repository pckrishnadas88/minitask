import json 

from minitask.database import Database

class Producer:
    def __init__(self, database:Database):
        self.database = database

    def enqueue(self, task_name: str, payload: dict) -> int:
        with self.database.connect() as connection:
            cursor = connection.execute("""
                INSERT INTO tasks (task_name, payload)
                VALUES (?, ?)
            """,
            (task_name, json.dumps(payload))
            )
            return cursor.lastrowid