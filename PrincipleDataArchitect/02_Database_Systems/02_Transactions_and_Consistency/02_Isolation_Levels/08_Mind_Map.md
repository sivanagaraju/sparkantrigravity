# Isolation Levels — Mind Map

> One-page scannable reference. Use for quick recall before interviews or when choosing isolation levels in production.

---

## Visual Mind Map

```mermaid
mindmap
  root((Isolation Levels))
    Read Uncommitted
      Dirty reads allowed
      Almost never used
      PostgreSQL silently upgrades to RC
      SQL Server only practical user
    Read Committed
      PostgreSQL & Oracle default
      Fresh snapshot per statement
      Non-repeatable reads possible
      Phantom reads possible
      95% of OLTP workloads belong here
    Repeatable Read
      MySQL InnoDB default
      Frozen snapshot for entire transaction
      PostgreSQL RR = Snapshot Isolation
        Prevents phantoms via snapshot
        No gap locks
        Allows inserts by other txns
      MySQL RR = Snapshot + Gap Locks
        Prevents phantoms via gap locks
        Pessimistic: blocks inserts
        Deadlock risk under load
      Write skew still possible
    Serializable
      Prevents ALL anomalies
      PostgreSQL: SSI optimistic
        SIREAD locks track reads
        RW-conflict graph
        Abort at commit time
        15-20% overhead vs RC
      MySQL & SQL Server: 2PL pessimistic
        Shared + exclusive locks
        Readers block writers
        50%+ overhead
        Deadlock risk
      MUST implement retry logic
    Key Anomalies
      Dirty Read
        See uncommitted data
        Only at Read Uncommitted
      Non-Repeatable Read
        Re-read returns different value
        At Read Committed
      Phantom Read
        New rows appear in range
        At RC and sometimes RR
      Write Skew
        Decisions on stale overlapping data
        At RC and RR
        The subtle Principal-level anomaly
    Cross-Engine Differences
      Same SQL name ≠ same behavior
      PostgreSQL RR ≠ MySQL RR
      PostgreSQL SER uses SSI
      MySQL SER uses 2PL + gap locks
      Oracle has no true Serializable
```

---

## Decision Cheat Sheet

```text
┌─────────────────────────────────────────────────────────┐
│              ISOLATION LEVEL SELECTOR                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Q: Does the operation modify financial/critical data?  │
│  └─ YES → Q: Can the app handle retries?                │
│           └─ YES → SERIALIZABLE (with retry logic)      │
│           └─ NO  → REPEATABLE READ + SELECT FOR UPDATE  │
│  └─ NO  → Q: Does it need a consistent snapshot?        │
│           └─ YES → REPEATABLE READ                      │
│           └─ NO  → READ COMMITTED (default, use this)   │
│                                                         │
│  NEVER USE: Read Uncommitted                            │
│  NEVER USE: Serializable without retry logic            │
│  NEVER USE: Long transactions at RR (blocks VACUUM)     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Quick-Reference: Anomaly Prevention

| Level | Dirty | Non-Repeatable | Phantom | Write Skew | Performance |
|---|---|---|---|---|---|
| **RU** | ❌ | ❌ | ❌ | ❌ | ~100% |
| **RC** | ✅ | ❌ | ❌ | ❌ | ~95% |
| **RR** | ✅ | ✅ | ✅ (PG) / ✅ (MySQL) | ❌ | ~85% |
| **SER** | ✅ | ✅ | ✅ | ✅ | ~80% (SSI) / ~50% (2PL) |

---

## Links

| File | What It Covers |
|---|---|
| [01_Concept_Overview.md](./01_Concept_Overview.md) | Definitions, comparison matrix, write skew example |
| [02_How_It_Works.md](./02_How_It_Works.md) | MVCC, 2PL, SSI internals, visibility algorithms |
| [03_Hands_On_Examples.md](./03_Hands_On_Examples.md) | Runnable SQL to prove each anomaly |
| [04_Real_World_Scenarios.md](./04_Real_World_Scenarios.md) | Coinbase, Uber, GitHub, Shopify, Netflix war stories |
| [05_Pitfalls_And_Anti_Patterns.md](./05_Pitfalls_And_Anti_Patterns.md) | 6 anti-patterns with detection and fixes |
| [06_Interview_Angle.md](./06_Interview_Angle.md) | Q&A frameworks, follow-up probes, whiteboard exercise |
| [07_Further_Reading.md](./07_Further_Reading.md) | Papers, books, engine docs, monitoring tools |
