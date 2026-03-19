# Pitfalls & Anti-Patterns: Connection Pooling

## 1. Setting Pool Size = max_connections

**The Trap:** PostgreSQL has `max_connections = 200`, so the team sets PgBouncer `default_pool_size = 200`. Now PgBouncer can open 200 backend connections, and PostgreSQL is handling 200 concurrent queries. On a 4-core machine, this is 50x oversubscribed—performance collapses from lock contention and scheduler thrashing.

**The Rule:** The database pool size should be `(cores × 2) + effective_spindle_count`, NOT `max_connections`. Set `max_connections` slightly higher than the pool size (to allow admin connections, monitoring, replication slots), but the pool should be the constraint.

## 2. No Connection Leak Detection

**The Trap:** Not enabling leak detection in the application pool. A single code path that forgets to return a connection will silently exhaust the pool. The failure manifests as "random" timeouts hours or days later, making diagnosis difficult.

**The Fix:** Always set `leak-detection-threshold` in HikariCP (e.g., 30 seconds). Always use `try-with-resources` in Java, `with` statement in Python, or `defer conn.Close()` in Go.

## 3. Session-Stateful Code with Transaction Pooling

**The Trap:** Using PgBouncer in transaction mode while the application uses:
- `SET search_path = tenant_schema;` (resets when connection changes)
- Temporary tables (invisible on next connection)
- `PREPARE` / `EXECUTE` named prepared statements
- Advisory locks (held on wrong connection)

**The Fix:** Audit application SQL for session-state dependencies. Either:
1. Eliminate session-stateful SQL (prefix table names with schema, avoid temp tables), or
2. Use `session` pool mode for those specific consumers, or
3. Use PgBouncer 1.21+ `max_prepared_statements` support for prepared statement tracking.

## 4. Ignoring maxLifetime / server_lifetime

**The Trap:** Connections in the pool grow old without recycling. Eventually, a firewall between the app and the database silently drops the TCP connection (common: AWS NLB idle timeout = 350s). The pool holds a dead connection and hands it to the application, which gets a "connection reset" error.

**The Fix:** Set `maxLifetime` (HikariCP) or `server_lifetime` (PgBouncer) to a value SHORTER than the network device's idle timeout. Common values: 1800 seconds (30 minutes). Enable `pool_pre_ping = True` (SQLAlchemy) or `connection-test-query` (HikariCP) to validate connections before use.

## 5. Application Pool + No Server-Side Pool in Microservices

**The Trap:** 50 microservice instances each open 20 connections to PostgreSQL directly. Total: 1000 connections. PostgreSQL is overwhelmed. Adding more microservice instances (autoscaling) makes it worse—each new pod opens 20 MORE connections.

**The Architecture:** Always use a server-side pooler (PgBouncer / ProxySQL) when you have >5 application instances. The server-side pooler is the single point of control for database connection count.

## Decision Matrix: Pool Configuration

| Scenario | Server-Side Pool | App Pool Size | Pool Mode | Key Settings |
| :--- | :--- | :--- | :--- | :--- |
| **Monolith (1-3 instances)** | Optional | `(cores × 2) + 1` | N/A | `maxLifetime`, `leakDetection` |
| **Microservices (10+ pods)** | Required (PgBouncer) | 3-5 per pod | Transaction | `max_db_connections` on PgBouncer |
| **LISTEN/NOTIFY consumers** | PgBouncer session pool | 1-2 per consumer | Session | Separate pool for these consumers |
| **Serverless / Lambda** | Required (RDS Proxy / PgBouncer) | 1 per invocation | Transaction | Short `server_idle_timeout` |
