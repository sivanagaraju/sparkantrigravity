# Databricks Delta Lake — Hands-On Examples

The power of Delta is that it seamlessly extends the standard Apache Spark DataFrame API and pure ANSI SQL with transactional superpower features.

## Scenario 1: Initializing and Writing to a Delta Table

When writing massive datasets from Pandas or standard Spark, converting from a brittle Data Lake (Parquet) to a robust Lakehouse (Delta) requires changing exactly one word in the API.

### Execution (PySpark)

```python
# Assume we have a massive incoming Kafka dataframe consisting of 5,000,000 rows
raw_stream_df = spark.readStream.format("kafka")...

# Standard Parquet Data Lake (Dangerous - No ACID, no updates, prone to corruption on crash)
raw_stream_df.write.format("parquet").save("s3://data-lake/raw_events")

# Delta Lakehouse (Safe - Fully ACID compliant, builds _delta_log)
raw_stream_df.write \
    .format("delta") \
    .mode("append") \
    .save("s3://data-lake/raw_events_delta")
```

---

## Scenario 2: The UPSERT (Merge Into) Command

In a traditional S3 Data Lake, updating an existing record with a new change (Change Data Capture / CDC) meant rewriting the entire multi-terabyte dataset from scratch to deduplicate rows. Delta allows standard SQL `MERGE INTO`, handling all the localized file copying and JSON logging silently in the background.

### Execution (SQL)

```sql
-- We have a Silver-tier Delta table representing active users.
-- We have a temporary view representing updates that arrived via an API webhook today.
MERGE INTO silver.users target
USING webhooks.daily_updates source
ON target.user_id = source.user_id

-- If the user already exists in the Silver table, update their subscription tier
WHEN MATCHED THEN 
  UPDATE SET target.subscription = source.subscription

-- If the user is brand new today, insert them entirely
WHEN NOT MATCHED THEN 
  INSERT (user_id, email, subscription) 
  VALUES (source.user_id, source.email, source.subscription)
```

---

## Scenario 3: Time Travel and Disaster Recovery

A junior developer accidentally runs a drop command or executes an `UPDATE` without a `WHERE` clause, destroying a critical production table visually.

### Execution (SQL / PySpark)

```sql
-- 1. Identify the catastrophic mistake using the transaction history log
DESCRIBE HISTORY silver.users;
-- Output shows:
-- version 12: MERGE (Normal operation)
-- version 13: UPDATE (The catastrophic un-filtered update executed 5 minutes ago)

-- 2. "Time Travel" to query the data exactly as it was at Version 12
SELECT * FROM silver.users VERSION AS OF 12;

-- 3. Permanently restore the production table back to the pristine state
RESTORE TABLE silver.users TO VERSION AS OF 12;
-- Delta creates a new Version 14 commit that nullifies the catastrophic Version 13.
```

---

## Scenario 4: Optimizing and Vacuuming

Because Delta's `UPDATE` and `DELETE` commands use Copy-On-Write (leaving the old, logically deleted Parquet files intact on S3 to support Time Travel), your S3 costs will continuously increase. You must actively clean up the physical object storage.

### Execution (SQL)

```sql
-- OPTIMIZE: The "Small File" problem solver.
-- Scans the Delta table for thousands of tiny 5KB parquet files and safely 
-- compacts them into massive 1GB files in the background, accelerating read speeds.
-- Uses Z-Ordering algorithms to mathematically cluster related data columns together.
OPTIMIZE silver.users ZORDER BY (last_login_date, subscription_tier);


-- VACUUM: The Physical Delete command.
-- Scans the _delta_log to find Parquet files that were logically "removed" 
-- by UPDATEs or DELETEs more than 7 days ago, and physically issues a hard DELETE 
-- via the S3 API to destroy the bytes and save money.
-- WARNING: You can no longer Time Travel beyond 7 days after running this.
VACUUM silver.users RETAIN 168 HOURS;
```
