# DELTA LAKE CHEATSHEET - Quick Reference

## 📝 Basic Operations
```python
# Read
df = spark.read.format("delta").load("/path")

# Write
df.write.format("delta").mode("overwrite").save("/path")

# SQL
spark.sql("SELECT * FROM delta.`/path/to/table`")
```

---

## ⏰ Time Travel
```python
# By version
df = spark.read.format("delta").option("versionAsOf", 5).load("/path")

# By timestamp
df = spark.read.format("delta").option("timestampAsOf", "2024-01-15").load("/path")

# Restore
RESTORE TABLE my_table TO VERSION AS OF 5
```

---

## 🔄 MERGE (Upsert)
```python
from delta.tables import DeltaTable

target = DeltaTable.forPath(spark, "/path")
target.alias("t").merge(
    source.alias("s"),
    "t.id = s.id"
).whenMatchedUpdateAll()
 .whenNotMatchedInsertAll()
 .execute()
```

---

## ⚡ Optimize & Z-Order
```sql
-- Compact small files
OPTIMIZE my_table

-- Multi-column clustering
OPTIMIZE my_table ZORDER BY (date, region)

-- Auto optimization
ALTER TABLE my_table SET TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
)
```

---

## 🗑️ Vacuum
```sql
-- Remove old files (7 days default)
VACUUM my_table

-- Custom retention
VACUUM my_table RETAIN 24 HOURS

-- Dry run
VACUUM my_table DRY RUN
```
⚠️ Cannot time travel before vacuum!

---

## 📊 Schema Evolution
```python
# Add columns
.option("mergeSchema", "true")

# Replace schema
.option("overwriteSchema", "true")
```

---

## 📡 Change Data Feed
```sql
-- Enable
ALTER TABLE t SET TBLPROPERTIES (delta.enableChangeDataFeed = true)
```
```python
# Read changes
spark.read.option("readChangeFeed", "true")
    .option("startingVersion", 5)
    .table("my_table")
# Columns: _change_type, _commit_version, _commit_timestamp
```

---

## 🔧 Table Properties
```sql
ALTER TABLE my_table SET TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.enableDeletionVectors' = 'true',
    'delta.logRetentionDuration' = 'interval 30 days'
)
```

---

## 📦 Clone
```sql
-- Shallow (metadata only, fast)
CREATE TABLE new_table SHALLOW CLONE source

-- Deep (full copy)
CREATE TABLE new_table DEEP CLONE source
```

---

## ✅ Constraints
```sql
ALTER TABLE t ALTER COLUMN name SET NOT NULL
ALTER TABLE t ADD CONSTRAINT chk CHECK (amount > 0)
```

---

## 🔍 Data Skipping
- Automatic min/max stats per file
- Works best with sorted/z-ordered data
- Bloom filters for point lookups

---

## ⚙️ ACID Internals
```
Atomicity: Transaction log (one commit = one JSON)
Consistency: Schema enforcement, constraints
Isolation: Optimistic concurrency control
Durability: Parquet files + replicated logs
```
