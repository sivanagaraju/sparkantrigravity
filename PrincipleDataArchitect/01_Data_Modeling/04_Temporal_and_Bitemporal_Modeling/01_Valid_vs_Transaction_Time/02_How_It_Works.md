# Valid Time vs Transaction Time — How It Works (Deep Internals)

> HLD, ER diagrams, DDL table structures, sequence diagrams, state machines, and data flow.

---

## High-Level Design — Temporal Architecture

```mermaid
flowchart TB
    subgraph "Source Systems"
        OLTP["OLTP (Oracle, Postgres)"]
        API["External APIs"]
        FILE["Flat Files / Late Corrections"]
    end
    
    subgraph "Ingestion"
        CDC["CDC Stream<br/>(Debezium / Golden Gate)"]
        BATCH["Batch Loader"]
    end
    
    subgraph "Bitemporal Layer"
        BT["Bitemporal Table<br/>valid_from, valid_to<br/>txn_from, txn_to"]
        IDX["Temporal Indexes<br/>(GiST range, B-tree composite)"]
    end
    
    subgraph "Query Patterns"
        CUR["Current State<br/>WHERE is_current = true"]
        ASOF["As-Of Query<br/>FOR SYSTEM_TIME AS OF"]
        RANGE["Range Query<br/>valid_from BETWEEN"]
        CROSS["Cross-Time Query<br/>Both axes"]
    end
    
    OLTP --> CDC --> BT
    API --> BATCH --> BT
    FILE --> BATCH
    BT --> IDX
    BT --> CUR
    BT --> ASOF
    BT --> RANGE
    BT --> CROSS
    
    style BT fill:#FF6B35,color:#fff
```

---

## ER Diagram — Bitemporal Employee Record

```mermaid
erDiagram
    EMPLOYEE_BITEMPORAL {
        bigint employee_sk PK
        int employee_id "Natural Key"
        varchar employee_name
        varchar department
        varchar job_title
        decimal salary
        varchar office_location
        date valid_from "When true in reality"
        date valid_to "When no longer true in reality"
        timestamp txn_from "When DB recorded this version"
        timestamp txn_to "When DB superseded this version"
        boolean is_current_valid "Latest valid-time version"
        boolean is_current_txn "Latest transaction-time version"
    }
    
    DEPARTMENT_BITEMPORAL {
        bigint dept_sk PK
        int dept_id "Natural Key"
        varchar dept_name
        varchar cost_center
        varchar vp_name
        date valid_from
        date valid_to
        timestamp txn_from
        timestamp txn_to
    }
    
    EMPLOYEE_BITEMPORAL }o--|| DEPARTMENT_BITEMPORAL : "department (temporal FK)"
```

---

## Table Structures

### Bitemporal Fact Table — Trade Ledger

```sql
-- ============================================================
-- Bitemporal trade ledger
-- Two independent time axes: valid time (when the trade occurred)
-- and transaction time (when the system recorded it)
-- ============================================================

CREATE TABLE trade_ledger_bitemporal (
    trade_version_sk    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    
    -- Natural key
    trade_id            VARCHAR(50)    NOT NULL,
    
    -- Business attributes
    instrument_id       VARCHAR(20)    NOT NULL,
    counterparty_id     INT            NOT NULL,
    trade_type          VARCHAR(10)    NOT NULL,  -- BUY, SELL, SHORT
    quantity            DECIMAL(18,4)  NOT NULL,
    price               DECIMAL(18,6)  NOT NULL,
    notional_value      DECIMAL(20,2)  NOT NULL,
    currency            CHAR(3)        NOT NULL,
    trader_id           INT            NOT NULL,
    desk_id             INT            NOT NULL,
    
    -- VALID TIME: when was this trade effective in reality?
    valid_from          DATE           NOT NULL,
    valid_to            DATE           NOT NULL DEFAULT '9999-12-31',
    
    -- TRANSACTION TIME: when did the system learn about this version?
    txn_from            TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    txn_to              TIMESTAMP      NOT NULL DEFAULT '9999-12-31 23:59:59',
    
    -- Convenience flags
    is_current_valid    BOOLEAN GENERATED ALWAYS AS (valid_to = '9999-12-31') STORED,
    is_current_txn      BOOLEAN GENERATED ALWAYS AS (txn_to = '9999-12-31 23:59:59') STORED,
    
    -- Metadata
    change_reason       VARCHAR(100),  -- INITIAL, CORRECTION, AMENDMENT, CANCELLATION
    source_system       VARCHAR(50),
    loaded_by           VARCHAR(100)
);

-- Composite index for bitemporal lookups
CREATE INDEX idx_trade_bt_lookup 
    ON trade_ledger_bitemporal(trade_id, valid_from, valid_to, txn_from, txn_to);

-- Current state fast path
CREATE INDEX idx_trade_current 
    ON trade_ledger_bitemporal(trade_id) 
    WHERE is_current_valid = TRUE AND is_current_txn = TRUE;

-- Temporal range queries (PostgreSQL GiST)
-- CREATE INDEX idx_trade_valid_range 
--     ON trade_ledger_bitemporal USING GIST (daterange(valid_from, valid_to));
```

### Bitemporal Dimension — Employee

```sql
-- ============================================================
-- Bitemporal employee dimension
-- Tracks both real-world changes and database corrections
-- ============================================================

CREATE TABLE dim_employee_bitemporal (
    employee_sk         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    
    -- Natural key
    employee_id         INT            NOT NULL,
    
    -- Attributes
    employee_name       VARCHAR(300)   NOT NULL,
    department          VARCHAR(100),
    job_title           VARCHAR(200),
    salary              DECIMAL(12,2),
    office_location     VARCHAR(100),
    manager_id          INT,
    cost_center         VARCHAR(20),
    
    -- VALID TIME
    valid_from          DATE           NOT NULL,
    valid_to            DATE           NOT NULL DEFAULT '9999-12-31',
    
    -- TRANSACTION TIME
    txn_from            TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    txn_to              TIMESTAMP      NOT NULL DEFAULT '9999-12-31 23:59:59',
    
    -- Change tracking
    change_type         VARCHAR(20),  -- HIRE, TRANSFER, PROMOTION, CORRECTION, TERMINATION
    change_source       VARCHAR(50)   -- HR_SYSTEM, MANUAL, PAYROLL_FEED
);

CREATE INDEX idx_emp_bt_nk ON dim_employee_bitemporal(employee_id, valid_from, txn_from);
CREATE INDEX idx_emp_bt_current ON dim_employee_bitemporal(employee_id) 
    WHERE valid_to = '9999-12-31' AND txn_to = '9999-12-31 23:59:59';
```

---

## Sequence Diagram — Correction Flow (Bitemporal)

This shows what happens when a trade is corrected after initial recording:

```mermaid
sequenceDiagram
    participant TR as Trader
    participant FO as Front Office
    participant DB as Bitemporal DB
    participant AUD as Audit Trail
    
    Note over TR,AUD: Day 1: Original trade entry
    TR->>FO: Execute trade T-1001<br/>100 shares AAPL @ $150<br/>Trade date: Jan 15
    FO->>DB: INSERT trade T-1001<br/>valid_from=Jan 15, valid_to=9999<br/>txn_from=Jan 15 09:30, txn_to=9999
    DB->>AUD: Version 1 recorded
    
    Note over TR,AUD: Day 5: Correction discovered
    TR->>FO: Correction: price was $151, not $150
    FO->>DB: UPDATE existing row:<br/>SET txn_to = Jan 20 14:00<br/>(close old transaction-time version)
    FO->>DB: INSERT corrected row:<br/>price=$151<br/>valid_from=Jan 15 (unchanged)<br/>txn_from=Jan 20 14:00, txn_to=9999
    DB->>AUD: Version 2 recorded<br/>Original version preserved
    
    Note over TR,AUD: Both versions exist in DB
    Note over DB: Query "as known today" → returns $151
    Note over DB: Query "as known on Jan 18" → returns $150
```

---

## State Machine — Bitemporal Record Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Active: INSERT<br/>valid_to=9999, txn_to=9999
    
    Active --> Superseded_Valid: Real-world change<br/>(e.g., employee transferred)<br/>Close valid_to, insert new version
    Active --> Superseded_Txn: Correction/Amendment<br/>Close txn_to, insert corrected version
    Active --> Superseded_Both: Retroactive correction<br/>of a past-dated change
    Active --> Logically_Deleted: Business cancellation<br/>Close valid_to to cancellation date
    
    Superseded_Valid --> [*]: Historical record<br/>(immutable)
    Superseded_Txn --> [*]: Audit record<br/>(immutable)
    Superseded_Both --> [*]: Audit record<br/>(immutable)
    Logically_Deleted --> Superseded_Txn: Correction to deletion<br/>Close txn_to, insert new version
    
    note right of Active
        is_current_valid = true
        is_current_txn = true
    end note
    
    note right of Superseded_Txn
        Preserves what the DB
        believed at a past point
    end note
```

---

## Data Flow Diagram — Bitemporal ETL Pipeline

```mermaid
flowchart LR
    subgraph "Source"
        SRC["Source System<br/>(OLTP)"]
        LATE["Late Corrections<br/>(manual/file)"]
    end
    
    subgraph "Staging"
        STG["Staging Table<br/>(raw payload + metadata)"]
        CLASSIFY["Classify Change Type<br/>• New record<br/>• Update to current<br/>• Correction to past<br/>• Late-arriving"]
    end
    
    subgraph "Bitemporal Engine"
        MATCH["Match on natural key"]
        NEW["New Record Path<br/>INSERT with valid_from=effective_date"]
        UPD["Update Path<br/>1. Close current valid_to<br/>2. INSERT new valid version"]
        CORR["Correction Path<br/>1. Close current txn_to<br/>2. INSERT with same valid_from<br/>   but new txn_from"]
        LATE_PATH["Late-Arriving Path<br/>1. Split existing valid ranges<br/>2. INSERT backdated version<br/>3. Close txn_to on affected rows"]
    end
    
    subgraph "Bitemporal Store"
        BT["Bitemporal Table<br/>(all versions preserved)"]
        VIEW["Current-State View<br/>WHERE valid_to=9999<br/>AND txn_to=9999"]
    end
    
    SRC --> STG
    LATE --> STG
    STG --> CLASSIFY
    CLASSIFY --> MATCH
    MATCH -->|"Not found"| NEW
    MATCH -->|"Current change"| UPD
    MATCH -->|"Correction"| CORR
    MATCH -->|"Late-arriving"| LATE_PATH
    NEW --> BT
    UPD --> BT
    CORR --> BT
    LATE_PATH --> BT
    BT --> VIEW
```

---

## The Four Quadrants of Bitemporal Query

Every bitemporal query falls into one of four quadrants:

```mermaid
quadrantChart
    title Bitemporal Query Quadrants
    x-axis "Transaction Time (DB Knowledge)" --> "Past" "Current"
    y-axis "Valid Time (Reality)" --> "Past" "Current"
    "Current-Current": [0.85, 0.85]
    "Historical-Current": [0.85, 0.25]
    "Current-Past Knowledge": [0.25, 0.85]
    "Full Historical": [0.25, 0.25]
```

| Quadrant | Query Pattern | Use Case |
|---|---|---|
| **Current-Current** | `WHERE valid_to = '9999-12-31' AND txn_to = '9999-12-31'` | Normal operational queries |
| **Historical valid, Current txn** | `WHERE valid_from <= @date AND valid_to > @date AND txn_to = '9999-12-31'` | "What was true on date X, as we know it now?" |
| **Current valid, Past txn** | `WHERE valid_to = '9999-12-31' AND txn_from <= @ts AND txn_to > @ts` | "What did we believe was current on timestamp T?" |
| **Full historical** | `WHERE valid_from <= @date AND valid_to > @date AND txn_from <= @ts AND txn_to > @ts` | "What did we believe was true on date X, as of timestamp T?" |
