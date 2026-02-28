# 15 — Data FinOps & Cost Management

> "The CEO doesn't care about your elegant architecture. They care about the $2.3 million monthly cloud bill and why it went up 40% this quarter."

Data workloads are typically the #1 or #2 line item on a company's cloud bill. A Principal Architect who can reduce data costs by 50% without degrading performance is worth their weight in gold. FinOps for data is a strategic capability, not a tactical exercise.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Cloud_Cost_Economics/`

- **The Compute-Storage Separation ROI**: Why separating compute from storage (Snowflake, BigQuery, Databricks SQL Warehouses) changed the economics — you no longer pay for idle compute on data you're not querying.
- **On-Demand vs. Reserved vs. Spot**: On-demand (pay per use, most expensive), Reserved/Committed (1-3 year contracts, 40-60% discount), Spot/Preemptible (up to 90% discount, but can be terminated mid-job). Designing fault-tolerant Spark pipelines that gracefully handle spot instance termination.
- **Egress Cost Landmines**: Moving data out of a cloud provider is expensive ($0.08-0.12/GB). Cross-region replication, multi-cloud federations, and even downloading query results to a BI tool all incur egress. Architectures that minimize data movement.

### `02_Query_Cost_Optimization/`

- **Snowflake Credits**: Understanding warehouse sizes (XS = 1 credit/hour, 4XL = 128 credits/hour). Why a query on an XL warehouse for 10 seconds costs the same as running it for 60 seconds (per-second billing with 60-second minimum).
- **BigQuery Bytes-Scanned Pricing**: $5 per TB scanned. Partitioning + clustering can reduce a $50 query to $0.05. Using `SELECT *` on a 1PB table is a career-limiting move.
- **Redshift Cost Patterns**: RA3 nodes (pay separately for compute and storage). Spectrum queries (pay per TB scanned from S3). Choosing between dense compute (CPU-bound) vs. dense storage (I/O-bound) nodes.
- **Query Cost Governance**: Pre-execution cost estimation. Query tagging to attribute costs to teams. Automatic query timeout policies for runaway queries.

### `03_Storage_Optimization/`

- **Storage Tiering Lifecycles**: Automatically moving data from hot (S3 Standard, $0.023/GB/month) → warm (S3 IA, $0.0125) → cold (S3 Glacier, $0.004) → archive (Glacier Deep Archive, $0.00099). Designing lifecycle policies based on access patterns.
- **Compression ROI**: Choosing Zstd (high compression, moderate CPU) vs. Snappy (low compression, fast CPU). A 3:1 compression ratio on 100TB saves $2,760/month in S3 storage costs alone.
- **Small File Consolidation**: 1 million 1KB files cost more to store (API request charges) and query (metadata overhead) than 1 single 1GB file. Automated compaction schedules.

### `04_Chargeback_And_Showback_Models/`

- **Chargeback**: Actually billing business units for their data consumption. Requires accurate tagging, cost allocation, and a billing system.
- **Showback**: Showing teams their costs without actually billing them. Lower friction to implement, still drives cost-conscious behavior.
- **Tagging Strategy**: Enforcing `team`, `project`, `environment`, `data-product` tags on every cloud resource. Untagged resources should be flagged and eventually terminated.
- **Unit Economics for Data**: Calculating "cost per data product," "cost per query," "cost per active user served." Making data platform costs as visible as SaaS subscription costs.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
