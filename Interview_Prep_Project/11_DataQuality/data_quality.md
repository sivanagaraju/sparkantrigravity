# Data Quality - Lead Engineer Interview

## 1. Data Quality Dimensions

### Core Dimensions
| Dimension | Description | Example Check |
|-----------|-------------|---------------|
| **Completeness** | No missing values | NOT NULL, row count |
| **Accuracy** | Data reflects reality | Range checks, regex |
| **Consistency** | No conflicts across systems | Cross-table validation |
| **Timeliness** | Data is current | Freshness checks |
| **Uniqueness** | No duplicates | Primary key, distinct |
| **Validity** | Conforms to format | Data type, enum values |

---

## 2. Validation Patterns

### Schema Validation
```python
expected_schema = StructType([
    StructField("id", LongType(), nullable=False),
    StructField("name", StringType(), nullable=False),
    StructField("amount", DoubleType(), nullable=True),
])

# Validate schema
assert df.schema == expected_schema, "Schema mismatch!"
```

### Null Checks
```python
from pyspark.sql.functions import col, count, when

# Count nulls per column
null_counts = df.select([
    count(when(col(c).isNull(), c)).alias(c) 
    for c in df.columns
])

# Fail if any nulls in critical columns
critical_columns = ["id", "date", "customer_id"]
for col_name in critical_columns:
    null_count = df.filter(col(col_name).isNull()).count()
    if null_count > 0:
        raise ValueError(f"Found {null_count} nulls in {col_name}")
```

### Range Checks
```python
# Amount should be positive
invalid = df.filter(col("amount") <= 0).count()
assert invalid == 0, f"Found {invalid} non-positive amounts"

# Date should be in expected range
df.filter(
    (col("date") < "2020-01-01") | (col("date") > current_date())
).count()
```

### Uniqueness Checks
```python
# Check for duplicates
total = df.count()
unique = df.dropDuplicates(["id"]).count()
duplicates = total - unique
assert duplicates == 0, f"Found {duplicates} duplicate IDs"
```

### Referential Integrity
```python
# All order customer_ids should exist in customers table
orphans = orders.join(
    customers, 
    orders.customer_id == customers.id, 
    "left_anti"
).count()
assert orphans == 0, f"Found {orphans} orphan orders"
```

---

## 3. Great Expectations Framework

### Basic Expectation
```python
import great_expectations as gx

context = gx.get_context()
datasource = context.sources.add_spark("my_spark")
data_asset = datasource.add_dataframe_asset(name="my_data")

batch = data_asset.get_batch(df)

# Define expectations
batch.expect_column_to_exist("id")
batch.expect_column_values_to_not_be_null("id")
batch.expect_column_values_to_be_unique("id")
batch.expect_column_values_to_be_between("amount", 0, 1000000)
batch.expect_column_values_to_match_regex("email", r"^[\w]+@[\w]+\.[\w]+$")
```

### Common Expectations
```python
# Column existence
expect_column_to_exist("column_name")

# Null handling
expect_column_values_to_not_be_null("column")
expect_column_values_to_be_null("column")

# Type validation
expect_column_values_to_be_in_type_list("col", ["INTEGER", "DOUBLE"])

# Value constraints
expect_column_values_to_be_between("age", 0, 120)
expect_column_values_to_be_in_set("status", ["A", "B", "C"])
expect_column_values_to_match_regex("phone", r"^\d{10}$")

# Uniqueness
expect_column_values_to_be_unique("id")
expect_compound_columns_to_be_unique(["col1", "col2"])

# Row-level
expect_table_row_count_to_be_between(1000, 10000)
expect_table_row_count_to_equal(other_table_count)
```

---

## 4. Delta Live Tables (DLT) Quality

### Expectations
```python
import dlt

@dlt.table
@dlt.expect("valid_id", "id IS NOT NULL")
@dlt.expect("positive_amount", "amount > 0")
@dlt.expect_or_drop("valid_date", "date >= '2020-01-01'")
@dlt.expect_or_fail("has_customer", "customer_id IS NOT NULL")
def cleaned_orders():
    return spark.read.table("bronze_orders")
```

### Expectation Types
| Type | Action | Use Case |
|------|--------|----------|
| `@dlt.expect` | Log, keep data | Monitoring |
| `@dlt.expect_or_drop` | Drop invalid rows | Data cleansing |
| `@dlt.expect_or_fail` | Fail pipeline | Critical constraints |

### Quarantine Pattern
```python
@dlt.table
def valid_records():
    return spark.read.table("raw").filter("_dlt_quality_passed = true")

@dlt.table
def quarantine_records():
    return spark.read.table("raw").filter("_dlt_quality_passed = false")
```

---

## 5. Data Reconciliation

### Row Count Reconciliation
```python
source_count = source_df.count()
target_count = target_df.count()

assert source_count == target_count, \
    f"Row count mismatch: source={source_count}, target={target_count}"
```

### Sum Reconciliation
```python
source_sum = source_df.agg(sum("amount")).collect()[0][0]
target_sum = target_df.agg(sum("amount")).collect()[0][0]

# Allow small floating point difference
tolerance = 0.01
diff = abs(source_sum - target_sum)
assert diff < tolerance, f"Sum mismatch: diff={diff}"
```

### Hash Reconciliation
```python
from pyspark.sql.functions import md5, concat_ws

# Add row hash
source_with_hash = source_df.withColumn(
    "row_hash", 
    md5(concat_ws("||", *source_df.columns))
)

# Compare hash sets
source_hashes = set(source_with_hash.select("row_hash").collect())
target_hashes = set(target_with_hash.select("row_hash").collect())

missing = source_hashes - target_hashes
extra = target_hashes - source_hashes
```

---

## 6. Data Profiling

### Basic Profiling
```python
from pyspark.sql.functions import *

# Describe numeric columns
df.describe().show()

# Count distinct values
df.agg(*[countDistinct(c).alias(c) for c in df.columns]).show()

# Null percentage
total = df.count()
null_pcts = df.select([
    (count(when(col(c).isNull(), 1)) / total * 100).alias(c)
    for c in df.columns
])
```

### Distribution Analysis
```python
# Value frequency
df.groupBy("category").count().orderBy(desc("count")).show()

# Percentiles
df.approxQuantile("amount", [0.25, 0.5, 0.75, 0.95], 0.01)

# Min/max/mean
df.agg(
    min("amount").alias("min"),
    max("amount").alias("max"),
    avg("amount").alias("mean"),
    stddev("amount").alias("stddev")
).show()
```

---

## 7. Freshness Monitoring

### Data Freshness Check
```python
from datetime import datetime, timedelta

# Get latest timestamp in data
max_date = df.agg(max("updated_at")).collect()[0][0]

# Check if within threshold
threshold = datetime.now() - timedelta(hours=24)
if max_date < threshold:
    raise ValueError(f"Data is stale! Latest: {max_date}, Threshold: {threshold}")
```

### SLA Monitoring
```python
# Record processing time
processing_metrics = {
    "job_name": "daily_etl",
    "start_time": start,
    "end_time": end,
    "duration_seconds": (end - start).seconds,
    "input_rows": input_count,
    "output_rows": output_count,
    "error_rows": error_count,
    "sla_met": duration_seconds < sla_seconds
}

# Write to metrics table
spark.createDataFrame([processing_metrics]).write.mode("append").saveAsTable("etl_metrics")
```

---

## 8. Common Data Quality Issues

### Issue Detection
| Issue | Detection Query |
|-------|-----------------|
| Duplicates | `GROUP BY key HAVING COUNT(*) > 1` |
| Missing values | `WHERE col IS NULL` |
| Out of range | `WHERE value < 0 OR value > max` |
| Invalid format | `WHERE NOT REGEXP(col, pattern)` |
| Future dates | `WHERE date > current_date()` |
| Type mismatch | `TRY_CAST(col AS type) IS NULL` |

### Handling Strategies
```python
# Replace nulls
df.na.fill({"amount": 0, "status": "UNKNOWN"})

# Filter invalids
valid_df = df.filter(col("amount") > 0)

# Quarantine invalids
invalid_df = df.filter(col("amount") <= 0)
invalid_df.write.saveAsTable("quarantine_orders")

# Log and continue
df.withColumn("is_valid", col("amount") > 0)
```

---

## 9. Automated Quality Framework

### Quality Check Config
```yaml
# quality_rules.yaml
tables:
  orders:
    completeness:
      - column: id
        max_null_pct: 0
      - column: customer_id
        max_null_pct: 0
    validity:
      - column: amount
        min: 0
        max: 1000000
      - column: status
        allowed: [PENDING, SHIPPED, DELIVERED]
    uniqueness:
      - columns: [id]
    freshness:
      - column: created_at
        max_age_hours: 24
```

### Quality Runner
```python
def run_quality_checks(df, table_name, config):
    """Run all quality checks for a table."""
    table_config = config["tables"][table_name]
    results = []
    
    # Completeness checks
    for rule in table_config.get("completeness", []):
        null_pct = df.filter(col(rule["column"]).isNull()).count() / df.count() * 100
        passed = null_pct <= rule["max_null_pct"]
        results.append({
            "rule": f"null_check_{rule['column']}",
            "passed": passed,
            "actual": null_pct,
            "threshold": rule["max_null_pct"]
        })
    
    # ... more checks ...
    
    return results
```

---

## 10. Interview Questions

### Q: How do you handle data quality in production?
```
1. Prevention: Schema enforcement, constraints, validation at ingestion
2. Detection: Automated quality checks after each pipeline stage
3. Response: Quarantine bad data, alert on-call, retry if transient
4. Remediation: Root cause analysis, fix at source, reprocess if needed
5. Monitoring: Dashboards for quality metrics, SLA tracking
```

### Q: What quality checks do you run on incoming data?
```
1. Schema validation (columns, types)
2. Null checks on critical fields
3. Range validation (amounts, dates)
4. Format validation (emails, phones)
5. Referential integrity (foreign keys exist)
6. Freshness check (data is recent)
7. Row count comparison with source
8. Checksum/hash reconciliation for critical data
```
