
from minitask import Database, Producer


def test_producer_persists_task(tmp_path):
    db_path = tmp_path / "test_minitask.db"

    database = Database(str(db_path))
    producer = Producer(database)

    task_id = producer.enqueue(
        "send_email",
        {"to": "test@example.com"}
    )

    connection = database.connect()
    try:
        task = connection.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        assert task is not None
        assert task["task_name"] == "send_email"
        assert task["status"] == "pending"
        assert task["payload"] == '{"to": "test@example.com"}'
    finally:
        connection.close()
