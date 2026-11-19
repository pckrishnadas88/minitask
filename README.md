# MiniTask

**A minimal SQLite-backed task queue written in Python.**

MiniTask is an experimental task-processing system built to explore how background job queues work internally.

The goal is to understand and implement the fundamental mechanisms behind reliable task processing: persistence, worker coordination, retries, failure recovery, idempotency and delivery guarantees.

Rather than wrapping an existing queue library, MiniTask builds these concepts incrementally.

> **Status:** Early development — v0.1  
> Not recommended for production workloads.

## Why MiniTask?

Background task processing looks simple at first:

1. Submit a task.
2. Store it somewhere.
3. Let a worker execute it.

But what happens when a worker crashes? What if two workers claim the same task? What if a task succeeds but the worker crashes before recording completion?

MiniTask explores these problems through a small, understandable implementation.

## Current features

- SQLite-backed task persistence
- Task producer
- Task handler registration
- Basic worker implementation
- JSON-based task payloads
- Basic task lifecycle: pending, running, completed and failed

## Technology

- Python
- SQLite
- JSON
- pytest (planned for automated testing)

## Getting started

Clone the repository:

```bash
git clone https://github.com/pckrishnadas88/minitask.git
cd minitask
```

Install in editable mode:

```bash
python3 -m pip install -e .
```

Run the example:

```bash
python3 examples/basic_usage.py
```

Expected output:

```text
Enqueued task: 1
Sending email to test@example.com
```

## Architecture

```text
          Producer
              |
              v
        Task Submission
              |
              v
          SQLite DB
              |
              v
           Worker
              |
              v
        Task Registry
              |
              v
        Task Handler
```

SQLite currently provides persistent task storage. Workers retrieve pending tasks and execute their registered handlers.

## Roadmap

### Phase 1 — Core queue

- [x] Basic task submission
- [x] SQLite persistence
- [x] Task handler registry
- [x] Basic worker execution
- [ ] Automated unit tests
- [ ] Connection lifecycle management

### Phase 2 — Concurrency

- [ ] Atomic task claiming
- [ ] Multiple concurrent workers
- [ ] Transaction boundaries
- [ ] Race-condition testing
- [ ] Worker process isolation

### Phase 3 — Reliability

- [ ] Worker crash recovery
- [ ] Task visibility timeout or lease mechanism
- [ ] Automatic retries
- [ ] Configurable retry policies
- [ ] Failed task handling
- [ ] Idempotency support

### Phase 4 — Developer experience

- [ ] Type-safe task registration
- [ ] Payload validation
- [ ] Configurable worker execution
- [ ] Graceful shutdown
- [ ] Structured logging
- [ ] Task inspection utilities

### Phase 5 — Production-oriented engineering

- [ ] Explicit delivery guarantees
- [ ] Observability and metrics
- [ ] Load testing
- [ ] Performance benchmarks
- [ ] Operational documentation
- [ ] Failure-injection testing

## Engineering principles

MiniTask follows a few principles:

- Prefer explicit implementations over unnecessary abstractions.
- Make failure scenarios visible and testable.
- Document reliability guarantees instead of making assumptions.
- Keep the core implementation small and understandable.
- Understand the trade-offs behind every design decision.

## Learning objectives

This project is also an exploration of distributed-systems concepts:

- Message delivery semantics
- Concurrency and coordination
- Atomic operations
- Transaction isolation
- At-least-once processing
- Idempotent execution
- Failure detection and recovery
- Backpressure and throughput

## Project status

MiniTask is under active development. Its current implementation is intentionally minimal and does not yet provide safe multi-worker execution or crash recovery.

Features and guarantees will be documented as they are implemented and tested.

## License

License not yet selected.