
import json

from minitask import Database, Producer, Worker
from minitask.registry import registry


def test_worker_executes_task(tmp_path):
    db_path = tmp_path / "test_minitask.db"

    database = Database(str(db_path))
    producer = Producer(database)

    executed_tasks = []

    @registry.register("test_send_email")
    def send_email(payload):
        executed_tasks.append(payload["to"])

    task_id = producer.enqueue(
        "test_send_email",
        {"to": "test@example.com"}
    )

    worker = Worker(database)

    result = worker.run_once()

    assert result is True
    assert executed_tasks == ["test@example.com"]

    connection = database.connect()
    try:
        task = connection.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        assert task["status"] == "completed"
        assert json.loads(task["payload"])["to"] == "test@example.com"
    finally:
        connection.close()


def test_worker_returns_false_when_queue_is_empty(tmp_path):
    database = Database(str(tmp_path / "empty.db"))
    worker = Worker(database)

    result = worker.run_once()

    assert result is False
