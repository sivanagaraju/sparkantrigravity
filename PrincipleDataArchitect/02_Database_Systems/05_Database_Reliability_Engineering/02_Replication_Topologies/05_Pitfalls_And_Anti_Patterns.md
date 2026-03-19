# Pitfalls & Anti-Patterns: Replication Topologies

## 1. Replication Slot Without Monitoring = Disk Full

**The Trap:** A replication slot tells the primary "do not recycle any WAL that I haven't consumed." If the replica disconnects (network failure, maintenance, forgotten test instance), the primary retains WAL indefinitely. On a write-heavy system generating 1 GB/hour of WAL, a 48-hour disconnect accumulates 48 GB of unreclaimable WAL, eventually filling the disk and crashing the primary.

**The Fix:**
```sql
-- Monitor replication slots regularly
SELECT slot_name, active, 
       pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) AS retained_bytes
FROM pg_replication_slots;

-- Set maximum WAL retention for slots (PostgreSQL 13+)
ALTER SYSTEM SET max_slot_wal_keep_size = '10GB';
-- Slot will be invalidated if it falls more than 10 GB behind
```

## 2. Reading from Replica Without Understanding Staleness

**The Trap:** Applications read from async replicas and show stale data to users. A user places an order (write to primary), is redirected to a confirmation page (read from replica), and the order is "missing" because the replica hasn't replayed the WAL yet.

**The Fix:** Route reads that must reflect recent writes to the primary. For session-scoped consistency, track the last write LSN and only query the replica if its `replay_lsn >= last_write_lsn`.

```python
# Pseudo-code: Read-Your-Writes consistency
def read_order(order_id, last_write_lsn):
    replica_lsn = query_replica("SELECT pg_last_wal_replay_lsn()")
    if replica_lsn >= last_write_lsn:
        return query_replica(f"SELECT * FROM orders WHERE id = {order_id}")
    else:
        return query_primary(f"SELECT * FROM orders WHERE id = {order_id}")
```

## 3. Synchronous Replication Without Timeout

**The Trap:** Synchronous replication with a remote standby. The network link to the standby goes down. Every COMMIT on the primary now hangs indefinitely—the primary waits for synchronous acknowledgment that will never arrive. The entire application freezes.

**The Fix:** Never use synchronous replication to a single remote standby without safeguards:
- Use `synchronous_standby_names = 'ANY 1 (local_standby, remote_standby)'` so commits succeed if ANY one standby acknowledges.
- Set `statement_timeout` to prevent indefinite hangs.
- Use Patroni's `synchronous_mode_strict = false` to allow fallback to async when no sync standby is available.

## 4. Multi-Master Without Conflict Avoidance

**The Trap:** Deploying multi-master replication ("because we want writes in both data centers") without partitioning the write domain. Both masters accept writes to the same tables. Clock-based conflict resolution (Last Write Wins) silently discards valid updates when clocks are skewed by even a few milliseconds.

**The Rule:** If you must use multi-master, partition writes by geography or tenant:
- US users write to the US master; EU users write to the EU master.
- Each master replicates to the other for read availability.
- No row is ever written by both masters simultaneously → zero conflicts.

## 5. Not Testing Failover

**The Trap:** Setting up replication and failover tooling (Patroni, pg_auto_failover) but never testing an actual failover in production. When the primary fails for real:
- The replica was secretly lagging by 2 hours because nobody was monitoring.
- The application connection pool has stale primary addresses cached.
- The DNS TTL is 300 seconds, so clients keep connecting to the dead primary for 5 minutes.

**The Fix:** Schedule monthly controlled failover drills. Verify: replica lag is acceptable, applications reconnect within SLA, data integrity post-failover, and rollback (fail-back) works.

## Decision Matrix: Replication Choices

| Question | If Yes → | If No → |
| :--- | :--- | :--- |
| Can you tolerate ANY data loss? | Async replication | Synchronous replication |
| Do you need writes in multiple regions? | Multi-master (with conflict avoidance!) | Single-leader + cross-region replicas |
| Do you need selective table replication? | Logical replication | Physical replication |
| Do you need cross-version replication? | Logical replication | Physical replication |
| Is read scalability the primary goal? | Add async replicas | Optimize the primary |
