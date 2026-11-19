import json 

from minitask.database import Database
from minitask.registry import registry

class Worker:
    def __init__(self, database: Database):
        self.database = database

    def run_once(self):
        with self.database.connect() as connection:
            task = connection.execute(
                """
                    SELECT * FROM tasks
                    WHERE status = 'pending'
                    ORDER BY id
                    LIMIT 1
                """
            ).fetchone()

            if task is None:
                return False 
            connection.execute(
                """
                UPDATE tasks 
                SET status = 'running',
                    started_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (task["id"],)
            )
        try:
            handler = registry.get(task["task_name"])
            payload = json.loads(task["payload"])
            handler(payload)

            with self.database.connect() as connection:
                connection.execute(
                    """
                        UPDATE tasks
                        SET status = 'completed',
                            completed_at = CURRENT_TIMESTAMP
                        WHERE id = ?

                    """, 
                    (task["id"],)
                    )
        except Exception as error:
            with self.database.connect() as connection:
                connection.execute(
                    """
                    UPDATE tasks
                    SET status = 'failed'
                    WHERE id = ?
                    """,
                    (task["id"],)
                )

            print(f"Task failed: {error}")

        return True