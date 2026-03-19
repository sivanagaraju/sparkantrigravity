# Interview Angle: Replication Topologies

## How This Appears

Replication is one of the most frequently tested topics in Senior/Principal database and system design interviews. It surfaces in:
1. **System Design:** "Design a globally distributed user profile service." (Forces you to choose a replication topology.)
2. **Trade-off Analysis:** "Compare synchronous vs. asynchronous replication. When would you choose each?"
3. **Failure Scenarios:** "Your primary database just crashed. Walk me through what happens next."

## Sample Questions & Answer Frameworks

### Q1: "Explain the CAP theorem implications for database replication."

**Strong:** "CAP states you can have at most two of Consistency, Availability, and Partition tolerance. Since network partitions are inevitable in distributed systems, the real choice is between CP (consistent under partition—refuse writes when you can't confirm replication) and AP (available under partition—accept writes but risk divergence).

Synchronous replication is a CP choice: if the replica is unreachable, commits stall (sacrificing availability for consistency). Asynchronous replication is an AP choice: writes succeed regardless of replica state, but a primary failure may lose recent commits (sacrificing consistency for availability).

In practice, most production systems use async replication for performance and add operational safeguards (monitoring lag, automated failover) to minimize the consistency risk window."

### Q2: "Walk me through what happens when a PostgreSQL primary crashes during synchronous replication."

**Principal Answer:**
1. "The primary crashes mid-transaction or after WAL flush but before returning COMMIT OK.
2. The Patroni agent (or equivalent) detects the primary is unresponsive via its health check loop.
3. Patroni checks the replication state of all synchronous standbys via etcd/DCS. The standby with the highest `replay_lsn` is selected for promotion.
4. Patroni issues `pg_ctl promote` on the chosen standby. The standby replays any remaining WAL records and marks itself as the new primary.
5. Patroni updates the DCS with the new leader endpoint. Applications using Patroni-aware connection routing (or a proxy like HAProxy checking the Patroni REST API) discover the new primary within seconds.
6. The old primary, if it ever comes back, cannot rejoin as-is. It must be rebuilt as a new standby using `pg_rewind` (if timeline divergence is small) or a fresh `pg_basebackup`.
7. For RPO=0 with synchronous replication: zero transactions are lost because no COMMIT OK was returned until the sync standby acknowledged the WAL."

### Q3: "Your company wants to write to databases in both US and EU to minimize latency. How would you architect this?"

**Strong:** "The first question is whether the same rows are written in both regions. If yes, you need multi-master with conflict resolution—which I would strongly argue against for transactional data.

Instead, I would propose **geographic write partitioning**: EU users are assigned to the EU primary; US users to the US primary. Each primary replicates asynchronously to the other region for read availability. This eliminates write conflicts entirely.

For the rare case where a user needs to access data from the other region (e.g., a US customer looking up an order placed while traveling in Europe), we route that specific read to the originating region's primary, accepting the latency hit.

If true multi-region writes to the same data are mandatory—like a collaborative document editing system—I would use a purpose-built system (CRDTs, operational transformation) rather than database-level multi-master replication."

### Q4: "What is split-brain and how do you prevent it?"

**Strong:** "Split-brain occurs when both nodes in a primary-standby pair believe they are the primary and accept writes independently. This creates divergent data that is extremely difficult to reconcile.

Prevention requires a **fencing mechanism**—a way to guarantee that the old primary stops accepting writes before the new primary starts. Three approaches:
1. **STONITH (Shoot The Other Node In The Head):** A hardware watchdog on the old primary reboots the machine if it loses contact with the consensus store. Patroni supports this with `watchdog_mode = required`.
2. **Quorum-based consensus:** Use a 3-node etcd/ZooKeeper cluster. Promotion only happens if the new leader can reach a majority of consensus nodes.
3. **Network fencing:** Use an API call to the cloud provider to forcibly terminate or disconnect the old primary's network interface."
