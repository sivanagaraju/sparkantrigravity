# 🧠 Mind Map – Apache Iceberg

---

## How to Use This Mind Map
- **For Revision**: Understanding the specific 3 layers of an Iceberg Table (Catalog > Metadata > Manifest).
- **For Application**: Grasping how to utilize `Hidden Partitioning` to avoid writing brutal 5-day Spark migration jobs. 
- **For Interviews**: Mastering the conceptual origin of Iceberg: curing the S3 massive directory `LIST` API bottleneck.

---

## 🗺️ Theory & Concepts

### The S3 LIST Bottleneck (The Problem)
- **Hive:** To execute a `SELECT` query, the engine literally asks S3 to list all the files inside `s3://year=2023/month=10/`. If that folder has 1 million files, S3 chokes. Network transit alone takes 10+ minutes before data is even processed.
- **Iceberg:** Explicitly tracks file routes inside a massive external index tree. The `LIST` command is completely bypassed by explicitly jumping exactly to the referenced physical byte ranges using parallel `GET` requests.

### Open vs Closed (The Business Logic)
- **Delta:** Originated by Databricks, leans heavily into Spark dominance.
- **Iceberg:** Built for **Engine Agnosticism**. Allows Spark, Flink, Trino, and Snowflake to flawlessly execute massive parallel queries and mutations against a single S3 bucket globally with zero data duplication.

---

## 🗺️ The Architecture (The Inverted Tree)

### 1. The Catalog (The Pointer)
- AWS Glue, DynamoDB, or Nessie.
- Defines the absolute singular truth: *"The absolute latest state of the table currently lives at `metadata v144.json`"*
- Guarantees Optimistic Concurrency atomicity during simultaneous writes.

### 2. The Metadata Layer (The Routing Map)
- **metadata.json:** The root file. Contains schema geometry and points to a single *Manifest List*.
- **Manifest List (Avro):** Explains broadly which partitions live where. Points downward to the *Manifests*.
- **Manifests (Avro):** Explains exactly which explicit Parquet files physically hold the data, tracking Min/Max column statistics to allow the SQL engine to completely skip irrelevant Parquet files.

### 3. The Data Layer (The Bytes)
- Standard open-source `Parquet` or `ORC` files scattered haphazardly inside S3 geometry.

---

## 🗺️ Transformative Mechanics

### Hidden Partitioning
- You don't create "Year" or "Day" strings inside your dataframe.
- You supply standard Timestamps. Iceberg executes mathematical partitioning natively inside the metadata layer.
- **Benefit:** You can execute `ALTER PARTITION strategy` seamlessly. Iceberg magically adapts new incoming data to new bounds while correctly reading historical data based on previous bounds. Zero Parquet files must be read or rewritten to execute this.

### Schema Evolution
- Iceberg references table columns by Internal Unique Integer IDs, not explicit string Names (e.g. `user_id` is tracked globally as `column #4`).
- Dropping, renaming, or expanding columns is a millisecond metadata shift. You never touch or rewrite historic S3 hard drive bits.

---

## 🗺️ Mistakes & Anti-Patterns

### M01: FinOps Time Travel Bloat
- **Issue:** Like Delta, Iceberg retains old JSON metadata trees and dead Parquet files indefinitely.
- **Correction:** Must execute `expire_snapshots` logic systematically to trigger physical AWS hard drive deletion rules.

### M02: Small File Metadata Collapse
- **Issue:** Micro-streaming writes millions of 5 KB Parquet files, bloating the JSON/Avro manifest lists until Spark literally crashes trying to load the map into RAM before the query starts.
- **Correction:** Must execute the `rewrite_data_files` and `rewrite_manifests` commands asynchronously in the background.
