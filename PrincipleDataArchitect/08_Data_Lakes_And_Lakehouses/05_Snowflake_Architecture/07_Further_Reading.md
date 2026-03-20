# Snowflake Architecture — Further Reading

## Foundational Architecture

| Title | Source | Key Topic |
|---|---|---|
| *The Snowflake Elastic Data Warehouse* | SIGMOD Proceedings (2016) | The authoritative, legendary academic paper published by Snowflake's founders (Benoit Dageville, Thierry Cruanes, Marcin Zukowski). Deep diving into the absolute structural mechanics of how they originally decoupled the Cloud Services (Brain) layer from EC2 local disk caches and S3 persistence. |
| *Understanding Micro-Partitions and Data Clustering* | Snowflake Official Documentation | The baseline documentation detailing the literal geometry of Micro-Partitions, how Min/Max metadata pruning works, and why explicit `CLUSTER BY` commands are required when Full Table Scans naturally collapse. |

## Feature Set

| Title | Publisher | Focus |
|---|---|---|
| *Zero-Copy Cloning: Theory and Practice* | Various Engineering Blogs | Essential to understand how pointers duplicate databases in seconds for CI/CD dev flows. |
| *Understanding Multi-Cluster Warehouses* | Snowflake Official Documentation | Explicitly details the logic that triggers Cluster #2 to spin up dynamically when the SQL workload queue exceeds the capacity of Cluster #1, critical for massive high-concurrency BI dashboards. |

## Comparative Ecosystem 

| Title | Topic Focus |
|---|---|
| *Snowflake vs. Databricks (Lakehouse Architecture)* | The modern architectural war. Understand that Snowflake started strictly as a rigid Data Warehouse requiring data to be ingested *into* Snowflake, but was forced to evolve to natively comprehend Apache Iceberg to compete with Databricks providing limitless raw S3 access. |
