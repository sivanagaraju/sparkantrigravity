# SAP HANA — Concept Overview

> The in-memory columnar database that powers the world's largest ERP systems.

## Why HANA Is Different

Traditional OLTP databases store data row-by-row on disk, reading from disk for every query. HANA keeps the ENTIRE database in memory (RAM) and stores data in columnar format. This enables real-time analytics on transactional data — no separate DW needed.

## Key Architecture

| Component | Purpose |
|---|---|
| **Column Store** | Primary storage; dictionary encoding + compression → 5-10x less memory |
| **Row Store** | For write-heavy OLTP tables (optional) |
| **Delta Store** | Buffered writes before merge into main column store |
| **Persistence Layer** | Savepoints + redo log for durability (data survives restart) |

**Enterprise scale**: SAP customers run HANA instances with 6-24TB of RAM on single appliances.

## Interview — Q: "When would you use an in-memory database over PostgreSQL?"

**Strong Answer**: "When the entire working set fits in RAM AND you need real-time analytics on OLTP data without ETL delay. HANA eliminates the DW by making OLTP data analytically queryable. But at $50K+/TB for HANA licensing vs free PostgreSQL, the cost justification must be clear. For smaller datasets (<500GB), PostgreSQL with enough `shared_buffers` achieves similar in-memory performance."

## References

| Resource | Link |
|---|---|
| [SAP HANA Architecture](https://help.sap.com/docs/SAP_HANA_PLATFORM/eb3777d5495d46c5b2fa773206bbfb46/) | Official docs |
