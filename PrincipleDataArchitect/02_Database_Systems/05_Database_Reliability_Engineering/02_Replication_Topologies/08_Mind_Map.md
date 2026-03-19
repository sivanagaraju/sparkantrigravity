# 🧠 Mind Map – Replication Topologies

---
## How to Use This Mind Map
- **For Revision:** Trace the flow: Primary writes WAL → WAL shipped to replica → Replica replays WAL.
- **For Design Decisions:** Start with single-leader async. Upgrade to sync only for zero-loss requirements. Avoid multi-master unless you can partition writes.
- **For Interviews:** Draw the replication architecture for any system design question. Always address: RPO, RTO, consistency model, and failover mechanism.

---
## 🔄 Physical vs. Logical Replication
### Physical
- Ships raw WAL bytes.
- Exact binary clone of primary.
- Same major version required.
- Read-only replica.

### Logical
- Decodes WAL → INSERT/UPDATE/DELETE events.
- Per-table granularity.
- Cross-version compatible.
- Can have different indexes, schemas.
- DDL NOT replicated automatically.

---
## 🔄 Consistency Spectrum
### Synchronous (RPO = 0)
- Primary waits for replica confirmation.
- Zero data loss guarantee.
- Higher commit latency (network RTT added).
- Risk: replica failure stalls all writes.

### Asynchronous (RPO > 0)
- Primary commits without waiting.
- Lowest latency.
- Data loss window = replica lag (typically < 1 second).
- Default for most deployments.

### Semi-Synchronous
- Primary waits for receipt (not application).
- Balance between the two.
- MySQL's semi-sync plugin.

---
## 🔄 Topology Patterns
### Single-Leader (Most Common)
- One primary, N read replicas.
- Simple, well-understood.
- Automated failover with Patroni / Orchestrator.

### Cascading
- Primary → Relay Replica → N additional replicas.
- Reduces primary's network/CPU load.
- Increases staleness for downstream replicas.

### Multi-Leader
- Multiple nodes accept writes.
- Requires conflict resolution (LWW, version vectors, app-level).
- Avoid unless you can partition writes by geography.

---
## 🔄 Failure Handling
### Failover
- Patroni: Health check loop → detect primary failure → promote standby via DCS.
- `maximum_lag_on_failover`: Only promote standbys within acceptable lag.
- `pg_rewind`: Resync old primary as new standby.

### Split-Brain Prevention
- STONITH: Hardware watchdog terminates old primary.
- Quorum: 3-node consensus (etcd/ZK/Consul).
- Network fencing: Cloud API to isolate old primary.

---
## 🔄 Anti-Pattern Checklist
- ❌ Replication slots without monitoring (disk full risk).
- ❌ Reading from replica without understanding staleness.
- ❌ Sync replication to a single remote standby (availability risk).
- ❌ Multi-master without write partitioning (conflict hell).
- ❌ Never testing failover until a real incident.
- ❌ Assuming replicas are backups (DROP TABLE replicates too).
