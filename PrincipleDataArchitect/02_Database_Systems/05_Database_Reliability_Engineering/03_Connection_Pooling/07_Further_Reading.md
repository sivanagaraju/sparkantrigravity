# Further Reading: Connection Pooling

## Essential Sources

*   **"About Pool Sizing" — HikariCP Wiki**
    *   *Source:* github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing
    *   *Why:* The definitive explanation of why smaller pool sizes outperform larger ones. Includes the `(cores × 2) + effective_spindle_count` formula and the PostgreSQL benchmark data that proves it.

*   **PgBouncer Documentation**
    *   *Source:* pgbouncer.org
    *   *Why:* Official reference for all PgBouncer configuration parameters, pool modes, and authentication methods.

*   **ProxySQL Documentation**
    *   *Source:* proxysql.com/documentation
    *   *Why:* Comprehensive guide to ProxySQL's query routing, caching, rewriting, and hostgroup management.

## Books

*   **PostgreSQL 14 Internals — Egor Rogov (Chapter: Processes and Memory)**
    *   *Why:* Explains PostgreSQL's process-per-connection architecture, shared buffers, and why connection count directly impacts memory and CPU.

## Tools

*   **PgBouncer** — Lightweight PostgreSQL connection pooler.
*   **Pgpool-II** — Connection pooling + load balancing + query caching for PostgreSQL.
*   **ProxySQL** — MySQL/MariaDB proxy with connection pooling, query routing, and caching.
*   **HikariCP** — Ultra-fast JVM connection pool (Spring Boot default).
*   **Amazon RDS Proxy** — Managed connection pooler for RDS/Aurora (handles serverless/Lambda connection storms).
*   **pgbench** — PostgreSQL benchmarking tool for testing pool size impact on throughput.

## Cross-References

*   **WAL and Durability:** Connection pooling does not affect WAL behavior, but pool sizing affects how many concurrent transactions generate WAL simultaneously.
*   **Replication Topologies:** After failover, connection pools must detect the new primary. PgBouncer + Patroni integration is critical.
*   **Upgrades and Migrations:** Connection poolers can facilitate zero-downtime migrations by draining connections from the old database and redirecting to the new one.
