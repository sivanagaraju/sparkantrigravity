# 🧠 Mind Map – SAP HANA

---

## How to Use This Mind Map
- **For Revision**: A fast hierarchical review of the most complex Enterprise HTAP system on earth. Study the Delta Merge state-machine logic.
- **For Application**: Review the "Techniques & Patterns" specifically for detecting Cartesian OOM queries and shifting code to the DB using CDS views.
- **For Interviews**: Drill the 'Interview Angle' to eloquently describe SIMD execution speeds and N-bit dictionary packing.

---

## 🗺️ Theory & Concepts

### 01: Core Architecture (HTAP Mastery)
- **Origin & Purpose**
  - Spearheaded by Hasso Plattner (2010), designed to eliminate overnight ETL batches entirely.
  - Hybrid Transactional/Analytical Processing (HTAP) unifies OLTP row-write needs with OLAP column-scan speeds.
  - The singular fundamental DB platform allowing SAP S/4HANA (enterprise ERP) to function.
- **Micro-Services Engine Topology**
  - **Index Server**: The massive core engine executing all data storage, processing, and SQL plans.
  - **Name Server**: The scale-out topology master knowing which Node IP holds what tables.
  - **XS Engine**: Embedded application/web server executing logic inside the DB boundary.

### 02: Space Management (The Column/Row Divide)
- **Row Store**
  - Fully resident in RAM, built for single-row lookups.
  - Used extremely sparingly (<5% tables), mostly for administrative sequences and highly volatile settings.
- **Column Store (The Engine Block)**
  - Stores all values of a column contiguously in RAM vectors.
  - Perfect for analytical reading (`SUM`, `AVG`).
  - Capable of massive compression (e.g., repeating strings compressed mathematically).

### 03: The Write Problem (Delta Stores)
- **The Paradox**
  - Column stores hate row insertions. You have to lock a million compressed elements to add one row.
- **The Solution (L1 / L2 Delta)**
  - New ERP transactions bypass the Column Store and insert blindly into an uncompressed memory array (L1 Delta) in microseconds.
  - Periodically shifts to L2 Delta (column formatted but not completely structured).
  - Keeps the primary ERP system incredibly responsive (low latency OLTP).

### 04: The Read Problem (Delta Merge)
- **The Tradeoff**
  - Queries must scan the giant compressed Main column AND the messy little Delta rows and merge the result sets mathematically in-flight.
- **The Background Delta Merge**
  - When the delta gets too large (>100k rows), HANA launches a background CPU-heavy sweep.
  - Fuses the Delta tables into a highly compressed, new Main structure.
  - Momentarily doubles memory footprint for that table during the `Main` -> `Main2` atomic pointer swap.

### 05: Analytics Acceleration
- **Dictionary Encoding & Bit Packing**
  - Strings are banned from the Main store vectors. Everything is an integer pointing to a global dictionary list.
  - N-Bit encoding detects column cardinality. If a column only has 4 unique string states globally, the entire billion-row vector is built using strictly 2 physical bits per row (`01`, `10`, etc.).
- **SIMD (Single Instruction, Multiple Data)**
  - Natively compiles to Intel SSE/AVX hardware.
  - CPU pulls 256 contiguously packed bits into L1 cache and computes identical math operations on 8 integers simultaneously in one hardware clock cycle.

### 06: Multi-Engine Extensibility
- **Spatial Engine**
  - Native storage for GIS data (ST_Point, ST_Geometry).
  - Allows spatial joins at RAM-speed (e.g., "Find all factories within 50 miles of this earthquake epicenter").
- **Graph Engine**
  - Stores data as nodes and edges for relationship traversal.
  - Essential for Supply Chain impact analysis and Fraud detection.
- **Predictive Analytics Library (PAL)**
  - 90+ algorithms (K-Means, C4.5, etc.) executed directly in the Index Server kernel to avoid data movement to Python/R.
- **Document Store (JSON)**
  - Native NoSQL capability inside the relational core.
  - Allows schema-less JSON collections that can be joined with strict SQL tables.

### 07: Deployment Architecture (MDC)
- **Multitenant Database Containers (MDC)**
  - One System Database manages infrastructure (topology, backups, licenses).
  - Multiple Tenant Databases run as isolated Unix processes with fixed memory caps.
- **Shared Everything vs. Shared Nothing**
  - On a single node, HANA is Shared-Memory; all cores touch the same physical DIMMs.
  - In a cluster, it behaves as Shared-Nothing for data partitions, but requires a high-speed GBit/s interconnect for cross-node joins.

### 08: Persistent Storage Layer
- **Redo Logs (WAL)**
  - Synchronous writes to persistent disk for every transaction.
  - Optimized for sequential NVMe throughput.
- **Savepoints**
  - Asynchronous persistent snapshots of the whole RAM state every few minutes.
  - Reduces the volume of logs needed to be replayed during a crash recovery.
- **Data Volumes**
  - Final resting place for column partitions and metadata blocks on disk.

### 09: Deep Internals: Delta Store Memory Tiers
- **L1 Delta (Write-Optimized)**
  - Row-store format, uncompressed, strictly in-memory.
  - Optimized for high-frequency inserts.
- **L2 Delta (Read-Optimized Delta)**
  - Column-store format, unsorted, lightly compressed.
  - Intermediate stage before full compression.
- **Main Store (The Golden Source)**
  - Heavily compressed (Dictionary Encoding, Bit-Packing).
  - Designed for massive scans.

---

## 🗺️ Techniques & Patterns

### T1: Scale-Out (Clustered Parallelism)
- **When to use**: When your primary ERP instance exceeds 6 Terabytes of required active RAM.
- **Step-by-Step Mechanics**
  - Deploy multiple massive Intel nodes connected via minimal-latency fiber.
  - Coordinator acts as Name Server. Partition massive billing tables across Node 1, Node 2, and Node 3 using Hash or Range partitioning.
  - When query lands, Coordinator issues sub-queries to all nodes. Nodes execute locally using SIMD on their local RAM partitions, executing massively parallel calculations before returning.
- **Decision Heuristics**: Prefer Scale-Up (one massive 12TB box) over Scale-Out whenever possible to avoid network latency. Scale-out introduces massive architectural planning overhead.
- **Failure Mode**: Improper partitioning keys force the Coordinator to broadcast 100% of queries to 100% of nodes, saturating network interconnects entirely.

### T2: Persistent Memory (Intel Optane PMEM)
- **When to use**: Reducing restart RTOs after OS kernel updates.
- **Step-by-Step Mechanics**
  - Install physical Non-Volatile DIMMs onto the motherboard alongside standard DDR4.
  - HANA config locates the Main Column Store heavily on PMEM.
  - DB node restarts. Power cycles. Standard RAM wipes.
  - HANA Index Server boots in seconds, memory-mapping directly to the surviving non-volatile RAM structures.
- **Decision Heuristics**: Huge CAPEX reduction (PMEM historically cheaper per Terabyte than pure DDR4).
- **Failure Mode**: High latency NUMA topologies. If CPU 1 is forced to read PMEM allocated strictly on CPU 4's bus, latency spikes by 30ns, slowing massive aggregations.

### T3: Dynamic Tiering / NSE (Native Storage Extension)
- **When to use**: Historical archive data bloating expensive pure in-memory footprint.
- **Step-by-Step Mechanics**
  - Identify read-cold columns or partitions via HANA monitoring views.
  - Tag with `PAGE LOADABLE`.
  - HANA writes the data purely to SSD NVMe disk structures, freeing it from the core RAM vectors.
  - Queries pulling this data transparently fetch 16KB blocks into a tiny RAM Buffer Cache dynamically.
- **Decision Heuristics**: Necessary to prevent HANA infrastructure licensing from bankrupting the global IT budget.

### T4: Smart Data Access (SDA) - Virtualization
- **When to use**: Querying a 100TB Hadoop cluster from a 2TB HANA box without moving data.
- **Mechanism**:
  - Map external tables as "Remote Sources" via ODBC.
  - HANA Query Optimizer performs "Predicate Push-down" (sends the `WHERE` clause to Hive/Snowflake).
  - Only the tiny aggregated result set returns via the wire.

### T5: Secondary Indexing Strategies
- **Philosophy**: Avoid unless specific high-cardinality searches fail performance targets.
- **Pattern**: Use "Inverted Indexes" on non-sorted column vectors to speed up exact match lookups.

---

## 🗺️ Hands-On & Code

### C01: Suspending Auto-Merge for ETL 
- **The Code Pattern**:
  ```sql
  ALTER TABLE "SYS_BILLING" DISABLE AUTOMERGE;
  -- App executes massive 10 Million row insert over 2 hours
  MERGE DELTA OF "SYS_BILLING";
  ALTER TABLE "SYS_BILLING" ENABLE AUTOMERGE;
  ```
- **Explanation**: Prevents the internal `mergedog` background process from firing repeatedly and hopelessly during a massive active batch job.

### C02: The Code-To-Data Paradigm (CDS)
- **The Code Pattern**:
  ```cds
  -- Executed strictly in the HANA Database, never the SAP App Server
  define view Z_Finance_Aggr as select from bseg as Accounting {
      key Accounting.company_code,
      sum(Accounting.total_amount) as TotalLedger
  } group by Accounting.company_code
  ```
- **Explanation**: Bypasses network transfer. Evaluates the aggregation completely natively using SIMD and Bit-Packed Main stores.

### C03: Monitoring Memory Breakdown
- **The SQL**:
  ```sql
  SELECT COMPONENT, SUM(EXCLUSIVE_SIZE_IN_USE) 
  FROM M_SERVICE_COMPONENT_MEMORY 
  GROUP BY COMPONENT ORDER BY 2 DESC;
  ```
- **Analysis**:
  - `ColumnStore`: Expected core data size.
  - `Statement Execution`: RAM used for temporary query results.
  - `RowStore`: Should be < 5% of ColumnStore.

### C04: Checking Delta Merge Health
- **The SQL**:
  ```sql
  SELECT TABLE_NAME, MEMORY_SIZE_IN_TOTAL, RECORD_COUNT, DELTA_RECORD_COUNT 
  FROM M_CS_TABLES WHERE DELTA_RECORD_COUNT > 100000;
  ```

---

## 🗺️ Real-World Scenarios

### 01: The Cartesian Statement OOM
- **The Trap**: Connecting analysts via Tableau without guarding the root database.
- **Scale**: Multi-Terabyte Global SAP environment.
- **What Went Wrong**: Analyst joins 10M rows with 50M rows linearly. Workspace tries to build 500-trillion-cell temp table in RAM.
- **The Fix**: Globally enforce `statement_memory_limit` in `.ini` settings.

### 02: The Savepoint Disk Queue Latency
- **The Trap**: Running HANA on slow SAN arrays.
- **Scale**: 5,000 active ERP cash-registers.
- **What Went Wrong**: Synchronous Redo Log writes block transactions. Savepoint flushes saturate I/O.
- **The Fix**: Mandatory direct-attached NVMe arrays for Log volumes.

### 03: S/4HANA Migration "Memory Wall"
- **Scenario**: Company migrates from Oracle to SAP HANA.
- **Problem**: Custom code uses nested loops fetching millions of rows to the application layer.
- **Resolution**: High CPU on App Server, idle DB. The "Wall" is the 10Gbps network link. Fix: Push logic into CDS Views.

### 04: The "Selective Load" Trap
- **Problem**: Admin restarts HANA; users complain about "slow first query."
- **Reality**: Column tables stay on disk until first access.
- **Fix**: Use `LD_PRELOAD` or pre-load scripts to pull mission-critical tables into RAM before users log in.

### 05: The "Split Brain" High Availability Failure
- **Problem**: Primary site loses network but remains powered on. DR site promotes itself to primary.
- **Result**: Dual masters. App servers write inconsistent data.
- **Fix**: STONITH (Shoot The Other Node In The Head) fencing protocols.

---

## 🗺️ Mistakes & Anti-Patterns

### M01: Pulling "All Columns" in Analytics
- **Root Cause**: Running `SELECT *` on a Column Store but only using three columns.
- **Diagnostic**: Forces 150 distinct memory traversal events to stitch rows back together horizontally.
- **Correction**: Exclusively select required dimensions.

### M02: Building Secondary Indexes Intuitively
- **Root Cause**: Oracle DBAs migrating to HANA building secondary indexes on everything.
- **Diagnostic**: Column store dictionary is essentially inherently indexed.
- **Correction**: Indexes are mostly obsolete and harm Delta Merge performance CPU overhead.

### M03: Massive Unfiltered Inserts without Batching
- **Problem**: Pushing 1M individual `INSERT` statements into the Row Store.
- **Reality**: Triggers 1M synchronous Redo Log disk commits.
- **Fix**: Use Array Inserts to allow HANA to group the Redo Log writes.

---

## 🗺️ Interview Angle

### HTAP Defensible Viability
- **The Setup**: "Can you honestly run an OLAP Data Warehouse inside your active OLTP Master ERP Database?"
- **The Defense**: Historically impossible due to row-lock contention. HANA enables it through decoupling the uncompressed Write-Optimized Delta Store and bit-packed Read-Optimized Main store.

### Physical Compression Math
- **The Question**: "Why is scanning a list of 1 Billion Country-Codes so fast in a Column store?"
- **The Answer**: "Dictionary Encoding. The table is purely 1 Billion bit-packed flags. Scanned by Intel SIMD hardware at exactly 1 cycle per 128-bit block."

### NUMA Awareness
- **The Question**: "Why does performance degrade when we increase the core count on a single host?"
- **The Answer**: "Non-Uniform Memory Access (NUMA). Remote RAM access crossing the UPI/QPI interconnect adds 30% latency penalty."

### RTO vs RPO in In-Memory Systems
- **The Question**: "If everything is in RAM, isn't a power failure catastrophic?"
- **The Answer**: "HANA is ACID persistent. Transactions are logged to the synchronous Redo Log on NVMe. Snapshots (Savepoints) are taken every 5 mins. Recovery replays the logs."

---

## 🗺️ Assessment & Reflection

### Knowledge Check Criteria
- [ ] Can you diagram the lifecycle of an `INSERT` (L1 -> L2 -> Main Store)?
- [ ] Define "N-Bit Encoding" for low-cardinality columns.
- [ ] Explain why `SELECT *` destroys Column Store query velocity.
- [ ] Understand why Intel PMEM improves RTO recovery times.
- [ ] Know the difference between `DELTA MERGE` and `SAVEPOINT`.

### Production Audit Questions
- Do we have `statement_memory_limit` configured globally?
- Are we using NSE (Native Storage Extension) for aging data?
- Are legacy ABAP developers using `LOOP AT` (network heavy) instead of CDS Views?
- Check `M_CS_TABLES`: Are any tables stuck with huge unmerged Deltas?

---

### 🔥 Deep Research Flashcards

**Q: What is the "Mergedog"?**
**A**: The internal background service responsible for triggering the Column Merge to Main.

**Q: What is the benefit of Dictionary Encoding?**
**A**: It enables fixed-length column vectors, allowing O(1) fixed-offset calculations.

**Q: How does HANA achieve ACID on-disk?**
**A**: Redo Logs (synchronous WAL) and Savepoints (RAM snapshots every 5 mins).

**Q: What is STONITH?**
**A**: "Shoot The Other Node In The Head" - a fencing technique to prevent split-brain in clustered setups.

**Q: What is the XS Engine?**
**A**: An embedded application/web server inside SAP HANA allowing "Zero-Latency" logic execution.

**Q: What is the benefit of N-Bit encoding?**
**A**: It optimizes bit-packing by using the minimum number of bits needed to represent the column's distinct values.

**Q: How do you force a Delta Merge manually?**
**A**: `MERGE DELTA OF "TABLE_NAME" FORCE;`

**Q: What is the Name Server's primary role in a cluster?**
**A**: It maintains the topography of the distributed database (routing tables to nodes).

**Q: What is a "Partitioned Table" in HANA?**
**A**: A massive table split into sub-units (shards) by Hash, Range, or Round-Robin, potentially across nodes.
