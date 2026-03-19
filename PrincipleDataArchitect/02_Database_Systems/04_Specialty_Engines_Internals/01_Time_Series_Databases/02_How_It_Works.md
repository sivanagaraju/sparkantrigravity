# Time-Series Databases — How It Works

## Architecture: The TSDB Engine Design

Modern TSDBs are built on the principle of **Inverted Indexing** for metadata (labels/tags) and **Columnar Data Stores** for measurements.

1.  **Index Layer (Inverted Index)**: Maps tag values (e.g., `region=us-east`) to a `Series ID`. This allows $O(1)$ lookups of which series need to be scanned.
2.  **Storage Layer (TSM / LSM)**:
    *   **WAL (Write Ahead Log)**: Immediate durability for incoming points.
    *   **Cache / MemTable**: In-memory buffer for the latest data points.
    *   **TSM (Time-Structured Merge Tree)**: Compressed, immutable files on disk. Data is sorted by `Series ID` then `Timestamp`.

## High-Level Design (HLD)

```mermaid
graph TD
    classDef client fill:#f9f,stroke:#333;
    classDef ingestion fill:#bbf,stroke:#333;
    classDef storage fill:#bfb,stroke:#333;
    classDef index fill:#fbb,stroke:#333;

    A[Client / Telegraf]:::client -->|Write Point| B[API / Gateway]:::ingestion
    B --> C{Validator}:::ingestion
    C -->|Valid| D[WAL - Durability]:::storage
    C -->|Valid| E[MemTable - In Memory]:::storage
    
    E -->|Lookup Tags| F[Inverted Index]:::index
    F -->|Return SeriesID| E
    
    E -->|Flush/Compact| G[TSM Files - Disk]:::storage
    G -->|Retention Policy| H[Tombstoner / Purger]:::storage
```

## Sequence Diagram: Data Ingestion & Indexing

```mermaid
sequenceDiagram
    participant App as Application
    participant HW as Head-of-Wall (API)
    participant IDX as Tag Index
    participant MT as MemTable
    participant WAL as Write-Ahead Log

    App->>HW: write(metric="cpu", tags="host=A", val=45, ts=N)
    HW->>IDX: lookup_or_create_series("cpu", "host=A")
    IDX-->>HW: Series_ID: 1001
    
    par Parallel Write
        HW->>WAL: append(1001, 12:00, 45)
        HW->>MT: insert(1001, 12:00, 45)
    end
    
    HW-->>App: 204 No Content (Success)
    
    Note over MT, WAL: Batching for Disk Flush...
```

## State Machine: The Lifecycle of a Data Point

```mermaid
stateDiagram-v2
    [*] --> Ingested
    Ingested --> InMemory : Buffering (MemTable)
    InMemory --> Compacted : Flush to Disk (Chunking)
    Compacted --> Downsampled : Aggregation (Optional)
    Downsampled --> Deleted : TTL Expired
    Compacted --> Deleted : TTL Expired
    Deleted --> [*]
```

## Data Flow Diagram (DFD): Query Execution

```mermaid
flowchart LR
    Q[SQL / PromQL Query] --> P[Parser]
    P --> T[Tag Filter Planner]
    T --> I[Index Interaction]
    I --> S[Gather Series IDs]
    S --> R[Range Scanner]
    R --> D[Disk SStables / TSM]
    D --> C[Decompress Chunks]
    C --> A[Aggregation Engine]
    A --> Result[Final Payload]
```

## Entity-Relationship (ER) Overview

In a TSDB, the relationship is between the "Series definition" and the "Point values".

```mermaid
erDiagram
    SERIES ||--o{ POINT : contains
    SERIES {
        string metric_name
        string hash_id PK
        json tags "Indexed metadata"
    }
    POINT {
        timestamp time PK
        double value "Measurement"
        string series_id FK
    }
```

## Table Structures (DDL)

**TimescaleDB (PostgreSQL Based):**
```sql
-- 1. Create standard table
CREATE TABLE sensor_data (
    time        TIMESTAMPTZ       NOT NULL,
    sensor_id   INTEGER           NOT NULL,
    temperature DOUBLE PRECISION  NULL,
    cpu_load    DOUBLE PRECISION  NULL
);

-- 2. Convert to Hypertable (Partitioned by time)
SELECT create_hypertable('sensor_data', 'time');

-- 3. Add compression policy
ALTER TABLE sensor_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'sensor_id'
);

-- 4. Set Retention Policy
SELECT add_retention_policy('sensor_data', INTERVAL '30 days');
```

**InfluxDB (Line Protocol Entry):**
```text
# Measurement, Tags, Field, Timestamp
cpu_usage,host=server01,region=us-west value=0.64 1434055562000000000
```
