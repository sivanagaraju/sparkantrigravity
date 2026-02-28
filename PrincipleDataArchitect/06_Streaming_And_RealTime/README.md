# 06 — Streaming & Real-Time Data Architecture

> "Batch is a special case of streaming where the window size is infinity."

Real-time data changes everything: the consistency model, the error handling, the cost profile, and the operational burden. A Principal must know the exact mechanics of watermarks, exactly-once semantics, and what happens when a Kafka broker dies mid-rebalance.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Apache_Kafka_Internals/`

- **Partition Mechanics**: How Kafka stores data as immutable append-only logs per partition. Why partition count is the **upper bound** on consumer parallelism.
- **Consumer Group Rebalancing**: The dreaded "Stop-the-World" rebalance. Cooperative Sticky Assignor vs. Eager Assignor. Why a slow consumer can freeze an entire consumer group.
- **Exactly-Once Semantics (EOS)**: Idempotent producers (`enable.idempotence=true`), transactional producers (`initTransactions()`), and the `read_committed` isolation level. The performance overhead of EOS.
- **KRaft Mode**: Removing ZooKeeper. How Kafka's new Raft-based metadata quorum works and why it matters for operational simplicity.
- **Schema Registry and Compatibility**: BACKWARD, FORWARD, FULL compatibility modes. Why a breaking schema change on a Kafka topic at 3 AM can silently corrupt every downstream consumer.

### `02_Stream_Processing_Engines/`

- **Apache Flink Deep Dive**: Event time vs. processing time. Watermark generation strategies (bounded-out-of-orderness). State backends (RocksDB vs. heap). Checkpointing mechanics (Chandy-Lamport algorithm). Savepoints for application upgrades.
- **Spark Structured Streaming**: Micro-batch (default, 100ms+) vs. Continuous Processing (experimental, ~1ms). Trigger modes. Exactly-once with idempotent sinks. Why Spark streaming is simpler but Flink is more powerful for complex event processing.
- **Kafka Streams**: The lightweight alternative. No separate cluster required. KTable vs. KStream. Interactive queries for serving state directly from the stream processor.

### `03_Event_Driven_Architecture_Patterns/`

- **Event Sourcing**: Storing every state change as an immutable event rather than overwriting current state. Replaying the event log to reconstruct any point-in-time state.
- **CQRS (Command Query Responsibility Segregation)**: Separating the write model from the read model. Building materialized views from event streams for sub-millisecond read performance.
- **The Outbox Pattern**: Solving the dual-write problem. Instead of writing to both the database and Kafka (which can fail independently), write to the database and let CDC (Debezium) publish the event.
- **Saga Pattern for Long-Running Transactions**: Choreography (event-based) vs. Orchestration (coordinator-based). Implementing compensating transactions when Step 3 of a 5-step saga fails.

### `04_CDC_Change_Data_Capture/`

- **Log-Based CDC (Debezium)**: Reading the database's Write-Ahead Log (WAL/binlog) to capture every INSERT, UPDATE, DELETE as a stream event. Zero impact on the source database's query performance.
- **Query-Based CDC**: Polling the source table with `WHERE updated_at > last_checkpoint`. Simple but misses hard deletes and creates load on the source system.
- **CDC Ordering and Deduplication**: Handling out-of-order events when the upstream database uses multi-threaded replication. Using LSN (Log Sequence Number) for global ordering.

### `05_Windowing_and_Late_Data/`

- **Tumbling, Sliding, Session, and Global Windows**: The four fundamental window types. Using session windows to group user click activity with a 30-minute inactivity gap.
- **Watermarks and Allowed Lateness**: Defining "I'm willing to wait 5 minutes for late data, but after that, I'll emit the window result and drop anything later." The trade-off between latency and completeness.
- **Side Outputs for Late Data**: Rather than dropping late events, routing them to a separate stream for later reconciliation.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
