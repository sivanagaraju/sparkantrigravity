# MVCC Internals — How It Works

> Two fundamentally different architectural approaches to MVCC dominate the industry: PostgreSQL's Append-Only Heap, and MySQL/Oracle's In-Place Updates with Undo Logs.

---

## Architecture 1: The Append-Only Heap (PostgreSQL)

In PostgreSQL, every `UPDATE` is physically executed as a `DELETE` followed by an `INSERT`. The new row version and the old row version live side-by-side in the main table heap.

### PostgreSQL Tuple Header Anatomy
Every row (tuple) in a Postgres table has a 23-byte header containing MVCC routing info:
- `t_xmin`: The Transaction ID (TXID) that inserted this version.
- `t_xmax`: The TXID that deleted or updated this version (0 if it is the current, active version).
- `t_ctid`: A physical pointer (Block Number + Offset) to the newest version of this row.

### The Visibility Rules (Simplified)
When Transaction $T_r$ (with snapshot $S$) reads a row:
1. Is `xmin` uncommitted? → **Invisible** (Wait, unless $T_r$ created it).
2. Is `xmin` committed, but occurred *after* $S$ was taken? → **Invisible** (From the future).
3. Is `xmin` committed before $S$, AND `xmax` is 0 (not deleted)? → **Visible**.
4. Is `xmax` committed before $S$? → **Invisible** (It was deleted before I started).

```mermaid
flowchart TD
    subgraph "PostgreSQL: Append-Only MVCC"
        T1["Tuple v1<br/>xmin: 100<br/>xmax: 105<br/>ctid: ->v2<br/>DATA: 'A'"]
        T2["Tuple v2<br/>xmin: 105<br/>xmax: 112<br/>ctid: ->v3<br/>DATA: 'B'"]
        T3["Tuple v3<br/>xmin: 112<br/>xmax: 0<br/>ctid: self<br/>DATA: 'C'"]
        
        T1 -.->|"UPDATE by Tx 105"| T2
        T2 -.->|"UPDATE by Tx 112"| T3
    end
    
    R1["Reader (Snapshot 102)"] -->|"Reads v1"| T1
    R2["Reader (Snapshot 110)"] -->|"Reads v2"| T2
    R3["Reader (Snapshot 115)"] -->|"Reads v3"| T3
```

**Consequences**: 
1. The main table grows rapidly under high update workloads.
2. Background `VACUUM` processes are required to scavenge the main table for dead tuples whose `xmax` is older than all running transactions.
3. **Write Amplification**: Updating one column in a 30-column table duplicates all 30 columns into a new physical location.
4. **Secondary Index Update**: Because the new tuple is at a new physical location (`ctid`), *every secondary index* must be updated to point to the new location, even if indexed columns weren't changed (partially mitigated by HOT - Heap Only Tuples).

---

## Architecture 2: In-Place Update with Undo Logs (MySQL InnoDB / Oracle)

In MySQL/InnoDB and Oracle, data is stored in clustered index (B-Tree) leaf nodes. Because moving data in a B-Tree is expensive, `UPDATE` statements modify the row **in place**. 

Before modifying the row, the engine copies the old version of the row (or just the diff) into a separate, dedicated storage area called the **Undo Log** (or Rollback Segment).

### Undo Log Pointer Anatomy
- `DB_TRX_ID`: The TXID of the last transaction to modify this row.
- `DB_ROLL_PTR`: A physical pointer to the previous version of this row stored inside the Undo Log.

```mermaid
flowchart LR
    subgraph "InnoDB Main Table (Clustered Index)"
        L["Latest Version<br/>TX: 112<br/>Roll_Ptr: ->Undo<br/>DATA: 'C'"]
    end
    
    subgraph "Undo Logs (Rollback Segments)"
        U1["Undo Record v2<br/>TX: 105<br/>Roll_Ptr: ->Undo<br/>DATA: 'B'"]
        U2["Undo Record v1<br/>TX: 100<br/>Roll_Ptr: NULL<br/>DATA: 'A'"]
    end
    
    L -->|"Follow ptr to reconstruct past"| U1
    U1 -->|"Follow ptr"| U2
    
    R1["Reader (Snapshot 102)"] -->|"Sees TX 112 is too new.<br/>Follows pointers<br/>until finding TX 100."| U2
    R2["Reader (Snapshot 115)"] -->|"Reads in-place"| L
```

**Consequences**:
1. The main table stays compact. No dead tuples accumulate in the primary file structure.
2. Write Amplification is vastly lower for updates. Secondary indexes usually don't need updating because the primary key (the physical location mapping) didn't change.
3. Reading historical versions is slow (you must reconstruct the row incrementally by walking the undo log chain).
4. Background `Purge` threads clean up the Undo Log, not the main tables.

---

## Sequence Diagram: Read-Write Conflict Resolution

This demonstrates exactly how MVCC provides lock-free concurrency.

```mermaid
sequenceDiagram
    participant R as Reader (TX 200)
    participant DB as Storage Engine
    participant W as Writer (TX 201)
    
    R->>DB: BEGIN. Get Snapshot (XID: 200, Active: []).
    W->>DB: BEGIN. Get Snapshot (XID: 201, Active: [200]).
    
    R->>DB: SELECT data FROM user WHERE id=1
    DB-->>R: Returns (Version A, xmin=150)
    
    W->>DB: UPDATE user SET data='B' WHERE id=1
    Note over DB: Writer creates Version B (xmin=201, xmax=0).<br/>Updates Version A (xmax=201).
    DB-->>W: UPDATE successful
    
    R->>DB: SELECT data FROM user WHERE id=1
    Note over DB: Evaluates Version B: xmin=201 > snapshot 200. Invisible.<br/>Evaluates Version A: xmin=150 < snapshot 200, xmax=201 > snapshot. Visible.
    DB-->>R: Returns (Version A) -- STILL SEES OLD DATA!
    
    W->>DB: COMMIT
    
    R->>DB: SELECT data FROM user WHERE id=1
    Note over DB: Even though TX 201 committed, Reader's <br/>snapshot is frozen at TX 200.
    DB-->>R: Returns (Version A)
```

---

## State Machine: Row Version Lifecycle (PostgreSQL)

How a tuple transitions from creation to garbage collection.

```mermaid
stateDiagram-v2
    [*] --> Inserted: INSERT (xmin=current_xid, xmax=0)
    
    Inserted --> Live: Transaction COMMITS
    Inserted --> Dead: Transaction ROLLS BACK
    
    Live --> Updated: UPDATE / DELETE by new Tx
    Updated --> Obsolete: New Tx COMMITS
    Updated --> Live: New Tx ROLLS BACK
    
    Obsolete --> Dead: All snapshots older than the Update COMPLETES
    
    Dead --> Vacuumed: Background Auto-Vacuum runs
    Vacuumed --> Reclaimed: Space marked available in FSM (Free Space Map)
    Reclaimed --> Inserted: New data overwrites space
```

### The "Long-Running Transaction" Dilemma
Looking at the state machine, an `Obsolete` tuple cannot transition to `Dead` if *any* currently running transaction has a snapshot older than the transaction that obsoleted the row. 
If an analyst leaves a `SELECT` running over the weekend, vacuum *cannot* clean up any rows updated all weekend. The database will bloat massively.
