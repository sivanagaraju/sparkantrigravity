# Data Modeling Patterns - Lead/Architect Interview

## 1. Dimensional Modeling Patterns

### Bridge Table (Many-to-Many)
```sql
-- Problem: Customer can have multiple accounts, account can have multiple customers

DIM_CUSTOMER: | customer_key | name |
DIM_ACCOUNT: | account_key | account_number |

BRIDGE_CUSTOMER_ACCOUNT:
| customer_key | account_key | weight_factor |
|--------------|-------------|---------------|
| C1           | A1          | 0.5           |
| C1           | A2          | 0.5           |
| C2           | A1          | 0.5           |

-- Weight factor for allocating measures
SELECT SUM(f.amount * b.weight_factor) as customer_amount
FROM fact_transactions f
JOIN bridge_customer_account b ON f.account_key = b.account_key
JOIN dim_customer c ON b.customer_key = c.customer_key
GROUP BY c.name
```

### Outrigger Dimension
```sql
-- Secondary dimension accessed through primary dimension
DIM_PRODUCT:
| product_key | product_name | category_key |

DIM_CATEGORY (Outrigger):
| category_key | category_name | department |

-- Snowflake pattern, but intentional for:
-- - Very large dimension with stable sub-dimension
-- - Shared sub-dimension across multiple dimensions
```

### Multi-Valued Dimension
```sql
-- Patient with multiple diagnoses
DIM_DIAGNOSIS_GROUP:
| diagnosis_group_key | diagnosis_list |
|---------------------|----------------|
| DG001               | D1, D2, D3     |

-- Or use Bridge Table pattern for better flexibility
BRIDGE_PATIENT_DIAGNOSIS:
| patient_key | diagnosis_key | is_primary |
```

---

## 2. Slowly Changing Dimension Deep Dive

### SCD Type 2 - Full Implementation
```python
from delta.tables import DeltaTable
from pyspark.sql.functions import *

def apply_scd2(spark, source_df, target_path, key_cols, track_cols):
    """
    Generic SCD Type 2 implementation.
    
    Args:
        source_df: New/updated records
        target_path: Delta table path
        key_cols: Business key columns
        track_cols: Columns to track for changes
    """
    
    # Generate hash for change detection
    source_with_hash = source_df.withColumn(
        "row_hash",
        md5(concat_ws("||", *[col(c) for c in track_cols]))
    )
    
    target = DeltaTable.forPath(spark, target_path)
    
    # Build join condition
    join_cond = " AND ".join([f"t.{c} = s.{c}" for c in key_cols])
    join_cond += " AND t.is_current = true"
    
    # Step 1: Expire changed records
    target.alias("t").merge(
        source_with_hash.alias("s"),
        join_cond
    ).whenMatchedUpdate(
        condition="t.row_hash != s.row_hash",
        set={
            "end_date": current_timestamp(),
            "is_current": lit(False)
        }
    ).execute()
    
    # Step 2: Insert new versions
    # Get expired records (just updated above)
    expired = target.toDF().filter(
        (col("is_current") == False) & 
        (col("end_date") > current_timestamp() - expr("INTERVAL 10 SECONDS"))
    ).select(*key_cols)
    
    # New records = source keys not in current target
    current_keys = target.toDF().filter("is_current = true").select(*key_cols)
    new_records = source_with_hash.join(current_keys, key_cols, "left_anti")
    
    # Changed records = join with expired
    changed_records = source_with_hash.join(expired, key_cols, "inner")
    
    # Combine and insert
    to_insert = new_records.union(changed_records) \
        .withColumn("start_date", current_timestamp()) \
        .withColumn("end_date", lit("9999-12-31").cast("timestamp")) \
        .withColumn("is_current", lit(True)) \
        .withColumn("surrogate_key", monotonically_increasing_id())
    
    to_insert.write.format("delta").mode("append").save(target_path)
    
    return to_insert.count()
```

### SCD Type 4 - History Table
```python
# Main table (current only)
current_customers = spark.table("dim_customer_current")

# History table (all versions)
history_customers = spark.table("dim_customer_history")

# On update:
# 1. Archive current to history
# 2. Replace current with new

def update_scd4(new_data, current_table, history_table):
    # Get changed records
    current = spark.table(current_table)
    changes = new_data.join(current, "customer_id") \
        .filter(new_data.row_hash != current.row_hash)
    
    # Archive current versions
    changes.select(current["*"]) \
        .withColumn("archived_at", current_timestamp()) \
        .write.mode("append").saveAsTable(history_table)
    
    # Update current table
    # (Use MERGE or overwrite)
```

---

## 3. Data Lake Table Formats Comparison

### Delta vs Iceberg vs Hudi

| Feature | Delta Lake | Apache Iceberg | Apache Hudi |
|---------|------------|----------------|-------------|
| ACID | ✓ | ✓ | ✓ |
| Time Travel | ✓ | ✓ | ✓ |
| Schema Evolution | ✓ | ✓ | ✓ |
| Partition Evolution | Limited | ✓ (Hidden) | Limited |
| Upsert | MERGE | MERGE | Native |
| Streaming | ✓ | ✓ | ✓ |
| Compaction | OPTIMIZE | Automatic | Automatic |
| Ecosystem | Databricks | Snowflake, Dremio | AWS EMR |

### When to Use Each
```
DELTA LAKE:
- Databricks ecosystem
- PySpark heavy workloads
- Need Z-ORDER optimization

ICEBERG:
- Multi-engine (Spark, Presto, Flink)
- Hidden partitioning needed
- Large-scale analytics workloads

HUDI:
- CDC-heavy workloads
- Need record-level updates
- AWS ecosystem
```

---

## 4. Partitioning Strategies

### Date Partitioning
```python
# Common patterns
df.write.partitionBy("year", "month", "day")  # Fine-grained
df.write.partitionBy("year_month")             # Balanced
df.write.partitionBy("date")                   # Coarse

# Best practice: Match query patterns
# If queries always filter by date → partition by date
# If queries span date ranges → coarser partitions
```

### Composite Partitioning
```python
# Multiple partition columns
df.write.partitionBy("region", "date")

# Order matters! Most selective first
# region/date creates: region=US/date=2024-01-15/
```

### Dynamic Partition Pruning
```python
# Spark 3.0+ automatic optimization
# Filters pushed to partitioned table in join

# Enable (default in Spark 3.0+)
spark.conf.set("spark.sql.optimizer.dynamicPartitionPruning.enabled", "true")
```

### Partition Guidelines
```
DO:
- Partition on frequently filtered columns
- Keep partition count manageable (<10K)
- Each partition should be 1GB+
- Use date for time-series data

DON'T:
- Partition on high-cardinality columns (user_id)
- Create too many small partitions
- Partition on columns with NULL values
```

---

## 5. Bucketing vs Partitioning

### Key Differences
```
PARTITIONING:                    BUCKETING:
├── region=US/                   All data in:
│   └── data.parquet             ├── part-0.parquet (bucket 0)
├── region=EU/                   ├── part-1.parquet (bucket 1)
│   └── data.parquet             └── part-N.parquet (bucket N)
└── region=APAC/
    └── data.parquet

Partition: Separate directories    Bucket: Hash into fixed files
Good for: Range queries           Good for: Join optimization
```

### When to Use Bucketing
```python
# Two tables frequently joined on same key
sales.write \
    .bucketBy(16, "customer_id") \
    .sortBy("customer_id") \
    .saveAsTable("bucketed_sales")

customers.write \
    .bucketBy(16, "customer_id") \
    .sortBy("customer_id") \
    .saveAsTable("bucketed_customers")

# Join is now shuffle-free!
spark.table("bucketed_sales") \
    .join(spark.table("bucketed_customers"), "customer_id")
```

---

## 6. Data Pipeline Patterns

### Idempotent Processing
```python
# Pattern 1: Merge with deduplication
target.merge(source, "target.id = source.id") \
    .whenMatchedUpdateAll() \
    .whenNotMatchedInsertAll()

# Pattern 2: Overwrite partition
df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("replaceWhere", f"date = '{process_date}'") \
    .save(path)
```

### Late Arriving Data
```python
# Allow updates to historical partitions
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")

# Reprocess with watermark
df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("replaceWhere", f"date >= '{watermark_date}'") \
    .save(path)
```

### Backfill Pattern
```python
def backfill(start_date, end_date, table_path):
    """Process date range idempotently."""
    dates = generate_date_range(start_date, end_date)
    
    for date in dates:
        process_single_day(date)
        
        # Overwrite partition
        df.write \
            .format("delta") \
            .mode("overwrite") \
            .option("replaceWhere", f"date = '{date}'") \
            .save(table_path)
        
        print(f"Completed: {date}")
```

---

## 7. Data Governance Patterns

### Data Lineage
```
Track: Source → Transformations → Target

Unity Catalog automatically captures:
- Column-level lineage
- Table dependencies
- Job execution history
```

### Data Classification
```python
# Tag sensitive columns
ALTER TABLE customers ALTER COLUMN ssn SET TAGS ('PII', 'Sensitive')
ALTER TABLE customers ALTER COLUMN email SET TAGS ('PII')

# Row-level security
CREATE ROW FILTER region_filter ON customers 
AS (region) -> current_user_regions() CONTAINS region
```

### Data Retention
```sql
-- Set retention policy
ALTER TABLE transactions SET TBLPROPERTIES (
    'delta.logRetentionDuration' = 'interval 30 days',
    'delta.deletedFileRetentionDuration' = 'interval 7 days'
);

-- Archive old data
INSERT INTO transactions_archive
SELECT * FROM transactions WHERE date < '2023-01-01';

DELETE FROM transactions WHERE date < '2023-01-01';
```

---

## 8. Interview Questions - Architect Level

### Q: Design a DW for an e-commerce company
```
1. Identify business processes:
   - Orders, Inventory, Customers, Shipping, Returns
   
2. Define facts:
   - fact_orders (transaction grain)
   - fact_inventory_snapshot (daily snapshot)
   - fact_returns (transaction grain)
   
3. Define dimensions:
   - dim_customer (SCD2 for address changes)
   - dim_product (SCD2 for price changes)
   - dim_date (standard calendar)
   - dim_location (slowly changing)
   - dim_promotion (junk dimension for flags)
   
4. Architecture:
   - Medallion: Bronze → Silver → Gold
   - Delta Lake for ACID and time travel
   - Partitioned by date for recent data access
   - Z-ORDER by customer_id for customer analytics
   
5. Quality:
   - Null checks on surrogate keys
   - Referential integrity validation
   - Reconciliation with source systems
```

### Q: How do you handle 1TB daily ingestion?
```
1. Incremental processing (not full loads)
2. Partition by date (query pruning)
3. Auto Loader for streaming ingestion
4. Delta Lake OPTIMIZE nightly
5. Cluster auto-scaling during peak
6. Z-ORDER on frequently joined columns
7. Separate compute for ETL vs analytics
```

### Q: How do you ensure data quality at scale?
```
1. Schema enforcement (Delta Lake)
2. Expectations (DLT or Great Expectations)
3. Automated reconciliation checks
4. Quarantine pattern for bad data
5. Alerting on quality thresholds
6. Lineage tracking for root cause
7. Data contracts between teams
```
