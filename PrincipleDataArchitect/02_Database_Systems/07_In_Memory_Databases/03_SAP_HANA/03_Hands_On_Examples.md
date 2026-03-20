# Hands-On Examples: SAP HANA

*Note: SAP HANA relies heavily on its proprietary SQL dialect (HANA SQLScript) and specialized architectural monitoring views rather than standard open-source client loops.*

## Scenario 1: Forcing and Monitoring the Delta Merge

If background processes fail or large batches finish during ETL, Delta stores bloat and destroy read performance. DBAs often manually force a Delta Merge.

### ❌ Before (Anti-Pattern)
Loading 50 million rows into a Column table via a nightly batch, leaving the system to auto-merge asynchronously.
```sql
-- Huge batch load completed
IMPORT FROM CSV FILE '/data/sales_history_2023.csv' INTO "FACT_SALES";
-- Queries immediately after the load will take 10x longer because 
-- the query engine has to scan 50 million uncompressed rows in the L1/L2 Delta store via row-pointers.
```

### ✅ After (Correct Approach)
Manually triggering an aggressive merge immediately after batch completion.
```sql
-- Trigger merge synchronously
MERGE DELTA OF "FACT_SALES";

-- Monitor the merge execution and memory spike
SELECT 
    HOST, 
    TABLE_NAME, 
    MEMORY_SIZE_IN_MAIN, 
    MEMORY_SIZE_IN_DELTA, 
    RECORD_COUNT_IN_MAIN, 
    RECORD_COUNT_IN_DELTA
FROM M_CS_TABLES 
WHERE TABLE_NAME = 'FACT_SALES';
```
**Result:** Queries instantly utilize SIMD scanning against the fully bit-packed Main array, dropping execution time from 40 seconds to 0.8 seconds.

---

## Scenario 2: Data Tiering (Native Storage Extension - NSE)

Using 5TB of pure RAM just to store 10-year-old closed invoices is financially irresponsible. Modern HANA implements Data Aging / NSE where you declare data as "Warm" (SSD-bound, Paged to RAM) instead of "Hot" (Resides in RAM completely).

### ❌ Before (Anti-Pattern)
Loading historic tables identically to active transactional tables.
```sql
CREATE COLUMN TABLE INVOICE_HISTORY (
  INV_ID INT PRIMARY KEY,
  YEAR INT,
  AMOUNT DECIMAL(10,2)
);
-- Over 10 years, this consumes 400GB of $50k/TB RAM.
```

### ✅ After (Correct Approach)
Using HANA NSE to explicitly mark the table (or specific partitions) for PAGE LOAD (Warm storage).
```sql
-- Creating a table bound for NVMe/SSD persistence, loaded into RAM only in 4KB/16KB pages when explicitly queried
CREATE COLUMN TABLE INVOICE_HISTORY (
  INV_ID INT PRIMARY KEY,
  YEAR INT,
  AMOUNT DECIMAL(10,2)
) PAGE LOADABLE;

-- Or altering an existing table to evict it from permanent RAM:
ALTER TABLE INVOICE_HISTORY PAGE LOADABLE;
ALTER TABLE INVOICE_HISTORY UNLOAD; 

-- Querying the Buffer Cache (RAM hit/miss ratio for page-able data)
SELECT * FROM M_BUFFER_CACHE_STATISTICS;
```
**Result:** Free up 400GB of main RAM memory. Analytic queries on 2012 data slow down from 0.5s to 2.5s (acceptable for historical analysis).

---

## Scenario 3: Aggregation via HANA Core Data Services (CDS) vs SQL Views

In traditional databases, you construct complex `CREATE VIEW` objects. In modern S/4HANA, logic is heavily pushed into ABAP CDS Views that compile directly into deep native HANA engine execution plans.

### ❌ Before (Anti-Pattern - The Application Layer Join)
Pulling raw data into the SAP Application Server (ABAP) and looping to sum values.
```abap
" (ABAP Pseudo-code run on the application server)
SELECT * FROM VBAK INTO TABLE lt_vbak. " Pulls 10 million rows across the network
LOOP AT lt_vbak INTO ls_vbak.
  Total_Rev = Total_Rev + ls_vbak-netwr.
ENDLOOP.
```
**Result:** 800MB network transfer. High latency. Abysmal performance. Known as the "Data-to-Code" paradigm.

### ✅ After (Correct Approach - Code-to-Data)
Creating a HANA CDS view that leverages the database engine directly.
```cds
@AbapCatalog.sqlViewName: 'ZSALES_AGGR_V'
@ClientHandling.type: #CLIENT_DEPENDENT
define view Z_Sales_Aggregation as select from vbak as SalesOrder {
    key SalesOrder.vbeln,
    SalesOrder.vkorg as SalesOrg,
    sum(SalesOrder.netwr) as TotalRevenue
} group by
    SalesOrder.vbeln,
    SalesOrder.vkorg
```
**Result:** Only the summarized absolute final number is transferred over the network (1 KB). The entire computation executes directly inside the HANA C++ core engines utilizing multi-threaded vector scans.

---

## Scale-Out Architecture Diagram

For massive deployments (e.g., 20TB of RAM needed, but the largest Cisco hardware only supports 6TB arrays), HANA is clustered into a Scale-Out architecture.

```mermaid
graph TD
    classDef client fill:#2d3436,stroke:#b2bec3,stroke-width:2px,color:#dfe6e9;
    classDef coord fill:#e17055,stroke:#fab1a0,stroke-width:2px,color:#fff;
    classDef worker fill:#d63031,stroke:#ff7675,stroke-width:2px,color:#fff;
    classDef disk fill:#0984e3,stroke:#74b9ff,stroke-width:2px,color:#fff;

    App[SAP Application Servers]:::client
    
    subgraph "HANA Distributed Cluster (Scale-Out)"
        Coord[Master Node\n(Coordinator / Name Server)]:::coord
        W1[Worker Node 1\n(Index Server)]:::worker
        W2[Worker Node 2\n(Index Server)]:::worker
        W3[Standby Node 3\n(Idle / Failover)]:::worker
    end
    
    subgraph "Global Shared Storage (Fiber Channel)"
        SAN[(Cluster Shared Volumes)]:::disk
    end

    App -->|SQL Connection| Coord
    Coord -.->|Statement Routing| W1
    Coord -.->|Statement Routing| W2
    
    W1 -->|Reads Part 1 of Table A| W1
    W2 -->|Reads Part 2 of Table A| W2
    
    W1 -->|Writes| SAN
    W2 -->|Writes| SAN
    
    W1 -.->|Node Crash Detect| W3
    W3 -.->|Claims W1 Memory Space from Disk| SAN
```
**Mechanism**: Tables are physically partitioned across Worker Nodes. When a massive aggregation hits, the Coordinator instructs W1 and W2 to scan their local RAM segments simultaneously in parallel, merging the final results at the Coordinator before returning to the App. The Standby Node reads nothing until a physical crash, at which point it dynamically adopts the crashed node's IP mapping and loads its data from Shared Storage.
