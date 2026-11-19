
from minitask import Database


def test_database_creates_tasks_table(tmp_path):
    db_path = tmp_path / "test_minitask.db"

    database = Database(str(db_path))

    connection = database.connect()
    try:
        cursor = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'tasks'
            """
        )

        result = cursor.fetchone()

        assert result is not None
        assert result["name"] == "tasks"
    finally:
        connection.close()
