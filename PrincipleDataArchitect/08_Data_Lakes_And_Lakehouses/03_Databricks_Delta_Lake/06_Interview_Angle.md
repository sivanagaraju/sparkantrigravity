# Databricks Delta Lake — Interview Angle

## How This Appears

Delta Lake (alongside Apache Iceberg and Apache Hudi) represents the absolute cutting edge of the "Data Lakehouse" architectural shift. 

Interviews at high-scale tech companies or heavy Data Engineering roles will almost always anchor around *why* Lakehouses were invented, and the specific mechanical magic of how they overlay ACID transactions on top of dumb Object Storage.

---

## Sample Questions

### Q1: "What is the specific architectural difference between a Data Lake and a Data Lakehouse?"

**Weak answer (Senior):** "A Lakehouse is Databricks. It lets you write SQL on top of S3 files like Parquet."

**Strong answer (Principal):** 
"A Data Lake (like pure S3 Parquet) offers infinite, decoupled storage but fundamentally lacks transactional integrity. If a Spark job crashes mid-write, the data lake is corrupted with half-written files. You cannot perform a SQL `UPDATE` or `DELETE` natively without rewriting entire multi-terabyte datasets manually.
A Data Lakehouse (powered by Delta Lake or Iceberg) solves this mathematically. It sits on top of standard open-source Parquet files but introduces a strict JSON Transaction Log. By forcing the compute engine to consult the log before reading or writing, the Lakehouse provides strict ACID guarantees, atomic Upserts (MERGE), and Schema Enforcement, merging the reliability physics of an Oracle Data Warehouse directly onto the cheap infinite storage of S3."

---

### Q2: "A Junior Engineer deleted the active `users` Delta table in production, but they assure you they can fix it using Delta 'Time Travel'. How exactly does Time Travel work mechanically behind the scenes?"

**Strong answer (Principal):**
"S3 is inherently immutable. Therefore, Delta Lake handles all `UPDATE` and `DELETE` commands using **Copy-on-Write (COW)**.
When the junior developer executed that DROP or DELETE command, Delta did not immediately invoke the AWS API to physically delete the physical Parquet files containing the users. 
Instead, Delta generated a brand-new JSON commit in the `_delta_log` directory. Inside that JSON, it simply added an array element saying: `remove("part-all-users.parquet")`. 
Because the old Parquet files still physically exist securely on the S3 hard drives, "Time Travel" simply instructs the Spark engine to ignore the newest JSON commit log, rewind to the previous version, and reconstruct the table layout as it existed linearly in history. We can permanently recover the table using the `RESTORE TABLE` command."

---

### Q3: "Our AWS Bill for S3 has quadrupled this month. The only architectural change we made was converting our nightly pure 'Append' Parquet batch pipeline into a continuously streaming Delta 'MERGE INTO' (Upsert) pipeline executing every 5 minutes. Why is S3 so expensive now?"

**Strong answer (Principal):**
"Because we migrated from an 'Append' pipeline to a heavy 'Update' Delta pipeline, we invoked Delta's strict Copy-On-Write mechanics. 
Every 5 minutes, Spark pulls a 1GB Parquet file, mutates 10 rows in RAM, writes a brand new 1GB Parquet file back to S3, and legally "deletes" the old one in the `_delta_log`. 
However, Delta retains the old Parquet files physically on S3 to support Time Travel. We are effectively copying 1GB of data every 5 minutes and keeping all 288 daily copies blindly on our AWS bill as invisible ghost files.
To solve this instantly, we must schedule a daily Databricks job executing the `VACUUM RETAIN 168 HOURS` command against that table. This physically issues S3 API Destroys against any JSON 'removed' Parquet file older than 7 days, mathematically capping our storage retention exponential growth."

---

## What They're Really Testing

1. **Parquet Geometry:** Do you actually understand that S3 cannot mutate files? Do you grasp Copy-On-Write? 
2. **ACID Mechanics:** Do you understand the conceptual layer spacing between the physical raw data (Parquet) and the logical metadata pointer engine (JSON Log)?
3. **FinOps (Financial Operations):** Are you dangerous enough to accidentally cost the company hundreds of thousands of dollars by failing to Vacuum heavy volatile streaming tables?
