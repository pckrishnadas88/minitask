
import json


class Producer:
    def __init__(self, database):
        self.database = database

    def enqueue(self, task_name, payload):
        with self.database.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO tasks (task_name, payload)
                VALUES (?, ?)
                """,
                (task_name, json.dumps(payload))
            )

            return cursor.lastrowid
