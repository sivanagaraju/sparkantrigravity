# 🧠 Mind Map – Amazon S3 & Cloud Storage

---

## How to Use This Mind Map
- **For Revision**: Contrasting Block, File, and Object Storage definitions permanently in your mind.
- **For Application**: Understanding when to utilize Presigned URLs to bypass Web APIs, and designing Hive-partitioned Bucket structures to save thousands of dollars on Athena queries.
- **For Interviews**: Mastering the Decoupled Compute/Storage thesis that defines modern cloud data lakes.

---

## 🗺️ Theory & Concepts

### Decoupled Architecture
- **The Old World (Hadoop/SAN):** To store more data, you must buy expensive CPUs tied to hard drives.
- **The New World (S3):** Infinite, pure geometric storage. Compute (Snowflake/Databricks) is purchased entirely separately and strictly by the hour.

### The Storage Trinity
1.  **Block Storage:** `C:\` drive or AWS EBS. Connects directly to OS. Lightning fast, random access edits. Does not scale horizontally.
2.  **File Storage:** Shared company network drive (NFS). Directory tree structure. Scales moderately, but directory indexes break under global load.
3.  **Object Storage:** S3. A massive HTTP Key-Value database mapping string hashes (`Path/To/String`) to raw binary bytes (`File Data`).

### Resilience Mechanics
- **Erasure Coding:** Files aren't simply "mirrored". They are mathematically shredded into 16 interlocking fragmented equations across 3 datacenters. Surviving 11 fragments can mathematically reconstruct the entire file if a meteor strikes one facility. -> "11 Nines of Durability".

---

## 🗺️ API & Ecosystem Integrations

### Data Processing In-Place
- **S3 Select:** Instead of pulling a 50GB file to your app to find 3 log lines, S3 applies the SQL filter at the disk level and returns only the 3 lines, saving brutal network overhead.

### S3 Prefix (Pseudo-Folders)
- S3 does not have actual folders. The `/` is just another letter in the file name mapping. S3 renders a visual filesystem illusion in the AWS Console for human sanity. 

### Data Tiers
- **S3 Standard:** Fast retrieval. High storage cost / Low retrieval cost.
- **S3 Standard-IA:** Half the storage cost / Charged physically every time you execute a `GET`.
- **S3 Glacier Deep Archive:** Pennies. Takes robots hours to load magnetic tapes. Ideal for 7-year legal minimum retention.

---

## 🗺️ Mistakes & Anti-Patterns

### M01: Node.js Network Saturation
- **Root Cause:** Making mobile apps POST 500 MB videos to your web API.
- **Diagnostic:** Load Balancers crash, RAM maxes out, Web tier falls over.
- **Correction:** Generate an **S3 Pre-signed URL** via the web API. The mobile app uploads physically to S3's infinite bandwidth tier directly, completely bypassing the backend hardware.

### M02: Massive Athena Scans
- **Root Cause:** Dumping 40TB of logs into the root directory of a bucket.
- **Diagnostic:** Athena scans all 40TB to find a single day, charging the company $200 per query.
- **Correction:** Implement pseudo-directory mapping (`/year=2023/month=10/`). Athena executes metadata pruning and only scans the 2GB folder matching the requested month.

### M03: Treating S3 like POSIX
- **Root Cause:** A python script trying to rename a 1 TB file.
- **Diagnostic:** It takes 4 hours because "Rename" on S3 is mathematically required to execute a `COPY` followed by a `DELETE`.

---

## 🗺️ Interview Angle

### Q: Why shouldn't I host my PostgreSQL database directly on S3?
- Assertive Answer: "Because databases require aggressive, nanosecond-level Random Access I/O to lock and mutate explicit rows inside a 5GB file without rewriting it. S3 is entirely immutable and executes via HTTP; you cannot edit byte 400. You must overwrite the entire object. A database requires block storage (EBS)."

### Q: How did the shift from Eventual to Strong Consistency completely alter the Data Lake paradigm?
- Assertive Answer: "Historically, uploading a Parquet file and immediately executing an Apache Spark job `LIST` command occasionally missed the new file, silently dropping data. Amazon rewriting S3 to execute Strong Read-After-Write consistency allowed Data Engineers to legally treat S3 as a flawless transactional file system, destroying the final obstacle to retiring on-premise HDFS universally."
