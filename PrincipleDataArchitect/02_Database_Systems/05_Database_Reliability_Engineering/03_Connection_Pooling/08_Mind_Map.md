# 🧠 Mind Map – Connection Pooling

---
## How to Use This Mind Map
- **For Revision:** Remember the formula: optimal connections ≈ `(cores × 2) + spindles`. More is NOT better.
- **For Architecture:** Monolith = app pool only. Microservices = app pool + server-side pool (PgBouncer/ProxySQL).
- **For Debugging:** Connection timeouts → check for leaks. Slow queries → check pool size vs core count.

---
## 🔌 Why Pool?
- PostgreSQL: 1 OS process per connection (5-10 MB each).
- MySQL: 1 thread per connection.
- Context switching at 500+ connections destroys throughput.
- Pool amortizes: TCP handshake, TLS, auth, process fork.

---
## 🔌 Pool Modes
### Session
- 1:1 mapping: client session → backend connection.
- Full compatibility (temp tables, SET, LISTEN).
- Minimal pooling benefit.

### Transaction
- Connection assigned per-transaction only.
- Max multiplexing: 1000 clients → 50 backend.
- Breaks session-stateful features.

### Statement
- Per-statement assignment.
- Breaks multi-statement transactions.
- Almost never used.

---
## 🔌 Tool Comparison
### PgBouncer (PostgreSQL)
- Single-threaded, libevent.
- Very lightweight (~5 MB RAM).
- Pooling only—no query routing.

### ProxySQL (MySQL)
- Multi-threaded, C++.
- Pooling + query routing + caching + rewriting.
- Feature-rich but more complex.

### HikariCP (JVM)
- Application-side pool.
- ConcurrentBag + CAS for sub-μs acquisition.
- Thread-local connection affinity.

---
## 🔌 Optimal Pool Size
- Formula: `(cores × 2) + effective_spindle_count`
- 4-core server → 9-10 optimal
- 8-core server → 17-20 optimal
- Beyond this: throughput DECREASES

---
## 🔌 Anti-Pattern Checklist
- ❌ Pool size = max_connections (way too large).
- ❌ No leak detection (silent pool exhaustion).
- ❌ Session-stateful SQL with transaction pooling.
- ❌ No maxLifetime / server_lifetime (stale/dead connections).
- ❌ App pool only in microservices (connection explosion).
- ❌ No monitoring of PgBouncer cl_waiting metric.
