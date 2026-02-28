# 04 — Data Lake & Lakehouse: The Convergence

> "A data lake without governance is a data swamp. A lakehouse without performance tuning is a slow swamp with ACID transactions."

The lakehouse paradigm merged the flexibility of data lakes (store anything, schema-on-read) with the reliability guarantees of data warehouses (ACID, time travel, schema enforcement). A Principal Architect must understand the three competing open table formats at the byte level.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Data_Lake_Foundations/`

- **Zone Architecture**: Landing (raw/bronze), Curated (silver), Consumption (gold). Why some companies add a "Quarantine" zone and a "Sandbox" zone.
- **File Format Selection**: Parquet vs. ORC vs. Avro vs. Delta. Parquet for analytics, Avro for streaming/Kafka, ORC for Hive legacy. The exact columnar encoding mechanics (dictionary encoding, RLE, delta encoding).
- **Partitioning Strategy**: Over-partitioning (1 million empty folders) vs. under-partitioning (full table scans). Calculating optimal partition granularity based on file size distributions.
- **Small Files Problem**: Why 100,000 one-kilobyte Parquet files are 1,000x slower than 10 hundred-megabyte files. Compaction strategies (Spark repartition, Delta OPTIMIZE, Hudi clustering).

### `02_Delta_Lake_Deep_Dive/`

- **Transaction Log (`_delta_log/`)**: The JSON+Parquet checkpoint mechanism. How Delta achieves ACID by writing metadata logs rather than modifying data in place.
- **Z-Ordering vs. Liquid Clustering**: Z-Ordering sorts data along multiple dimensions using space-filling curves. Liquid Clustering (new in Delta 3.0) eliminates the need for explicit OPTIMIZE by clustering incrementally on write.
- **Change Data Feed (CDF)**: Enabling downstream consumers to read only the changed rows since the last checkpoint, rather than rescanning the entire table.
- **Deletion Vectors**: Marking rows as deleted without rewriting entire Parquet files, dramatically reducing the cost of MERGE operations.

### `03_Apache_Iceberg_Deep_Dive/`

- **Metadata Layer Architecture**: Catalog → Metadata File → Manifest List → Manifest File → Data File. Why this 4-layer indirection enables time travel and snapshot isolation without locking.
- **Hidden Partitioning**: Users write `WHERE event_date = '2025-01-15'` and Iceberg automatically prunes partitions without the user needing to know the partitioning scheme. How this eliminates partition-column-in-query mistakes.
- **Schema Evolution Without Rewrite**: Adding, dropping, renaming, and reordering columns without rewriting the underlying Parquet files. Name-based vs. ID-based column mapping.
- **Catalog Integration**: Nessie (Git-like branching for data), AWS Glue Catalog, Hive Metastore, REST catalog. Multi-engine access (Spark, Flink, Trino, Dremio all reading the same table).

### `04_Apache_Hudi_Deep_Dive/`

- **Copy-on-Write (CoW) vs. Merge-on-Read (MoR)**: CoW rewrites entire file groups on update (fast reads, slow writes). MoR logs deltas to append files and compacts later (fast writes, slower reads until compaction).
- **Timeline Architecture**: Hudi's unique time-ordered log of all operations. Enabling incremental queries: "Give me all records that changed since my last pipeline run."
- **Compaction Strategies**: Inline vs. async compaction. Scheduling compaction during off-peak hours to avoid query latency spikes.

### `05_Table_Format_Head_To_Head/`

- **Delta vs. Iceberg vs. Hudi Decision Matrix**: Comparing on write performance, read performance, schema evolution, partition evolution, time travel depth, community momentum, and cloud-native integrations.
- **The UniForm / XTable Movement**: Delta's UniForm and Apache XTable (formerly OneTable) — automatically generating Iceberg metadata from Delta tables. Moving toward format interoperability.
- **Vendor Lock-in Analysis**: Databricks pushes Delta. AWS pushes Iceberg. Uber built Hudi. How to choose without betting your career on a vendor.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
