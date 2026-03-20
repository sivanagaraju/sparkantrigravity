# Real-World Scenarios: SAP HANA

## 01: Walmart — Migrating the World's Largest Supply Chain
- **Scale**: Over 50 million transactions per day, 11,000 stores, processing complex point-of-sale data, inventory routing, and accounting ledgers simultaneously.
- **Architecture Decision**: Walmart modernized their monolithic legacy SAP ERP (ECC) onto S/4HANA in order to achieve real-time insight. They deployed on a massive cluster of HANA scale-out nodes with over **40 Terabytes of RAM**.
- **The Core Problem Solved**: Historically, regional financial close algorithms and supply-chain shortage forecasts were batch jobs run by standard relational databases (Oracle/DB2) overnight. Executive dashboards were 24-hours stale. By deploying HANA, Walmart unified transactional appends (cash registers finalizing orders) with real-time aggregate queries (live global inventory levels), utilizing HANA's Native Storage Extension (NSE) to partition "warm" older receipts to disk while keeping the active fiscal quarter entirely in RAM.
- **Production Result**: Analytics that previously took **days** dropped to **minutes/seconds**, enabling dynamic supply chain rerouting.

## 02: P&G (Procter & Gamble) — The OOM (Out Of Memory) Blackout
- **The Incident**: During end-of-quarter financial processing, a massive set of custom-written supply chain projections were launched concurrently. The SAP HANA system experienced a total catastrophic lockup and crashed globally.
- **Root Cause Analysis (Post-Mortem)**:
  1. Developers launched uncontrolled `JOIN` views across un-optimized schema designs with billions of rows (Cartesian product explosions).
  2. Because HANA requires a physically distinct memory allocation area to compile query result sets (the `Workspace` and `Statement Memory`), these massive temporary tables began to rapidly consume RAM.
  3. Crucially, a **Delta Merge** triggered on the main accounting tables at exactly the same time. During Delta Merge, HANA must hold the old `Main` and the new `Main2` in memory simultaneously (consuming 2x RAM for that table) until the atomic pointer swap.
  4. The absolute OS memory limit was breached, triggering the Linux OOM-killer which violently killed the `hdbindexserver` process (the core HANA engine tier).
- **The Fix**: P&G implemented strict `Statement Memory Limits`. DBAs configured `statement_memory_limit = 100GB`. If a single query attempts to cache intermediate result sets larger than 100GB of RAM due to a bad SQL Cartesian join, HANA actively aborts the singular query transaction and throws a resource error back to the user, thereby saving the overarching database process from cluster destruction.

## 03: The Persistent Memory (PMEM) Hardware Revolution
- **Scale**: Hardware architecture at the datacenter tier.
- **Architecture Decision**: Rebooting a typical Intel node with 6TB of RAM takes an exceptionally long time (sometimes **45 to 60+ minutes**) because HANA must systematically read 6TB of data from NVMe/SSDs and stream it physically onto the DDR4 DIMMs over the motherboard buses before the database allows client connections.
- **Implementation**: Enterprise deployments widely adopted **Intel Optane DC Persistent Memory (PMEM)** modules. These physically plug into standard RAM DDR4 slots on the motherboard, but they are Non-Volatile (they maintain state without power).
- **Production Mechanics**: HANA's Column Store Main structures were explicitly rewritten to understand PMEM. Data is stored locally on the Non-Volatile DIMMs. If the server is restarted (due to patching or a kernel panic), the `hdbindexserver` boots in **seconds**, simply pointing its C++ pointers to the PMEM addresses without reading a single byte from the disk storage subsystem. This fundamentally altered enterprise RTO (Recovery Time Objectives) for tier-1 SAP billing architectures.

## The Hardware Topology of an Enterprise Node

```mermaid
graph TD
    classDef cpu fill:#2d3436,stroke:#b2bec3,stroke-width:2px,color:#dfe6e9;
    classDef nvdimm fill:#e17055,stroke:#fab1a0,stroke-width:2px,color:#fff;
    classDef dram fill:#d63031,stroke:#ff7675,stroke-width:2px,color:#fff;
    classDef ssd fill:#0984e3,stroke:#74b9ff,stroke-width:2px,color:#fff;

    subgraph "Server Rack Hardware"
        CPU1[Socket 0: Intel Xeon Platinum 28-Core]:::cpu
        CPU2[Socket 1: Intel Xeon Platinum 28-Core]:::cpu
        
        subgraph "Memory Bus 0"
            RAM1[volatile DDR4 \nDelta Store / Caches]:::dram
            NVRAM1[Intel Optane PMEM \nMain Column Store]:::nvdimm
        end
        
        subgraph "Memory Bus 1"
            RAM2[volatile DDR4 \nDelta Store / Caches]:::dram
            NVRAM2[Intel Optane PMEM \nMain Column Store]:::nvdimm
        end
        
        NVME[(NVMe Data & Log Volumes)]:::ssd
    end

    CPU1 <-->|Memory Controller| RAM1
    CPU1 <-->|Memory Controller| NVRAM1
    CPU2 <-->|Memory Controller| RAM2
    CPU2 <-->|Memory Controller| NVRAM2
    
    CPU1 <-->|UPI Link (NUMA Penalty)| CPU2
    
    RAM1 -.->|Async Savepoints / Fsync| NVME
    RAM2 -.->|Async Savepoints / Fsync| NVME
```
*Note: Due to NUMA (Non-Uniform Memory Access) architectures, if CPU1 needs data residing on PMEM attached to CPU2, it must travel over the UPI link, adding nanoseconds of latency. HANA actively optimizes thread placement (`NUMA node affinity`) to ensure SQL computation happens on the physical CPU socket closest to the memory modules housing the partition of the table being queried.*
