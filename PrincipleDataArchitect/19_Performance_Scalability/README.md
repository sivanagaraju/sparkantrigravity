# 19 — Performance & Scalability

> "Anyone can write a query that works on 10 gigabytes. A Principal writes queries that will still work on 100 terabytes three years from now."

At FAANG scalability levels, brute-force compute is a crutch for bad architecture. True performance is achieved by eliminating the work the CPU has to do in the first place. You must master the physical data structures, caching layers, and the mathematics of data distribution.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Advanced_Indexing_and_B-Tree_Mechanics/`

- **The B-Tree Depth Problem**: Why a B-Tree of depth 4 requires 4 random disk I/O operations (if not cached). Calculating exact buffer pool hit ratios.
- **Covering Indexes and Index-Only Scans**: Designing indexes where the database engine never actually visits the underlying table data page.
- **Partial and Filtered Indexes**: Indexing only the `active = true` records to save 90% of index size and keep the "hot" data permanently in RAM.
- **GiST, GIN, and BRIN (Block Range Indexes)**: When point queries fail and you need to index arrays, full-text documents, or massive time-series append-only append-logs.

### `02_Partitioning_and_Sharding_Math/`

- **Range vs. Hash vs. List Partitioning**: The trade-offs. Why date-range partitioning is great for dropping old data but terrible for the "hot partition" problem on current-day writes.
- **Horizontal Sharding and Cross-Shard Joins**: The absolute nightmare of needing to join Data on Shard A with Data on Shard B. Application-level scatter-gather vs. Distributed Query Engines (like Presto/Trino).
- **The Resharding Tax**: Designing a consistent hashing ring so that moving from 10 to 12 shards only moves 16% of the data, rather than 100%.

### `03_Caching_Layers_and_Invalidation/`

- **Cache Aside vs. Read-Through vs. Write-Through vs. Write-Behind**: The race conditions inherent in each.
- **The Two Hardest Things**: Phil Karlton's famous quote. Naming things, and *Cache Invalidation*.
- **The Thundering Herd Problem**: What happens when a popular cache key (e.g., the Super Bowl score) expires and 10,000 application threads simultaneously query the database to rebuild it. Using probabilistic early expiration and mutex locks.
- **Materialized Views and Refresh Mechanics**: Fast concurrent refreshes vs. full rebuilds. Using incremental view maintenance.

### `04_Data_Compression_and_Encoding/`

- **Columnar vs. Row Storage Physics**: Why joining 5 columns on a 100-column table in Parquet is 100x faster than in CSV/JSON.
- **Run-Length Encoding (RLE) vs. Dictionary Encoding**: Sorting your data *before* you compress it to turn 1 billion distinct records into a compressed block the size of a few kilobytes.
- **Zstd vs. Snappy vs. LZ4**: The CPU vs. I/O trade-off equation. When to use fast-decompression algorithms over high-compression algorithms.

### `05_Query_Execution_Plans_and_Join_Algorithms/`

- **Nested Loop vs. Hash Join vs. Sort-Merge Join**: Reading EXPLAIN plans. Knowing exactly why the database optimizer chose a Nested Loop, and knowing when to force it to use a Hash Join using query hints.
- **Cardinality Estimation Failures**: When the database statistics are slightly wrong, the query optimizer makes catastrophically wrong decisions. How to manually analyze tables and fix histograms.
- **Data Skew and the "Straggler" Node**: In distributed Spark/Redshift, why one massive customer (CustomerID = NULL) causes 99 nodes to finish in 5 seconds while 1 node runs for 4 hours (OOM error). Mitigation via salting strategies.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
