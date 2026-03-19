# Real-World Scenarios: Connection Pooling

## Case Study 1: The Kubernetes Connection Explosion

**The Problem:**
A fintech company deployed 80 microservice pods on Kubernetes, each running a Spring Boot app with HikariCP `maximumPoolSize = 20`. Total database connections: `80 × 20 = 1,600`. Their PostgreSQL instance had `max_connections = 200`. During peak traffic, pods could not acquire database connections. Error logs showed:
```
FATAL: sorry, too many clients already
```

**Root Cause:** Application-side pooling alone is insufficient in microservices. Each pod independently manages its pool, unaware of other pods. There is no global coordination.

**The Fix:**
1. Deployed PgBouncer as a sidecar container in each pod (alternative: a centralized PgBouncer deployment).
2. Set PgBouncer `max_db_connections = 3` per pod × 80 pods = 240 (still close; centralized is better).
3. Better approach: Deployed a centralized PgBouncer (2 instances for HA) with `max_db_connections = 100`.
4. Reduced HikariCP per-pod pool to `maximumPoolSize = 3` (since PgBouncer handles the multiplexing).

Result: PostgreSQL saw a maximum of 100 connections. Mean query latency dropped 40% due to reduced context switching in PostgreSQL.

## Case Study 2: Connection Leak Detective Work

**The Problem:**
An e-commerce API experienced intermittent failures: after operating normally for 6-8 hours, all requests started timing out with `connectionTimeout` errors from HikariCP. Restarting the application "fixed" it temporarily.

**Diagnosis:**
```yaml
# Enabled HikariCP leak detection
spring.datasource.hikari.leak-detection-threshold: 10000  # 10 seconds
```

After enabling, the log showed:
```
WARN  HikariPool - Connection leak detection triggered for connection com.zaxxer.hikari.pool.ProxyConnection@7e3f7, 
stack trace of borrowed location:
    at com.example.OrderService.processRefund(OrderService.java:142)
    at com.example.OrderController.handleRefund(OrderController.java:67)
```

**Root Cause:** The `processRefund` method had an early-return path that skipped the `connection.close()` call in the `finally` block. Each refund request leaked one connection. After 5 connections were leaked (HikariCP pool size = 5), the pool was exhausted.

**The Fix:** Wrapped the connection usage in a try-with-resources block:
```java
// Before (buggy)
Connection conn = dataSource.getConnection();
if (refundAmount <= 0) return; // LEAK: connection never returned
// ...
conn.close();

// After (correct)
try (Connection conn = dataSource.getConnection()) {
    if (refundAmount <= 0) return; // Connection auto-closed by try-with-resources
    // ...
}
```

## Case Study 3: PgBouncer Transaction Mode Breaking LISTEN/NOTIFY

**The Problem:**
A real-time notification system used PostgreSQL `LISTEN/NOTIFY` for event-driven updates. After migrating from direct PostgreSQL connections to PgBouncer in transaction mode, notifications stopped being received.

**Root Cause:** `LISTEN` is a session-level command. In transaction mode, after the `LISTEN` command's implicit transaction completes, PgBouncer reassigns the server connection. The next server connection assigned to the client has no `LISTEN` registered.

**The Fix:**
- Created a separate PgBouncer pool specifically for LISTEN/NOTIFY consumers in `session` mode:
```ini
[databases]
myapp = host=pg-primary.internal port=5432 dbname=production pool_mode=transaction
myapp_notify = host=pg-primary.internal port=5432 dbname=production pool_mode=session
```

- The notification consumer connects to `myapp_notify` (session mode); all other services use `myapp` (transaction mode).

## Case Study 4: The Optimal Pool Size Discovery

**The Problem:**
A team set their PostgreSQL `max_connections = 500` and HikariCP `maximumPoolSize = 100` "to handle future growth." Under load testing with 200 concurrent users, throughput was LOWER than with 50 concurrent users.

**The Experiment:**
They ran pgbench varying `max_connections`:

| max_connections | Throughput (TPS) | Avg Latency |
| :--- | :--- | :--- |
| 10 | 2,800 | 3.5ms |
| 20 | 4,200 | 4.7ms |
| 50 | 3,900 | 12.8ms |
| 100 | 3,100 | 32.1ms |
| 200 | 2,400 | 83.5ms |

**Result:** Peak throughput was at 20 connections (on a 4-core machine: `4 × 2 + 1 = 9`, so 20 is already generous). Beyond 20, lock contention and context switching **reduced** throughput. More connections does not mean more speed.
