# Page Architecture — How It Works

> The internal anatomy of a database page: headers, line pointers, tuples, and free space management.

---

## PostgreSQL 8KB Page Layout (Detailed)

```
┌──────────────────────────────────────────────────────────┐
│ PAGE HEADER (24 bytes)                                    │
│ ┌───────────┬────────────┬──────────┬──────────────────┐ │
│ │ pd_lsn    │ pd_checksum│ pd_flags │ pd_lower/pd_upper│ │
│ │ (WAL pos) │ (CRC-16)   │          │ (free space ptrs)│ │
│ └───────────┴────────────┴──────────┴──────────────────┘ │
├──────────────────────────────────────────────────────────┤
│ LINE POINTERS (ItemIdData array, 4 bytes each)           │
│ ┌────┬────┬────┬────┬────┬────────────────────────────┐ │
│ │ LP1│ LP2│ LP3│ LP4│ LP5│  ...grows downward →       │ │
│ └────┴────┴────┴────┴────┴────────────────────────────┘ │
│                                                           │
│ ═══════════ FREE SPACE ════════════                      │
│ pd_lower ↓                                                │
│                                                           │
│ pd_upper ↑                                                │
│ ═══════════════════════════════════                       │
│                                                           │
│ TUPLE DATA (grows upward from bottom ↑)                  │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Tuple 5: [header 23B][null bitmap][user data]        │ │
│ │ Tuple 4: [header 23B][null bitmap][user data]        │ │
│ │ Tuple 3: [header 23B][null bitmap][user data]        │ │
│ │ Tuple 2: [header 23B][null bitmap][user data]        │ │
│ │ Tuple 1: [header 23B][null bitmap][user data]        │ │
│ └──────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────┤
│ SPECIAL SPACE (for B-Tree: sibling pointers)             │
└──────────────────────────────────────────────────────────┘
```

**Key mechanics**:
- `pd_lower` points to the end of line pointers (grows down)
- `pd_upper` points to the start of tuple data (grows up)
- Free space = `pd_upper - pd_lower`
- When free space runs out → page is full → insert goes to next page

## HLD — Buffer Manager and Page Flow

```mermaid
flowchart TB
    subgraph "Query Executor"
        Q["SELECT * FROM users WHERE id=42"]
    end
    
    subgraph "Buffer Manager"
        BT["Buffer Tag<br/>(relation_id, fork_type, block_number)"]
        HT["Hash Table<br/>(tag → buffer_id)"]
        BP["Buffer Pool<br/>(shared_buffers = 1024 pages)"]
    end
    
    subgraph "Storage Manager"
        OS["OS Page Cache"]
        DISK["Data File<br/>(8KB pages on disk)"]
    end
    
    Q -->|"1. Request page 5 of users table"| BT
    BT -->|"2. Lookup in hash table"| HT
    HT -->|"3a. HIT: return buffer"| BP
    HT -->|"3b. MISS: evict (clock sweep) + read from disk"| OS --> DISK
    DISK -->|"4. Copy page into buffer pool"| BP
    BP -->|"5. Return page to executor"| Q
```

## Sequence Diagram — Page Read Path

```mermaid
sequenceDiagram
    participant Exec as Query Executor
    participant BM as Buffer Manager
    participant Hash as Hash Table
    participant Pool as Buffer Pool (RAM)
    participant Disk as Data File (Disk)
    
    Exec->>BM: GetPage(users, block=5)
    BM->>Hash: Lookup(rel=users, blk=5)
    
    alt Page in Buffer Pool (HIT)
        Hash-->>BM: buffer_id=42
        BM->>Pool: Pin buffer 42, increment ref count
        Pool-->>Exec: Return page pointer
    else Page NOT in Buffer Pool (MISS)
        Hash-->>BM: NOT FOUND
        BM->>Pool: Find victim buffer (clock sweep)
        Pool-->>BM: buffer_id=99 (unpinned, usage_count=0)
        BM->>BM: If victim dirty → flush to disk first
        BM->>Disk: Read 8KB from file offset (5 × 8192)
        Disk-->>Pool: Copy 8KB into buffer 99
        BM->>Hash: Insert(rel=users, blk=5 → buffer=99)
        Pool-->>Exec: Return page pointer
    end
```

## Tuple Header — MVCC Versioning (23 bytes)

```
┌──────────────────────────────────────────────────┐
│ HeapTupleHeaderData (23 bytes)                    │
├───────────┬──────────────────────────────────────┤
│ t_xmin    │ Transaction ID that INSERT'd this row │
│ (4 bytes) │ Visibility: is xmin committed?        │
├───────────┼──────────────────────────────────────┤
│ t_xmax    │ Transaction ID that DELETE'd/UPDATE'd │
│ (4 bytes) │ 0 = not deleted; >0 = check CLOG     │
├───────────┼──────────────────────────────────────┤
│ t_cid     │ Command ID within transaction         │
│ (4 bytes) │                                       │
├───────────┼──────────────────────────────────────┤
│ t_ctid    │ Current tuple's TID (block, offset)   │
│ (6 bytes) │ Points to newer version after UPDATE  │
├───────────┼──────────────────────────────────────┤
│ t_infomask│ Status bits (committed, aborted, etc) │
│ (2+2+1 B) │ HEAP_XMIN_COMMITTED, HEAP_UPDATED... │
└───────────┴──────────────────────────────────────┘
```

## InnoDB 16KB Page Layout (Comparison)

```mermaid
flowchart TB
    subgraph "InnoDB 16KB Page"
        FH["File Header (38B)<br/>checksum, page_no, prev/next"]
        PH["Page Header (56B)<br/>record count, free space ptr"]
        INF["Infimum Record<br/>(smallest possible key)"]
        REC["User Records<br/>(clustered by PK)"]
        SUP["Supremum Record<br/>(largest possible key)"]
        FD["Free Space"]
        PD["Page Directory<br/>(sparse index to records)"]
        FT["File Trailer (8B)<br/>checksum verification"]
    end
    
    FH --> PH --> INF --> REC --> SUP --> FD --> PD --> FT
```

**Key difference from PostgreSQL**: InnoDB pages store records ordered by primary key (clustered index). PostgreSQL heap pages store tuples in insertion order (unordered).

## State Machine — Page Lifecycle

```mermaid
stateDiagram-v2
    [*] --> EMPTY: Page allocated
    EMPTY --> PARTIAL: First tuple inserted
    PARTIAL --> PARTIAL: More tuples inserted
    PARTIAL --> FULL: pd_upper meets pd_lower
    FULL --> PARTIAL: VACUUM removes dead tuples
    PARTIAL --> EMPTY: All tuples deleted + VACUUM FULL
    
    note right of FULL: New inserts go to\\nnext page via FSM
```
