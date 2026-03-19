# Further Reading: Replication Topologies

## Essential Sources

*   **Designing Data-Intensive Applications (DDIA) — Chapter 5: Replication**
    *   *Author:* Martin Kleppmann
    *   *Why:* The definitive treatment of leaders, followers, multi-leader, and leaderless replication. Covers consistency models, conflict resolution, and quorum-based approaches with cross-database examples.

*   **PostgreSQL Documentation: High Availability, Load Balancing, and Replication**
    *   *Source:* postgresql.org/docs/current/high-availability.html
    *   *Why:* The official reference for streaming replication, logical replication, synchronous commit levels, and replication slots.

*   **Patroni Documentation**
    *   *Source:* patroni.readthedocs.io
    *   *Why:* The de facto standard for PostgreSQL automated failover. Understanding Patroni is essential for any production PostgreSQL deployment.

## Books

*   **Database Internals — Alex Petrov (Part II: Distributed Systems)**
    *   *Why:* Deep coverage of failure detection, leader election, consensus algorithms (Raft, Paxos), and replication protocols from a systems perspective.

## Tools

*   **Patroni** — Automated PostgreSQL failover with etcd/ZooKeeper/Consul.
*   **pg_auto_failover** — Simpler alternative to Patroni for smaller deployments.
*   **Orchestrator** — GitHub's tool for MySQL replication topology discovery and failover.
*   **pg_rewind** — Resynchronize a diverged primary to rejoin as a standby without a full base backup.
*   **pgEdge / Spock / BDR** — Multi-master logical replication for PostgreSQL.

## Cross-References

*   **WAL and Durability:** Replication is fundamentally WAL shipping. Understanding WAL mechanics (LSN, checkpoints, fsync) is prerequisite.
*   **Connection Pooling:** After failover, connection pools must detect the new primary and re-route. PgBouncer/Patroni integration is critical.
*   **Backup & Recovery:** Replicas are NOT backups. A dropped table replicates to the replica. Backups with WAL archiving are still required.
