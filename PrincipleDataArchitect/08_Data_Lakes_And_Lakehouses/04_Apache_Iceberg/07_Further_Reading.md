# Apache Iceberg — Further Reading

## Foundational Architecture

| Title | Source | Key Topic |
|---|---|---|
| *Apache Iceberg: An Architectural Look Under the Covers* | Dremio / YouTube | Highly recommended deep dive into the explicit JSON, Avro Manifest list, and Parquet data topology structure. |
| *To Data Warehouse, Data Lake, or Lakehouse?* | Netflix TechBlog (Medium) | The original essay from the engineers at Netflix detailing specifically why they broke away from Hive and engineered the first iterations of Iceberg to manage their Petabyte-scale metadata problem. |

## Mechanics

| Title | Publisher | Focus |
|---|---|---|
| *Hidden Partitioning in Apache Iceberg* | Apache Software Foundation Docs | Defines the literal math and transforms behind how Iceberg escapes the physical S3 nested folder trap using the `years(), months(), days(), hours()` syntax layer. |
| *Iceberg Catalogs Explained* | Tabular Blog (Creators of Iceberg) | An explanation addressing the concurrency lock: explaining why you absolutely must use an ACID-compliant catalog like Nessie, DynamoDB, or AWS Glue, rather than file-system locking or weak MySQL instances, to lock the pointer swaps. |

## Evolution vs Hudi and Delta

| Title | Author | Focus |
|---|---|---|
| *The Open Table Format War* | Databricks / Snowflake Keynotes | Look for competing corporate keynotes detailing why Databricks Delta Lake heavily pushes proprietary Spark features (like Liquid Clustering) while the broader ecosystem (Snowflake, AWS) fiercely standardizes completely on Iceberg interoperability. |
