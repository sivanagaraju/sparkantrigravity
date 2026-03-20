# Databricks Delta Lake — Further Reading

## Foundational Architecture

| Title | Source | Key Topic |
|---|---|---|
| *Delta Lake: High-Performance ACID Table Storage over Cloud Object Stores* | VLDB Proceedings (2020) | The authoritative academic paper published by Databricks founders (Matei Zaharia, Michael Armbrust). Explicitly details Optimistic Concurrency, the JSON Transaction log math, and how it mathematically guarantees Serializable isolation on S3. |
| *Medallion Architecture* | Databricks Official Blog | The canonical definition of the Bronze (Raw) -> Silver (Filtered) -> Gold (Aggregated) data flow, the absolute standard for modern Lakehouse structuring. |

## Official References

- **Delta Lake Official Documentation**: https://docs.delta.io/latest/index.html (Essential reading for the explicit syntax of `MERGE INTO`, `OPTIMIZE`, and `VACUUM`).
- **Databricks Engineering Blog**: https://databricks.com/blog/category/engineering (Constantly updated with deepest dives on Z-Ordering, Liquid Clustering, and Photon engine integrations).

## Comparative Ecosystem 

| Title | Topic Focus |
|---|---|
| *Apache Iceberg vs. Delta Lake vs. Apache Hudi* | To be a Principal Architect, you must understand the open-source format wars. Research the differences. (Hint: They all basically do the exact same thing—Overlay Parquet with metadata pointers. Delta is backed by Databricks, Iceberg is backed by Snowflake/Netflix, Hudi is backed by Uber). |
