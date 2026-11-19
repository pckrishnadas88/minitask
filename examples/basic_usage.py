
from minitask import Database, Producer, Worker
from minitask.registry import registry


@registry.register("send_email")
def send_email(payload):
    print(f"Sending email to {payload['to']}")


database = Database("minitask.db")

producer = Producer(database)

task_id = producer.enqueue(
    "send_email",
    {"to": "test@example.com"}
)

print(f"Enqueued task: {task_id}")

worker = Worker(database)

while worker.run_once():
    pass
