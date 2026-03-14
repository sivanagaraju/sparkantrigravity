# PostgreSQL Internals — Concept Overview

> Process architecture, query execution, buffer management: what happens under the hood.

## Architecture

```mermaid
flowchart TB
    subgraph "Client Connections"
        C1["psql"] & C2["App"] & C3["pgAdmin"]
    end
    
    subgraph "PostgreSQL Server"
        PM["Postmaster<br/>(main process)"]
        subgraph "Backend Processes (per connection)"
            B1["Backend 1 (parser → planner → executor)"]
            B2["Backend 2"]
        end
        subgraph "Background Workers"
            AV["Autovacuum"]
            CK["Checkpointer"]
            WW["WAL Writer"]
            BW["Background Writer"]
            AR["WAL Archiver"]
        end
        subgraph "Shared Memory"
            SB["Shared Buffers (pages)"]
            WB["WAL Buffers"]
            CT["CLOG (transaction status)"]
        end
    end
    
    C1 & C2 & C3 --> PM
    PM --> B1 & B2
    B1 & B2 --> SB
    SB --> WB
    WW --> WAL["WAL Files"]
    CK --> DATA["Data Files"]
    BW --> DATA
```

**Key insight**: One OS process per connection. This is why connection pooling matters — 1000 connections = 1000 processes.

## Query Execution Pipeline

```
SQL text → Parser → Rewriter → Planner/Optimizer → Executor → Results
       (syntax tree)  (view expansion)  (cost-based plan)  (run plan)
```

## References

| Resource | Link |
|---|---|
| [PostgreSQL Internals](https://www.postgresql.org/docs/current/internals.html) | Official |
| *PostgreSQL 14 Internals* | Egor Rogov (free e-book) |
