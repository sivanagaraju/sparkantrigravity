# Spanner, CockroachDB, TiDB — Mind Map

> **Principal's Perspective:** A quick visual reference mapping the core structural differences, problem solving tools, and architectural tradeoffs inherent to Distributed SQL.

---

## Visual Architecture Map

```mermaid
mindmap
  root((Distributed SQL))
    The Foundational Layer
      LSM Tree (RocksDB/Pebble/TiKV)
      Strictly Sorted KV Space
      Separated into 64MB "Ranges"
    Replication/Resilience
      Consensus via Raft or Paxos
      Multi-Raft Architecture
      Quorum ACKs for Commit
    Transaction Coordination (2PC)
      Write Intents
      Centralized Transaction Record
      Optimistic Concurrency (OCC)
      Serialization Failures & Retries
    Global Clock Sync (The Hard Problem)
      Spanner
        TrueTime (GPS, Atomic Clocks)
        Bounded Error (e.g. 7ms)
        Commit Wait Penalty
      CockroachDB
        Hybrid Logical Clocks (HLC)
        NTP + Logical Counter
        Max Offset Limit (500ms)
        Txn Restarts on uncertainty
      TiDB
        Timestamp Oracle (TSO)
        Centralized Placement Driver
        Zero clock drift
        Network bottleneck
    TiDB Unique Feature: HTAP
      TiKV for point lookups
      TiFlash for Columnar Scans
      Raft Learner syncing
      Smart SQL routing
    Major Pitfalls
      Latency Speed-of-Light limits
      Sequential ID Hotspotting
      Massive N+1 ORM Queries
      Cross-Continent 2PC locks
    Performance Hacks
      Follower Reads (Stale)
      Geo-Partitioning (Data Domicile)
      Interleaved Tables (Parent-Child)
```

---

## Quick Comparison Matrix

| Aspect                 | Spanner           | CockroachDB      | TiDB               |
|:-----------------------|:-----------------:|:----------------:|:------------------:|
| **Language Compat**    | PostgreSQL / Spanner | PostgreSQL | MySQL             |
| **Primary Clock**      | Hardware (TrueTime) | Software (HLC) | Central Network (TSO) |
| **Transaction Method** | 2PC + Paxos       | 2PC + Multi-Raft | 2PC + Multi-Raft  |
| **Deep Analytics**     | BigQuery (Export)   | No               | Native (TiFlash) |
| **Open Source**        | No                  | BSL (Source Available) | Apache 2.0  |

---

## The "How Does a Write Happen?" Flow

1. **Client connects to node (Gateway).**
2. Gateway checks SQL -> Maps to KV keys.
3. Gateway opens Transaction Record (Pending).
4. Gateway determines which internal Ranges map to the Keys.
5. Gateway asks Cluster: "Who is the Raft Leaseholder for Range Z?"
6. Gateway sends KV Write Intents to the Leaseholder.
7. Leaseholder writes payload to Raft log, replicates exactly a subset to quorum.
8. Quorum ACKs.
9. Gateway updates Transaction Record (Committed).
10. System responds to Client (Success).
11. Async: Intents are lazily cleaned up to normal committed values in the LSM.
