# Time-Series Databases — Interview Angle

## How This Appears in System Design Interviews

System design interviews for mid-to-senior levels often transition into TSDB territory when the prompt is: *"Design a system like CloudWatch,"* *"Design a metrics dashboard for 10,000 servers,"* or *"Design a high-frequency trading ticker."*

The core evaluation is whether you understand **Storage Engine Specialization**. If you suggest storing millions of metrics per second in a standard MySQL table, you have failed the "Scale" portion of the rubric.

## Sample Questions

### Question 1: Solving the High Cardinality Problem
**Interviewer**: *"You're building a metrics system for a multi-tenant cloud provider. A user wants to add 'Client IP' as a label to every HTTP request metric. What is the risk and how do you mitigate it?"*

*   **Weak Answer (Senior)**: "The database will get slow because IP addresses are unique. We should tell the user not to do it or use a bigger instance."
*   **Strong Answer (Principal)**: "This is a **Cardinality Explosion** risk. Every unique IP creates a new time-series entry in the inverted index. At scale, this index will exceed RAM and cause OOM or disk thrashing. I would mitigate this by: (1) Implementing 'Cardinality Quotas' at the ingestion gateway. (2) Suggesting the user move IP tracking to a Logging layer (Loki/ES) or a distributed tracing system. (3) If they must have it in TSDB, I'd use a 'sketch' data structure like HLL (HyperLogLog) to estimate unique IPs without storing every series explicitly."

### Question 2: Designing for Multi-Year Retention
**Interviewer**: *"We need to store sub-second metrics for 3 years for compliance, but querying 3 years of raw data is too slow. How do you architect the storage?"*

*   **Strong Answer**: "I would implement a **Tiered Storage and Downsampling** strategy. Raw data (100ms resolution) stays in the 'Hot' tier (SSD/In-Memory) for 7 days. An asynchronous process runs 'Rollup' queries to aggregate that data into 1-minute buckets (Mean, Max, Min, Count) and stores it in the 'Warm' tier (S3/Object Storage) for 6 months. Finally, 1-hour rollups are stored for 3 years. The query coordinator is made 'Hierarchy-Aware' so it automatically picks the coarser-grained resolution if the user queries a wide time window."

## What They're Really Testing

1.  **Compression Knowledge**: Do you know about Gorilla (XOR) or Delta-Delta encoding?
2.  **Trade-offs between SQL and Custom Engines**: Why use Timescale vs InfluxDB?
3.  **Indexing Depth**: Understanding why B-Trees fail for temporal order and why Inverted Indexes are used for labels.

## Whiteboard Exercise: TSM File Internal Layout

You should be able to sketch how a Time-Structured Merge (TSM) file is laid out on disk to enable fast scans.

```mermaid
graph TD
    subgraph "TSM File Structure (Disk)"
        Header[Header: Version/Magic]
        
        subgraph "Data Blocks (Compressed)"
            B1[Block 1: Series 1001, Time 1-100]
            B2[Block 2: Series 1001, Time 101-200]
            B3[Block 3: Series 1002, Time 1-100]
        end
        
        subgraph "Index (Trailing)"
            IDX1[Series 1001: Offset 0, Len 500]
            IDX2[Series 1002: Offset 500, Len 250]
        end
        
        Footer[Footer: Index Offset]
    end
    
    Note over IDX1, IDX2: The Index is at the END of the file<br/>so it can be written in one atomic flush.
```
