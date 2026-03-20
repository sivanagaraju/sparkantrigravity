# Apache Iceberg — How It Works

To understand how Apache Iceberg executes Petabyte-scale queries in milliseconds while bypassing S3 directory listings, you must examine its strict **three-tier tree architecture**. 

Unlike Delta Lake (which uses a flat `_delta_log` directory of sequential JSON files), Iceberg is fundamentally constructed as an inverted tree specifically designed to be pruned aggressively by SQL optimizers.

---

## The Three Layers of Iceberg

Every Iceberg table is mechanically divided into three distinct physical layers:

### 1. The Catalog Layer (The Pointer)
Because Iceberg tracks files instead of folders, readers need to know exactly which `metadata.json` file represents the absolute latest "current state" of the table. You cannot just put a file named `latest.json` in S3 because S3 doesn't support atomic file overwrites.
You must use an external **Catalog**.
Common catalogs include AWS Glue, Nessie, DynamoDB, or a Hive Metastore. 
When a Spark cluster executes `SELECT * FROM users`, it first pings the AWS Glue Catalog. Glue responds: *"The current state of the table is defined exactly in `s3://bucket/metadata/v145.metadata.json`."*

### 2. The Metadata Layer (The Tree)
This is the core engineering miracle of Iceberg. It is a three-level inverted tree structure.

1.  **Metadata File (`v145.metadata.json`):** 
    Stores the table schema, partition configuration, and exactly one pointer to the current `manifest-list`.
2.  **Manifest List (`snap-89123.avro`):** 
    A list of Manifests. Crucially, it stores partition metadata (e.g., *"Manifest A contains data for 2023, Manifest B contains data for 2024"*). If the SQL query requires 2024 data, the engine completely ignores Manifest A without ever downloading it.
3.  **Manifest Files (`abc-001.avro`):** 
    A list of the actual physical Parquet data files. Crucially, it tracks column-level Min/Max statistics for every Parquet file (e.g., *"File 1 contains User IDs 1-50, File 2 contains User IDs 51-100"*). If the SQL query is `WHERE user_id = 42`, the engine completely ignores File 2.

### 3. The Data Layer
The absolute bottom of the tree. Standard `Apache Parquet` or `ORC` files sitting blindly in S3. 
Notice that their physical folder location inside S3 doesn't matter at all anymore. The path could be a completely random string of UUIDs, because the Manifest Files explicitly define exactly where they are.

---

## Mechanics: An INSERT Operation

How does an `INSERT` mathematically happen without locking the entire table?

1.  Spark spins up and writes three brand new `Parquet` files deep into the S3 bucket.
2.  Spark creates a new `Manifest File` tracking the column min/max statistics of those three new Parquet files.
3.  Spark generates a new `Manifest List` that includes all the pre-existing historic manifests, *plus* the new manifest it just created.
4.  Spark creates `v146.metadata.json` pointing to the new Manifest List.
5.  **The Atomic Commit:** Spark attempts an atomic "Swap" operation inside the AWS Glue Catalog, changing the current pointer from `v145` to `v146`. 
6.  If another job beat it to the punch and wrote `v146` a millisecond earlier, the Catalog rejects the swap (Optimistic Concurrency). Spark simply generates `v147.metadata.json` and tries the swap again.

---

## Mechanics: Schema Evolution without Rewrites

In traditional Hadoop, if you dropped a column from a massive table, the engine would violently crash if it read an older Parquet file that still physically contained that column byte-data.

**Iceberg Schema Evolution is an entirely metadata operations.**
When you execute `ALTER TABLE users DROP COLUMN phone_number`, Iceberg simply writes a new `metadata.json` assigning a new internal schema ID. 
Iceberg tracks columns by a unique integer ID, not by their string name (`phone_number`). 
If a reader queries an older Parquet file under the new schema ID, the Iceberg library mechanically masks the `phone_number` integer ID out of the result set completely in memory. The physical Parquet file is never rewritten, but the column magically functionally disappears for all downstream users.
