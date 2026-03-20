# Databricks Delta Lake — How It Works

Delta Lake looks like sorcery from the outside: providing strict ACID transactional updates against an S3 Object Store that natively prohibits in-place edits. To understand how it works, you must look directly at the underlying file structure.

## 1. The Anatomy of a Delta Table

When you write a DataFrame to S3 using the Delta format, there are exactly two components created in the target directory:

1.  **The Data Files:** Standard, open-source **Apache Parquet** columnar files. These physically hold the bytes of your table.
2.  **The `_delta_log` Directory:** A hidden subdirectory containing a perfectly sequential list of JSON files representing the **Transaction Log**.

```text
s3://my-datalake/users_table/
    ├── _delta_log/
    │   ├── 00000000000000000000.json  (Commit 0)
    │   ├── 00000000000000000001.json  (Commit 1)
    │   └── 00000000000000000002.json  (Commit 2)
    ├── part-00000-xyz.parquet  (Contains Charlie, David)
    ├── part-00001-xyz.parquet  (Contains Eve, Frank)
    └── part-00002-abc.parquet  (Contains Alice v2, Bob)
```

---

## 2. Implementing ACID Transactions (The JSON Log)

Because S3 doesn't have a centralized SQL engine managing locks, Delta uses the `_delta_log` to achieve **Optimistic Concurrency Control**.

### The Flow of a READ Operation
If a Spark cluster wants to query "Commit 2" of the table:
1. It reads the `_delta_log` to determine what happened in Commits 0, 1, and 2.
2. The JSON logs contain explicitly literal arrays of "Added" and "Removed" Parquet file pointers.
   - *Commit 0 JSON:* `add("part-00000.parquet")`
   - *Commit 1 JSON:* `add("part-00001.parquet")`
   - *Commit 2 JSON:* `add("part-00002.parquet"), remove("part-00000.parquet")`
3. Spark mathematically calculates the active state: It must selectively ONLY read `part-00001` and `part-00002`. Even if `part-00000` still physically exists in the S3 bucket, Spark completely ignores it because the transaction log marked it "Removed".

This mechanism prevents "Dirty Reads". If another cluster is halfway through writing a massive 10GB Parquet file, its associated JSON transaction log doesn't exist yet. The reading cluster will therefore never accidentally read a half-written file.

---

## 3. How "Updates" and "Deletes" Physically Work

S3 is completely immutable. You cannot open a Parquet file and overwrite line 50. 
Therefore, how does Delta Lake process this command? 
`UPDATE users SET status = 'Premium' WHERE name = 'Alice'`

1. Spark scans the active Parquet files and locates the exact file containing Alice's row (e.g., `part-00000.parquet` which also contains David).
2. Spark physically copies the *entire contents* of `part-00000.parquet` into its RAM.
3. It mutates Alice's status in RAM, leaving David alone.
4. Spark writes out a brand new file: `part-00005.parquet`.
5. Finally, Spark writes a new JSON commit log to the `_delta_log` stating:
   `remove("part-00000.parquet")`
   `add("part-00005.parquet")`

The old file still exists on disk, but the Delta protocol considers it logically deleted. This is known as **Copy-On-Write (COW)**.

---

## 4. Time Travel

Because the old Parquet files are never physically deleted immediately (they are only marked "removed" in the JSON log), Delta Lake inherently supports **Time Travel**.

If a junior data scientist accidentally runs `DELETE FROM users`, they haven't destroyed the actual Parquet files. They simply appended a new JSON log marking all active files as "removed".

You can query the historical state of the table before the destruction:
`SELECT * FROM users TIMESTAMP AS OF '2023-10-01 12:00:00'`
When you run this, Delta intentionally ignores the newest JSON commit logs and rebuilds the active file list exactly as it existed at noon.

---

## 5. Schema Enforcement and Evolution

Data Lakes frequently suffer from schema rot (e.g., someone uploads a CSV where the `id` column is a STRING instead of an INT, crashing all downstream jobs).
Delta Lake natively leverages **Schema Enforcement**. The official approved schema geometry is saved securely inside the `_delta_log` JSON. 
If an incoming Kafka stream attempts to append a dataframe containing a new undocumented column `social_security_number`, Delta hard-rejects the write and throws an error, protecting the integrity of the data lake.
If developers intentionally want to accept the new column, they can trigger **Schema Evolution** by explicitly passing a `.option("mergeSchema", "true")` flag, cleanly documenting the schema change inside the next JSON commit log.
