# Snapshot Fact Tables — How It Works (Deep Internals)

> HLD, ER diagrams, DDL table structures, sequence diagrams, and data flow.

---

## High-Level Design — Periodic vs Accumulating Snapshots

```mermaid
flowchart TB
    subgraph "Periodic Snapshot Architecture"
        TXN1["Transaction Facts<br/>(every event)"]
        AGG["Aggregation Job<br/>(Spark/SQL — daily batch)"]
        PS["Periodic Snapshot<br/>fact_account_daily<br/>One row per account per day"]
        DIM["Dimensions<br/>(account, product, date)"]
    end
    
    subgraph "Accumulating Snapshot Architecture"
        TXN2["Transaction Events<br/>(status changes)"]
        UPSERT["Upsert Job<br/>(match on process key)"]
        AS["Accumulating Snapshot<br/>fact_order_lifecycle<br/>One row per order"]
        DIM2["Milestone Dimensions<br/>(date dims for each stage)"]
    end
    
    TXN1 --> AGG --> PS
    DIM --> PS
    TXN2 --> UPSERT --> AS
    DIM2 --> AS
    
    style PS fill:#FF6B35,color:#fff
    style AS fill:#4ECDC4,color:#fff
```

---

## ER Diagram — Periodic Snapshot: Daily Account Balance

```mermaid
erDiagram
    FACT_ACCOUNT_DAILY {
        bigint snapshot_sk PK
        int date_sk FK "Snapshot date"
        bigint account_sk FK
        bigint branch_sk FK
        bigint product_sk FK
        decimal opening_balance "Semi-additive"
        decimal closing_balance "Semi-additive"
        decimal total_credits "Additive"
        decimal total_debits "Additive"
        int transaction_count "Additive"
        decimal avg_daily_balance "Semi-additive"
        decimal interest_accrued "Additive"
    }
    
    DIM_DATE {
        int date_sk PK
        date calendar_date
        int year
        int quarter
        int month
        int day_of_week
        boolean is_business_day
        boolean is_month_end
    }
    
    DIM_ACCOUNT {
        bigint account_sk PK
        int account_id
        varchar account_type
        varchar status
        date open_date
        decimal credit_limit
    }
    
    FACT_ACCOUNT_DAILY }o--|| DIM_DATE : "date_sk"
    FACT_ACCOUNT_DAILY }o--|| DIM_ACCOUNT : "account_sk"
```

## ER Diagram — Accumulating Snapshot: Order Lifecycle

```mermaid
erDiagram
    FACT_ORDER_LIFECYCLE {
        bigint order_sk PK
        varchar order_number "Degenerate dim"
        bigint customer_sk FK
        bigint product_sk FK
        int order_date_sk FK
        int payment_date_sk FK "NULL until paid"
        int ship_date_sk FK "NULL until shipped"
        int delivery_date_sk FK "NULL until delivered"
        int return_date_sk FK "NULL if not returned"
        decimal order_amount
        decimal shipping_cost
        varchar current_status
        int days_to_payment "Computed lag"
        int days_to_ship "Computed lag"
        int days_to_deliver "Computed lag"
        timestamp last_updated
    }
    
    DIM_DATE {
        int date_sk PK
        date calendar_date
    }
    
    DIM_CUSTOMER {
        bigint customer_sk PK
        varchar customer_name
    }
    
    FACT_ORDER_LIFECYCLE }o--|| DIM_DATE : "order_date_sk"
    FACT_ORDER_LIFECYCLE }o--|| DIM_DATE : "ship_date_sk"
    FACT_ORDER_LIFECYCLE }o--|| DIM_DATE : "delivery_date_sk"
    FACT_ORDER_LIFECYCLE }o--|| DIM_CUSTOMER : "customer_sk"
```

---

## Table Structures

### Periodic Snapshot — Daily Account Balance

```sql
-- ============================================================
-- Periodic snapshot: one row per account per day
-- Semi-additive measures: can SUM across accounts, NOT across days
-- ============================================================

CREATE TABLE fact_account_daily (
    snapshot_sk         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    
    -- Grain: account + date
    date_sk             INT            NOT NULL REFERENCES dim_date(date_sk),
    account_sk          BIGINT         NOT NULL REFERENCES dim_account(account_sk),
    
    -- Dimension FKs
    branch_sk           BIGINT         REFERENCES dim_branch(branch_sk),
    product_sk          BIGINT         REFERENCES dim_product(product_sk),
    
    -- Semi-additive measures (DO NOT SUM across time)
    opening_balance     DECIMAL(18,2)  NOT NULL,
    closing_balance     DECIMAL(18,2)  NOT NULL,
    avg_daily_balance   DECIMAL(18,2),
    
    -- Fully additive measures (CAN SUM across time and other dims)
    total_credits       DECIMAL(18,2)  DEFAULT 0,
    total_debits        DECIMAL(18,2)  DEFAULT 0,
    transaction_count   INT            DEFAULT 0,
    interest_accrued    DECIMAL(12,4)  DEFAULT 0,
    
    -- Metadata
    snapshot_date       DATE           NOT NULL,
    loaded_at           TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    
    -- Uniqueness constraint on grain
    CONSTRAINT uq_account_daily UNIQUE (date_sk, account_sk)
    
) PARTITION BY RANGE (snapshot_date);

-- Create monthly partitions
CREATE TABLE fact_account_daily_2024_01 PARTITION OF fact_account_daily
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE fact_account_daily_2024_02 PARTITION OF fact_account_daily
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- ... repeat per month

-- Indexes
CREATE INDEX idx_fad_account ON fact_account_daily(account_sk, snapshot_date);
CREATE INDEX idx_fad_date ON fact_account_daily(date_sk);
```

### Accumulating Snapshot — Order Lifecycle

```sql
-- ============================================================
-- Accumulating snapshot: one row per order, updated at each milestone
-- Multiple date FKs, lag measures computed on each update
-- ============================================================

CREATE TABLE fact_order_lifecycle (
    order_sk            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    
    -- Process instance key
    order_number        VARCHAR(30)    NOT NULL UNIQUE,  -- degenerate dim
    
    -- Entity dimensions
    customer_sk         BIGINT         NOT NULL REFERENCES dim_customer(customer_sk),
    product_sk          BIGINT         NOT NULL REFERENCES dim_product(product_sk),
    channel_sk          BIGINT         REFERENCES dim_channel(channel_sk),
    
    -- Milestone date dimensions (NULL until milestone is reached)
    order_date_sk       INT            NOT NULL REFERENCES dim_date(date_sk),
    payment_date_sk     INT            REFERENCES dim_date(date_sk),
    pick_date_sk        INT            REFERENCES dim_date(date_sk),
    ship_date_sk        INT            REFERENCES dim_date(date_sk),
    delivery_date_sk    INT            REFERENCES dim_date(date_sk),
    return_date_sk      INT            REFERENCES dim_date(date_sk),
    
    -- Measures
    order_amount        DECIMAL(12,2)  NOT NULL,
    shipping_cost       DECIMAL(10,2)  DEFAULT 0,
    discount_amount     DECIMAL(10,2)  DEFAULT 0,
    return_amount       DECIMAL(12,2)  DEFAULT 0,
    
    -- Status
    current_status      VARCHAR(20)    NOT NULL,  -- ORDERED, PAID, PICKED, SHIPPED, DELIVERED, RETURNED
    
    -- Computed lags (days between milestones)
    days_order_to_payment   INT,
    days_payment_to_ship    INT,
    days_ship_to_delivery   INT,
    days_order_to_delivery  INT,
    
    -- Metadata
    last_updated        TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fol_status ON fact_order_lifecycle(current_status);
CREATE INDEX idx_fol_order_date ON fact_order_lifecycle(order_date_sk);
```

---

## Sequence Diagram — Periodic Snapshot Generation

```mermaid
sequenceDiagram
    participant SCH as Scheduler (Airflow)
    participant SPARK as Spark Job
    participant TXN as fact_transactions
    participant PREV as Previous Day Snapshot
    participant SNAP as fact_account_daily
    participant QA as Quality Check
    
    SCH->>SPARK: Trigger daily snapshot job (T+1)
    SPARK->>PREV: Read previous day closing balances
    SPARK->>TXN: Read today's transactions<br/>(credits, debits, count)
    SPARK->>SPARK: Compute:<br/>opening_balance = prev.closing_balance<br/>closing_balance = opening + credits - debits<br/>avg_balance = (opening + closing) / 2
    SPARK->>SNAP: INSERT INTO fact_account_daily<br/>(one row per account)
    SNAP->>QA: Validate:<br/>1. Row count = expected accounts<br/>2. SUM(closing) reconciles with GL<br/>3. No NULLs in required fields
    QA->>SCH: Pass/Fail
    
    Note over SPARK: Dense snapshot: creates a row<br/>for every active account,<br/>even if no transactions today
```

---

## Sequence Diagram — Accumulating Snapshot Update

```mermaid
sequenceDiagram
    participant EVENT as Status Change Event
    participant ETL as ETL Pipeline
    participant SNAP as fact_order_lifecycle
    
    Note over EVENT,SNAP: Phase 1: Order Created
    EVENT->>ETL: Order ORD-1001 created
    ETL->>SNAP: INSERT new row<br/>order_date_sk = 20240315<br/>status = ORDERED<br/>All other date_sk = NULL
    
    Note over EVENT,SNAP: Phase 2: Payment Received
    EVENT->>ETL: ORD-1001 payment received
    ETL->>SNAP: UPDATE SET<br/>payment_date_sk = 20240316<br/>status = PAID<br/>days_order_to_payment = 1
    
    Note over EVENT,SNAP: Phase 3: Shipped
    EVENT->>ETL: ORD-1001 shipped
    ETL->>SNAP: UPDATE SET<br/>ship_date_sk = 20240318<br/>status = SHIPPED<br/>days_payment_to_ship = 2
    
    Note over EVENT,SNAP: Phase 4: Delivered
    EVENT->>ETL: ORD-1001 delivered
    ETL->>SNAP: UPDATE SET<br/>delivery_date_sk = 20240321<br/>status = DELIVERED<br/>days_ship_to_delivery = 3<br/>days_order_to_delivery = 6
```

---

## Data Flow Diagram — Snapshot Pipeline

```mermaid
flowchart LR
    subgraph "Sources"
        OLTP["OLTP Systems"]
        CDC["CDC Events"]
        GL["General Ledger"]
    end
    
    subgraph "Transaction Layer"
        TXN["Transaction Fact Table<br/>(finest grain events)"]
    end
    
    subgraph "Snapshot Generation"
        PREV["Previous Period Snapshot<br/>(T-1 closing state)"]
        CALC["Compute New Snapshot:<br/>• Opening = prev closing<br/>• Credits/Debits from txns<br/>• Closing = opening + net<br/>• Avg = (open + close) / 2"]
        QA["Quality Checks:<br/>• Row count validation<br/>• Balance reconciliation<br/>• Completeness check"]
    end
    
    subgraph "Snapshot Store"
        SNAP["Periodic Snapshot Fact<br/>(partitioned by date)"]
        DENSE["Dense: every entity every period"]
    end
    
    subgraph "Consumers"
        BI["BI Reports<br/>(balance trends)"]
        REG["Regulatory<br/>(period-end state)"]
        RECON["Reconciliation<br/>(txn ↔ snapshot)"]
    end
    
    OLTP --> CDC --> TXN
    GL --> TXN
    TXN --> CALC
    PREV --> CALC
    CALC --> QA --> SNAP
    SNAP --> DENSE
    SNAP --> BI
    SNAP --> REG
    TXN --> RECON
    SNAP --> RECON
```

---

## Activity Diagram — Semi-Additive Measure Handling

```mermaid
flowchart TD
    START([BI user writes query])
    
    START --> Q1{What measure type?}
    
    Q1 -->|Fully additive| ADD["SUM across all dimensions<br/>(transaction_count, total_credits)"]
    Q1 -->|Semi-additive| SEMI{"Dimension being aggregated?"}
    
    SEMI -->|"Across accounts (non-time)"| SUM_OK["SUM is valid<br/>Total closing balance across all accounts"]
    SEMI -->|"Across time"| SUM_BAD["⚠️ SUM is INVALID<br/>Cannot sum daily balances"]
    
    SUM_BAD --> ALT{"What to use instead?"}
    ALT -->|Period-end| LAST["Use closing_balance WHERE<br/>date = period_end_date"]
    ALT -->|Average| AVG["Use AVG(closing_balance)<br/>across the period"]
    ALT -->|Weighted avg| WAVG["Use SUM(balance × days_held)<br/>÷ total_days"]
    
    ADD --> RESULT([Return result])
    SUM_OK --> RESULT
    LAST --> RESULT
    AVG --> RESULT
    WAVG --> RESULT
    
    style SUM_BAD fill:#E74C3C,color:#fff
    style SUM_OK fill:#27AE60,color:#fff
```
