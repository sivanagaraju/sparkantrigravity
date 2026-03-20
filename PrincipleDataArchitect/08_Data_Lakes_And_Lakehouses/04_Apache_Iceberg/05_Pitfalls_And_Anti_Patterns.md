# Apache Iceberg — Pitfalls and Anti-Patterns

## Anti-Pattern 1: The "Small Files" Metadata Explosion

While Iceberg mathematically solves the *S3 Directory Listing* bottleneck, it does not solve the fundamental laws of physics regarding downloading millions of tiny files over the internet.

### The Trap
A Kafka streaming application writes a new Iceberg commit every 500 milliseconds. 
Each commit creates a new `metadata.json`, a new `Manifest List`, a new `Manifest`, and three tiny 5 KB `Parquet` files.
Over the course of a week, you generate 1.2 million JSON metadata files and 3.6 million tiny Parquet files.
When an analyst tries to query the table, Iceberg has to download thousands of JSON manifests and millions of 5 KB Parquet files. The Iceberg query planner mathematically collapses under the weight of parsing the sheer volume of Avro/JSON column statistics, and the SQL Engine (Trino/Spark) spends 99% of its time establishing TCP handshakes to download tiny files instead of actually crunching data.

### Concrete Fix
Like Delta Lake, Iceberg requires rigorous background compaction procedures.
- **Correction:** Implement an asynchronous background maintenance job (using Airflow or an AWS Lambda) that continually runs:
  `CALL catalog.system.rewrite_data_files('events');`
- This command reads the massive fragmented tail of tiny Parquet files, crunches them into optimal 1 GB files in the background, and seamlessly swaps the active metadata pointers to the new, clean 1 GB files without interrupting live queries.

---

## Anti-Pattern 2: The Finite Catalog Bottleneck

Every single transaction executed against an Iceberg table requires the exact same final step: **An atomic swap inside the Catalog layer.** Iceberg uses this catalog (AWS Glue, Hive Metastore (HMS), DynamoDB, Nessie) as the single source of truth to lock the table pointer.

### The Trap
A massive global gaming company attempts to use an outdated, on-premise MySQL-backed Hive Metastore (HMS) as their central Iceberg Catalog.
During a massive promotional event, 5,000 parallel microservices attempt to execute separate `INSERT` operations into the same Iceberg table roughly simultaneously.
Because each microservice has to update the central HMS, the MySQL database begins to lock rows. 5,000 parallel Optimistic Concurrency requests slam into the single MySQL CPU, causing a catastrophic database deadlock. The MySQL HMS crashes, and every single Iceberg write pipeline horizontally across the entire global company fails instantly.

### Concrete Fix
The Catalog must be highly available and horizontally scalable.
- **Correction:** Iceberg explicitly requires massive cloud-native Catalogs for high-concurrency workloads. You must utilize **AWS Glue**, **Project Nessie**, or a native **Amazon DynamoDB** catalog. These systems are specifically engineered to handle thousands of concurrent optimistic locking requests per second without crumbling.

---

## Anti-Pattern 3: Unbounded Snapshot Retention (The FinOps Crisis)

Because Iceberg provides Time Travel capabilities, it explicitly utilizes the "Copy-On-Write" or "Merge-On-Read" principles. It fundamentally never physically deletes older data unless explicitly commanded to.

### The Trap
An analytics team drops an old 2-Terabyte table partition using a standard `DELETE FROM` SQL operation. They verify the data is gone visually when querying the table.
Six months later, the finance team notices the AWS S3 bill has not decreased at all. 
Because Iceberg provides Time Travel, the `metadata.json` merely stopped pointing to those specific Parquet files. The 2-Terabyte Parquet files are still sitting comfortably inside the S3 bucket, completely invisible to standard `SELECT` statements, but physically racking up AWS storage costs every single month.

### Concrete Fix
You must mathematically sever the Time Travel lifeline to reclaim physical hard drive space.
- **Correction:** Schedule a routine execution of the Expire Snapshots command:
  `CALL catalog.system.expire_snapshots('table_name', TIMESTAMP 'X');`
- This command forces Iceberg to explicitly issue HTTP `DELETE` commands to S3, permanently destroying any un-referenced Parquet objects that are older than Timestamp X. By running this daily, you cap your Time Travel window at exactly 7 days, capping your AWS FinOps cost strictly.
