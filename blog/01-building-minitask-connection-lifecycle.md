# Building MiniTask: From a Basic Task Queue to Safe Database Connection Management

## Why I Started Building MiniTask

I wanted to understand how background task processing systems work
internally.

Tools like Celery and RabbitMQ solve interesting engineering problems,
but using them doesn't necessarily teach us how their internal
mechanisms work.

So I decided to build a much smaller system from scratch using Python
and SQLite.

The goal isn't to recreate Celery or RabbitMQ. It's to understand the
fundamental building blocks behind background processing systems, one
feature at a time.

I'm calling this project **MiniTask**.

GitHub: https://github.com/pckrishnadas88/minitask

------------------------------------------------------------------------

## What Are We Building?

Imagine an application that needs to send an email after a user
registers.

One approach is to send the email directly during the HTTP request.
However, email delivery may take several seconds, and the user has to
wait until that operation finishes.

Instead, we can separate the operation:

1.  The application submits an email task.
2.  The task is stored in a database.
3.  A background worker retrieves it.
4.  The worker executes the email operation.

The application can return a response without waiting for the email
delivery process.

This is the basic idea behind a background task queue.

## 1. Understanding the Producer--Consumer Pattern

Our first architectural concept is the producer--consumer pattern.

There are two main participants.

### Producer

The producer creates and submits tasks.

``` python
producer.enqueue(
    "send_email",
    {"to": "test@example.com"}
)
```

The producer doesn't need to know how the email is actually sent. Its
responsibility is to submit the task.

### Consumer (Worker)

The worker retrieves tasks and executes them.

It doesn't need to know which application originally submitted the task.
Its responsibility is to process available tasks.

This separation is important because task submission and task execution
become independent operations.

## 2. Why SQLite Persistence?

Initially, we could store tasks in a Python list:

``` python
tasks = []

tasks.append({
    "task_name": "send_email",
    "payload": {"to": "test@example.com"}
})
```

But what happens when the Python process stops?

The list disappears. All pending tasks are lost.

Instead, MiniTask stores tasks in SQLite. A database record allows task
information to exist independently of the lifetime of the Python
process.

Our architecture now looks like this:

``` text
Application
    |
    v
Producer
    |
    v
SQLite Database
    |
    v
Worker
    |
    v
Task Handler
```

The database becomes the shared storage layer between the producer and
worker.

This is an important foundation for understanding persistent message
queues.

However, persistence alone doesn't guarantee reliable processing. We
still need to handle interruptions, concurrent workers and recovery
scenarios.

## 3. Task Handler Registry

How does a worker know which Python function should execute a particular
task?

For example, consider these tasks:

-   `send_email`
-   `generate_invoice`
-   `resize_image`

We don't want to hardcode every possible operation inside the worker.

Instead, MiniTask has a task handler registry.

A registry maintains the association between a task name and its
corresponding Python function.

Conceptually:

``` python
{
    "send_email": send_email,
    "generate_invoice": generate_invoice,
    "resize_image": resize_image
}
```

When a worker retrieves a task named `send_email`, it looks up the
corresponding function and invokes it with the task payload.

For example:

``` python
@registry.register("send_email")
def send_email(payload):
    print(f"Sending email to {payload['to']}")
```

This gives us an important separation:

-   Producer knows the task name and payload.
-   Registry knows the available handlers.
-   Worker knows how to execute registered handlers.

The producer doesn't need to import or directly call the business
function.

## 4. Basic Worker Execution

Now we have the basic components:

-   Producer
-   SQLite database
-   Handler registry
-   Worker

The worker retrieves a pending task, identifies its handler, and
executes it.

We also track task execution using statuses.

Our basic task lifecycle is:

``` text
pending
   |
   v
running
   |
   v
completed
```

If execution fails, the task can enter a failed state.

This gives us visibility into what happened to a task.

At this stage, we have basic sequential task execution. We haven't
implemented safe coordination between multiple workers.

That distinction will become important later.

## 5. Understanding Database Connections

Once the producer and worker started using SQLite, another
responsibility became important: managing database connections
correctly.

A database connection is an active communication channel between our
Python application and the SQLite database.

We create one using:

``` python
connection = sqlite3.connect("minitask.db")
```

Through this connection, we can execute SQL statements, read records and
modify data.

But opening a connection is only one part of the job. We also need to
decide:

-   Who owns the connection?
-   How long should it remain open?
-   When should changes be committed?
-   What should happen if an operation fails?
-   Who guarantees that the connection is closed?

These questions are collectively part of connection lifecycle
management.

### The connection lifecycle

A typical managed database operation follows this sequence:

``` text
Create connection
      |
      v
Execute database operations
      |
      v
Success? -------- No --------> Roll back
      |                           |
     Yes                          |
      |                           |
      v                           |
   Commit                         |
      |                           |
      +------------+--------------+
                   |
                   v
             Close connection
```

The important principle is that cleanup must happen on both successful
and failed operations.

## 6. Connection and Transaction Are Different

This was an important distinction to understand.

A **connection** is the communication channel to the database.

A **transaction** is a group of database operations that should be
committed or rolled back together.

For example:

``` python
connection = sqlite3.connect("minitask.db")

connection.execute(
    "INSERT INTO tasks (task_name, status) VALUES (?, ?)",
    ("send_email", "pending")
)

connection.commit()
connection.close()
```

Here:

-   `connect()` opens the connection.
-   `execute()` performs the SQL operation.
-   `commit()` commits the transaction.
-   `close()` closes the connection.

Commit and close are not the same thing.

A successful commit does not close the connection. Similarly, rollback
does not close it.

We need to manage both transaction completion and resource cleanup.

### A Python SQLite detail worth remembering

This code may look as though it automatically closes the connection:

``` python
with sqlite3.connect("minitask.db") as connection:
    connection.execute(
        "INSERT INTO tasks (task_name, status) VALUES (?, ?)",
        ("send_email", "pending")
    )
```

However, SQLite's connection context manager manages transaction
completion. It commits on successful exit or rolls back on an exception,
but it does **not** automatically close the connection.

That distinction is easy to miss.

## 7. Python Context Managers

Python's `with` statement provides a convenient way to manage resources.

A familiar example is opening a file:

``` python
with open("example.txt") as file:
    content = file.read()
```

The file is closed when the block exits, including when an exception
occurs.

We wanted a similar interface for MiniTask database connections.

Python supports custom context managers. One way to create them is with
a class implementing `__enter__` and `__exit__`. Another, more concise
approach is the `@contextmanager` decorator from `contextlib`.

### Understanding `@contextmanager`

First, consider a small example:

``` python
from contextlib import contextmanager


@contextmanager
def my_context():
    print("Entering context")

    yield

    print("Leaving context")


with my_context():
    print("Inside the with block")
```

Output:

``` text
Entering context
Inside the with block
Leaving context
```

The `yield` statement is the important part.

When Python reaches `yield`, the generator pauses and gives control to
the body of the `with` block.

When the block finishes, execution resumes after `yield`.

If an exception occurs inside the `with` block, Python throws that
exception back at the `yield` point. This lets the context manager
handle the failure.

### Why use `yield` instead of `return`?

A `return` statement finishes a function.

A `yield` statement pauses a generator function and allows it to resume
later.

That pause-and-resume behaviour is what makes this pattern useful for
resource management.

## 8. Centralizing Connection Lifecycle Management

We don't want the Producer and Worker to each repeat connection
creation, commit, rollback and cleanup logic.

Instead, the Database class should own that responsibility.

The design has two separate methods:

-   `connect()` creates and returns a raw SQLite connection.
-   `connection()` manages the lifecycle of a connection.

The managed method can call the low-level method internally.

An illustrative implementation looks like this:

``` python
import sqlite3
from contextlib import contextmanager


class Database:
    def __init__(self, path):
        self.path = path

    def connect(self):
        connection = sqlite3.connect(self.path)
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
```

Let's understand the responsibilities.

**Create the connection**

``` python
connection = self.connect()
```

The low-level method creates the SQLite connection and configures its
row factory.

**Give the connection to the caller**

``` python
yield connection
```

The caller receives the connection inside the `with` block.

**Commit on success**

``` python
connection.commit()
```

When the caller's block finishes successfully, execution resumes after
`yield` and commits the transaction.

**Roll back on failure**

``` python
except Exception:
    connection.rollback()
    raise
```

If the caller's code raises an exception, the context manager rolls back
the transaction and re-raises the exception.

Re-raising is important: it ensures that the original failure is not
silently swallowed.

**Always close**

``` python
finally:
    connection.close()
```

The `finally` block runs whether the operation succeeds or fails.

This is what guarantees cleanup.

## 9. Using the Managed Connection

The main benefit is that the Producer and Worker no longer need to
repeat transaction and cleanup code.

For example:

``` python
with database.connection() as connection:
    connection.execute(
        "INSERT INTO tasks (task_name, status) VALUES (?, ?)",
        ("send_email", "pending")
    )
```

We don't manually call:

``` python
connection.commit()
connection.rollback()
connection.close()
```

The custom context manager handles those responsibilities.

This automatic behaviour applies specifically to our
`database.connection()` context manager. It is not a property of every
`with` statement.

### Why keep both `connect()` and `connection()`?

They have different responsibilities:

  -----------------------------------------------------------------------
  Method                              Responsibility
  ----------------------------------- -----------------------------------
  `connect()`                         Create and return a SQLite
                                      connection

  `connection()`                      Manage connection usage,
                                      transaction completion and cleanup
  -----------------------------------------------------------------------

Separating these responsibilities gives us a low-level connection
creator and a convenient managed interface.

## 10. Connection Lifecycle and Worker Design

There is another useful design consideration when processing background
tasks.

Imagine a worker retrieves a task that sends an email.

Sending the email may involve a slow external service. We don't want to
hold a database connection open while waiting for that service.

A better general flow is:

``` text
Open database connection
        |
        v
Retrieve task and update status
        |
        v
Close database connection
        |
        v
Execute task handler
        |
        v
Open database connection again
        |
        v
Update task result
        |
        v
Close database connection
```

This keeps database connections focused on database operations.

It also gives us a useful foundation for future worker concurrency.

This connection-lifecycle improvement does not, by itself, make task
claiming safe for multiple workers. That is a separate problem we will
address in a later milestone.

## 11. Testing the Connection Lifecycle

We shouldn't consider connection lifecycle management complete merely
because the context manager exists.

We need to verify its behaviour.

Useful tests include:

### Successful operation

-   Open a managed connection.
-   Execute a database write.
-   Exit the context successfully.
-   Verify that the change was committed.
-   Verify that the connection was closed.

### Failed operation

-   Open a managed connection.
-   Execute a database write.
-   Raise an intentional exception.
-   Verify that the transaction was rolled back.
-   Verify that the connection was closed.
-   Verify that the exception was propagated.

### Integration tests

We should also run the existing Producer and Worker tests to ensure that
moving to managed connections hasn't broken task submission or
execution.

The aim is to test observable behaviour, not just the existence of a
context manager method.

## 12. What Have We Achieved?

The first version of MiniTask now covers these foundational areas:

-   Basic task submission.
-   SQLite persistence.
-   Task handler registry.
-   Basic worker execution.
-   Automated unit tests.
-   Database connection lifecycle management.

We now have a basic producer--consumer architecture with database-backed
task storage and centralized connection management.

But this is not yet a reliable distributed task queue.

### What is still missing?

**Atomic task claiming**

Two workers could potentially retrieve the same pending task. We need a
safe claiming mechanism.

**Multiple worker coordination**

We haven't implemented reliable coordination between concurrent workers.

**Crash recovery**

What happens if a worker stops while processing a task?

**Retries**

Should failed tasks be attempted again? How many times? With what delay?

**Idempotency**

How do we prevent duplicate side effects when a task is executed more
than once?

These are separate engineering problems, and we'll explore them
incrementally.

## 13. What Comes Next?

The next milestone is **atomic task claiming**.

We'll investigate a concrete race condition:

1.  Worker A reads a pending task.
2.  Worker B reads the same pending task.
3.  Both attempt to execute it.

We need to understand why this can happen and how database transactions
and atomic updates can prevent it.

This will be our next step towards supporting multiple workers safely.

## Final Thoughts

I believe building small systems from scratch is an effective way to
understand the engineering decisions behind larger infrastructure
projects.

Rather than immediately adopting a large framework, MiniTask gives me an
opportunity to explore the underlying mechanisms and their trade-offs.

The project will grow incrementally. Every milestone will include
implementation, tests, and a detailed explanation of what was learned.

**The objective isn't to build another Celery. It's to understand why
systems like Celery need the mechanisms they have.**

More importantly, I want to understand each mechanism well enough to
explain and defend the design decisions behind it.

------------------------------------------------------------------------

*MiniTask is an educational project under active development. The
article describes its current foundational scope; it does not claim
production-grade delivery guarantees or safe multi-worker coordination.*
