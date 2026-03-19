# Interview Angle: Connection Pooling

## How This Appears

Connection pooling questions surface in Senior+ interviews as:
1. **System Design:** "Design a high-throughput API. How do you manage database connections at scale?"
2. **Debugging:** "Your application is throwing 'cannot acquire connection' errors under load. Diagnose."
3. **Architecture:** "You have 100 microservices connecting to one PostgreSQL instance. How do you prevent connection exhaustion?"

## Sample Questions & Answer Frameworks

### Q1: "Why is more connections not always better?"

**Strong:** "Database performance is not linear with connection count. On an 8-core machine, only 8 queries can truly execute concurrently. Additional connections wait in the database's internal queue, consuming memory for their process/thread stack, and increasing lock contention and context switch overhead. Experiments consistently show that throughput peaks at roughly `(cores × 2)` connections and degrades beyond that. A pgbench test on 4 cores typically peaks at ~20 connections. At 200 connections, throughput drops by 30-50%.

The correct approach is to keep the actual database connection count small (matching the core count) and use a connection pool to queue application requests. The pool creates the *illusion* of many connections while maintaining a small, efficient backend pool."

### Q2: "Explain the difference between session pooling and transaction pooling."

**Strong:** "In session pooling, a backend database connection is assigned to a client for the entire duration of its connection. If the client connects, runs 3 queries over 10 minutes, then disconnects, that backend connection is occupied for the full 10 minutes—even during idle periods between queries. This provides full compatibility with session-stateful features (temp tables, SET variables, advisory locks) but offers minimal pooling benefit.

In transaction pooling, the backend connection is assigned only for the duration of a single transaction (BEGIN → COMMIT/ROLLBACK). Between transactions, the connection is returned to the pool and can serve other clients. This provides dramatically better multiplexing—1000 clients can efficiently share 50 backend connections if transactions are short. However, it breaks any feature that depends on session state persisting across transactions, because the next transaction may use a completely different backend connection."

### Q3: "How would you architect database connectivity in a Kubernetes deployment with 100 pods?"

**Principal Answer:**
"The naive approach—each pod opens N connections directly to PostgreSQL—fails at scale. 100 pods × 20 connections = 2000 connections, which overwhelms PostgreSQL.

My architecture:
1. **Deploy a centralized PgBouncer** (2 instances behind a Kubernetes Service for HA) in transaction mode with `max_db_connections = 25-40` (matching the database's optimal concurrency).
2. **Each pod uses HikariCP** with `maximumPoolSize = 3-5`. Pods connect to PgBouncer, not directly to PostgreSQL.
3. **PgBouncer multiplexes** 300-500 application connections into 25-40 backend connections.
4. **Monitor** PgBouncer's `SHOW POOLS` for `cl_waiting > 0` (clients queuing). If this is consistently positive, either increase `max_db_connections` (if the database can handle it) or optimize query performance to reduce connection hold time.
5. **For autoscaling:** The system is safe—new pods open more connections to PgBouncer, but PgBouncer caps database connections. The queue grows, providing natural backpressure."

### Q4: "Your team's Spring Boot app ran fine for months, but now connections are timing out every 6-8 hours. What's happening?"

**Debugging Framework:**
1. "First, check for connection leaks. Enable HikariCP `leak-detection-threshold = 10000` and check logs for leaked connection stack traces.
2. Check `SHOW POOLS` in PgBouncer (if used) — look for `sv_active` growing without corresponding `sv_idle`.
3. Check for long-running transactions: `SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction' AND xact_start < now() - interval '5 minutes'`.
4. Check if the pool is exhausted: HikariCP metrics show `pending` requests growing.
5. Most likely root cause: a code path that acquires a connection but doesn't release it on an exception path. Fix with try-with-resources."
