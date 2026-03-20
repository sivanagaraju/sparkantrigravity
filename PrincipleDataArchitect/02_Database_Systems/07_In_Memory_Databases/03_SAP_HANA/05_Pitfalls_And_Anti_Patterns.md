# Pitfalls and Anti-Patterns: SAP HANA

## M01: Leaving the Delta Merge to Auto-Pilot on Huge Loads

### The Mistake
Migrating 100 million rows from a legacy Oracle database into SAP HANA via SAP Data Services, entirely relying on the background `mergedog` (the automatic merge daemon) to eventually process the L2 Delta store.

### The Impact
The `mergedog` is designed for thousands of trickle-feed ERP transactions. When hit by a 100 million row wall, the L1/L2 Delta stores explode. Because Delta stores are uncompressed and row-pointer oriented, RAM consumption shoots up by 200GB unexpectedly. Queries against the table during this time are forced to scan 100 million uncompressed Delta rows, dropping performance by 10x. Eventually, the `mergedog` kicks in, doubling memory usage during the atomic swap phase, potentially causing a global OOM crash.

### Detection
```sql
SELECT 
    HOST, TABLE_NAME, MEMORY_SIZE_IN_DELTA, RECORD_COUNT_IN_DELTA 
FROM M_CS_TABLES 
WHERE RECORD_COUNT_IN_DELTA > 1000000;
```

### The Fix
When executing massive ETL batches, temporarily suspend the `mergedog` on that specific table, execute the batch, and explicitly trigger a synchronous merge exactly when the batch completes.
```sql
-- Disable auto merge for large batch jobs
ALTER TABLE "MVT_HISTORY" DISABLE AUTOMERGE;

-- ... RUN MASSIVE BATCH INSERT ...

-- Manually trigger synchronous merge when it is safely completed
MERGE DELTA OF "MVT_HISTORY";

-- Re-enable for normal daily ERP transactions
ALTER TABLE "MVT_HISTORY" ENABLE AUTOMERGE;
```

---

## M02: Unbounded Statement Caching (The Cartesian OOM)

### The Mistake
Allowing ad-hoc analytics queries (e.g., from PowerBI or Tableau direct connections) without hard query memory limits. An analyst writes a query joining `VBAK` (10M rows) to `BSEG` (100M rows) without joining on the primary keys, creating a massive Cartesian product.

### The Impact
HANA executes queries entirely in memory. It allocates a "Workspace" for the intermediate results. A Cartesian product of $10M \times 100M$ rapidly attempts to allocate terabytes of RAM. If left unchecked, the `hdbindexserver` consumes all physical RAM on the hardware, the Linux Kernel OOM killer steps in, and the entire production ERP system crashes globally.

### Detection
Check the `M_EXPENSIVE_STATEMENTS` view for historically massive queries.
```sql
SELECT START_TIME, STATEMENT_STRING, MEMORY_SIZE 
FROM M_EXPENSIVE_STATEMENTS 
ORDER BY MEMORY_SIZE DESC LIMIT 10;
```

### The Fix
Globally enforce the strictly necessary `statement_memory_limit` in the `global.ini` configuration file.
```ini
[memorymanager]
global_allocation_limit = 2000000  # 2TB Global DB Limit
statement_memory_limit = 100000    # Hard kill any query exceeding 100GB
```
When an analyst runs a terrible query, the single query transaction dies instantly with an explicit `SQL Error 137: memory allocation failed`, but the SAP ERP system stays online.

---

## M03: "Data-to-Code" Paradigm (The ABAP Loop)

### The Mistake
Writing application logic the exact same way you did on an Oracle database in 2005. The application dynamically queries 2,000,000 raw rows from HANA, moves them over the 10Gbps network to the SAP NetWeaver Application Server, and runs an ABAP `LOOP AT ... ENDLOOP` to sum the values.

### The Impact
HANA's core value—its ability to use SIMD instructions to sum 2 million rows locally in 0.05 seconds—is bypassed completely. The query is now bottlenecked entirely by 10Gbps TCP network transfer latency and the slow, strictly sequential ABAP application server language loop.

### Detection
Identify network saturation between the DB layer and the App layer, and investigate programs running `SELECT *` without `WHERE` or `GROUP BY` aggregations.

### The Fix
Transition strictly to the "Code-to-Data" paradigm. Push all complex filtering, joining, and aggregation down into the database via **Core Data Services (CDS) Views** or **HANA SQLScript (AMDPs)**. Transfer only the final 1-row summarized result back over the network to the application server for eventual UI display.

---

## M04: Ignoring NSE (Native Storage Extension) for Cold Data

### The Mistake
Upgrading to S/4HANA but leaving all historical transactional tables (from the year 2000 to the present) configured as standard In-Memory Main Column Stores.

### The Impact
HANA Enterprise RAM costs anywhere from $20k to $100k per Terabyte on top-tier certified hardware. Storing 24-year-old closed sales orders entirely in main memory forces the enterprise to purchase 12TB of RAM, wasting millions of dollars on data that is queried once a month for regulatory audits.

### Detection
Analyze disk and memory aging views.
```sql
-- Find columns taking massive RAM that have not been accessed by queries in > 1 year
SELECT TABLE_NAME, LAST_ACCESS_TIME, MEMORY_SIZE_IN_TOTAL 
FROM M_TABLE_STATISTICS 
WHERE LAST_ACCESS_TIME < ADD_YEARS(CURRENT_DATE, -1)
ORDER BY MEMORY_SIZE_IN_TOTAL DESC;
```

### The Fix
Implement SAP HANA NSE (Data Tiering).
```sql
ALTER TABLE "ZOLD_TRANSACTIONS" PAGE LOADABLE;
-- Unload immediately forces the 10-year data entirely onto NVMe Flash
ALTER TABLE "ZOLD_TRANSACTIONS" UNLOAD;
```
Data remains perfectly accessible to SQL. When queried, HANA pulls blocks transparently from NVMe to a specialized tiny RAM Buffer Cache, executing the query slightly slower but saving millions in hardware footprint.
