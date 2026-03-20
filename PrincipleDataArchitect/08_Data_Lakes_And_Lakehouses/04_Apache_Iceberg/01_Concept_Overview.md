# Apache Iceberg — Concept Overview

## Why This Exists

To understand Apache Iceberg, you have to understand the catastrophic bottleneck Netflix hit with traditional Hive/Hadoop Data Lakes running on Amazon S3.

Historically, to query a massive Parquet table, data engines like Presto or Apache Spark relied on the **Hive Metastore** and physical S3 folder paths (e.g., `s3://data/year=2023/month=10/`). 
1. When you ran a query for October, the engine would literally ask S3: *"Please list all files inside the `month=10` directory."*
2. If the folder contained 500,000 Parquet files (because of heavy streaming), S3's `LIST` API inherently choked. S3 only returns 1,000 objects per API call. Listing 500,000 files required 500 sequential network requests over the internet before the query even started processing a single byte of data.

Netflix essentially discovered that **Directory structures are fundamentally broken at Petabyte scale.**

In 2018, Netflix open-sourced a radical new architecture to solve this: **Apache Iceberg**, an *open table format*.

---

## What is Apache Iceberg?

Iceberg is fundamentally similar to Databricks Delta Lake (it provides ACID transactions, Time Travel, and Upserts on top of underlying Parquet files). 
However, its architectural philosophy is violently different.

**Iceberg tracks individual files, not directories.**

By utterly abandoning the concept of S3 "folders" and instead maintaining an explicit, microscopic tree hierarchy of metadata files, Iceberg allows engines to physically skip the S3 `LIST` API completely. 

When Presto queries an Iceberg table, it reads a single master `metadata.json` file. That file points to a `Manifest List`, which explicitly lists exactly which 5 specific Parquet files contain the target data, down to the exact byte offset and column statistics. Presto instantly issues 5 exact `GET` requests for those files.

What took Apache Hive 4 minutes of metadata listing, Iceberg executes in 30 milliseconds.

---

## The "Open" Architecture War

Delta Lake, Apache Hudi, and Apache Iceberg are currently fighting a massive architectural war for dominance over the next decade of cloud data.

**Why Iceberg is Winning the Open Source War:**
Delta Lake was built by Databricks. While it is open-source, it is fundamentally optimized for the Databricks Apache Spark engine.
Apache Iceberg was explicitly designed to be **Engine Agnostic**. 
Because Iceberg standardizes the exact format of the metadata JSONs, it serves as an open contractual treaty between completely fierce corporate rivals.
Using Iceberg, you can explicitly have an **AWS EMR Spark cluster** streaming writes into a table on S3, while a **Snowflake** cluster, a **Databricks** cluster, and an **AWS Athena** query all read from that exact same S3 table simultaneously, with perfect transactional safety and zero vendor lock-in.

---

## "Hidden Partitioning" (The Engineering Miracle)

In legacy Hive/Delta architectures, partitioning was a massive headache. If you partitioned your logs by `date`, your application fundamentally had to inject a literal `date` string column into the dataframe so that it physically routed to the `date=2023-10-01` S3 folder. If the business suddenly decided to query by `hour` instead, you had to rewrite the entire multi-petabyte dataset.

Iceberg introduces **Hidden Partitioning**.
Instead of forcing the data layout to physically match the directory string, Iceberg creates mathematical partition transforms in the metadata layer.
You simply supply standard `timestamp` columns. You tell Iceberg: *Partition this table by `days(timestamp)`*. 
When a user writes a standard SQL query `SELECT * FROM table WHERE timestamp > '2023-10-01'`, Iceberg intelligently does the math, translates the timestamp into the partition bounds hidden in the metadata layer, and skips the irrelevant files. The user writing the SQL query literally does not need to know the table is partitioned, and the data engineers can completely alter the partition strategy in the background without rewriting a single Parquet file.
