# Databricks Operations - Lead Engineer Interview

## 1. Unity Catalog Architecture

```
┌────────────────────────────────────────────────────────┐
│                     METASTORE                          │
│              (One per region/account)                  │
├────────────────────────────────────────────────────────┤
│                                                        │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│   │   CATALOG    │  │   CATALOG    │  │   CATALOG    ││
│   │   (prod)     │  │   (dev)      │  │   (staging)  ││
│   ├──────────────┤  ├──────────────┤  ├──────────────┤│
│   │   SCHEMA     │  │   SCHEMA     │  │   SCHEMA     ││
│   │  (sales)     │  │  (analytics) │  │  (raw)       ││
│   ├──────────────┤  ├──────────────┤  ├──────────────┤│
│   │ TABLE/VIEW   │  │ TABLE/VIEW   │  │ TABLE/VIEW   ││
│   │ FUNCTION     │  │ FUNCTION     │  │ FUNCTION     ││
│   │ VOLUME       │  │ VOLUME       │  │ VOLUME       ││
│   └──────────────┘  └──────────────┘  └──────────────┘│
└────────────────────────────────────────────────────────┘
```

### Key Concepts
- **Metastore**: Top-level container, one per cloud region
- **Catalog**: Logical grouping of databases (like environments)
- **Schema**: Database, contains objects
- **Table/View**: Data objects
- **Volume**: Unstructured data (files)
- **Function**: User-defined functions

### Three-Level Namespace
```sql
SELECT * FROM catalog.schema.table
SELECT * FROM prod.sales.orders
```

---

## 2. dbutils (Databricks Utilities)

### File System Operations
```python
# List files
dbutils.fs.ls("/mnt/data/")

# Move/copy files
dbutils.fs.mv("/src", "/dst")
dbutils.fs.cp("/src", "/dst", recurse=True)

# Remove files
dbutils.fs.rm("/path", recurse=True)

# Create directory
dbutils.fs.mkdirs("/new/path")

# Read file
dbutils.fs.head("/path/to/file.txt", 1000)  # First 1000 bytes
```

### Secrets
```python
# Get secret from scope
password = dbutils.secrets.get(scope="my-scope", key="db-password")
api_key = dbutils.secrets.get(scope="prod", key="api-key")

# List secret scopes
dbutils.secrets.listScopes()

# List secrets in scope
dbutils.secrets.list(scope="my-scope")
```

### Widgets (Parameters)
```python
# Create widget
dbutils.widgets.text("env", "dev", "Environment")
dbutils.widgets.dropdown("table", "orders", ["orders", "customers", "products"])
dbutils.widgets.multiselect("regions", "US", ["US", "EU", "APAC"])

# Get widget value
env = dbutils.widgets.get("env")

# Remove widget
dbutils.widgets.remove("env")
dbutils.widgets.removeAll()
```

### Notebook Utilities
```python
# Run another notebook
result = dbutils.notebook.run("/path/to/notebook", timeout_seconds=600, arguments={"param": "value"})

# Exit with value
dbutils.notebook.exit("Success")
```

---

## 3. Jobs and Workflows

### Job Configuration
```json
{
  "name": "Daily ETL",
  "tasks": [
    {
      "task_key": "bronze_ingest",
      "notebook_task": {
        "notebook_path": "/ETL/bronze_layer",
        "base_parameters": {"date": "{{start_date}}"}
      },
      "new_cluster": {
        "spark_version": "13.3.x-scala2.12",
        "num_workers": 2
      }
    },
    {
      "task_key": "silver_transform",
      "depends_on": [{"task_key": "bronze_ingest"}],
      "notebook_task": {
        "notebook_path": "/ETL/silver_layer"
      }
    }
  ],
  "schedule": {
    "quartz_cron_expression": "0 0 6 * * ?",
    "timezone_id": "UTC"
  }
}
```

### Task Parameters
```python
# Access task parameters in notebook
task_value = dbutils.widgets.get("date")  # From base_parameters
job_run_id = spark.conf.get("spark.databricks.job.runId")
task_key = spark.conf.get("spark.databricks.task.key")
```

### Cron Expressions
```
┌───────────── second (0-59)
│ ┌───────────── minute (0-59)
│ │ ┌───────────── hour (0-23)
│ │ │ ┌───────────── day of month (1-31)
│ │ │ │ ┌───────────── month (1-12)
│ │ │ │ │ ┌───────────── day of week (0-6) (Sunday=0)
│ │ │ │ │ │
* * * * * *

0 0 6 * * ?     = Every day at 6:00 AM
0 0 */4 * * ?   = Every 4 hours
0 30 9 ? * MON-FRI = 9:30 AM, Monday to Friday
```

---

## 4. Cluster Configuration

### Cluster Types
| Type | Use Case | Cost |
|------|----------|------|
| All-Purpose | Interactive development | Higher |
| Job Cluster | Automated jobs | Lower (ephemeral) |
| Pool | Pre-warmed instances | Faster startup |

### Auto Scaling
```json
{
  "autoscale": {
    "min_workers": 2,
    "max_workers": 8
  },
  "autotermination_minutes": 30
}
```

### Spark Configurations
```python
# Set in cluster config or notebook
spark.conf.set("spark.sql.shuffle.partitions", "200")
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
```

---

## 5. Cost Optimization

### Cluster Strategies
1. **Use Job Clusters**: Auto-terminate after job
2. **Instance Pools**: Reduce startup time
3. **Spot Instances**: 60-90% cheaper (for fault-tolerant jobs)
4. **Auto-scaling**: Match resources to workload
5. **Auto-termination**: Kill idle clusters

### Storage Strategies
1. **Lifecycle policies**: Archive old data
2. **VACUUM**: Clean up old Delta files
3. **OPTIMIZE**: Reduce file count
4. **Z-ORDER**: Skip irrelevant files

### Serverless Options
- **Serverless SQL Warehouse**: Pay per query
- **Serverless Compute**: No cluster management
- **Auto-suspending warehouses**: Suspend when idle

---

## 6. Auto Loader (cloudFiles)

### Basic Usage
```python
df = spark.readStream \
    .format("cloudFiles") \
    .option("cloudFiles.format", "parquet") \
    .option("cloudFiles.schemaLocation", "/path/to/schema") \
    .load("/mnt/landing/")

df.writeStream \
    .format("delta") \
    .option("checkpointLocation", "/path/to/checkpoint") \
    .trigger(availableNow=True) \
    .start("/mnt/bronze/")
```

### Key Options
```python
.option("cloudFiles.format", "json")           # Source format
.option("cloudFiles.schemaLocation", "...")     # Schema inference location
.option("cloudFiles.schemaHints", "date DATE")  # Override schema
.option("cloudFiles.inferColumnTypes", "true")  # Infer types
.option("cloudFiles.maxFilesPerTrigger", 1000)  # Limit files per batch
```

### Auto Loader vs COPY INTO

| Feature | Auto Loader | COPY INTO |
|---------|-------------|-----------|
| Mode | Streaming | Batch |
| File tracking | Automatic | Automatic |
| Schema evolution | Rescue column | Limited |
| Performance | Faster (streaming) | Batch |
| Use case | Continuous | Scheduled |

---

## 7. Data Quality with Expectations

### Delta Live Tables (DLT) Expectations
```python
import dlt

@dlt.table
@dlt.expect("valid_amount", "amount > 0")
@dlt.expect_or_drop("not_null", "id IS NOT NULL")
@dlt.expect_or_fail("valid_date", "date > '2020-01-01'")
def silver_orders():
    return spark.read.table("bronze_orders")
```

### Expectation Types
- `@dlt.expect`: Log invalid rows, keep them
- `@dlt.expect_or_drop`: Drop invalid rows
- `@dlt.expect_or_fail`: Fail pipeline if any invalid

---

## 8. Orchestration with ADF

### ADF ↔ Databricks Integration
```json
{
  "name": "RunDatabricksNotebook",
  "type": "DatabricksNotebook",
  "linkedServiceName": {
    "referenceName": "ADBLinkedService",
    "type": "LinkedServiceReference"
  },
  "typeProperties": {
    "notebookPath": "/ETL/process_data",
    "baseParameters": {
      "date": "@pipeline().parameters.runDate",
      "env": "@pipeline().parameters.environment"
    }
  }
}
```

### Passing Parameters from ADF
```python
# In Databricks notebook
run_date = dbutils.widgets.get("date")
env = dbutils.widgets.get("env")
```

---

## 9. Monitoring

### System Tables (Unity Catalog)
```sql
-- Query audit logs
SELECT * FROM system.access.audit
WHERE event_time > current_timestamp() - INTERVAL 1 DAY

-- Billing usage
SELECT * FROM system.billing.usage
WHERE usage_date = current_date()

-- Cluster events
SELECT * FROM system.compute.clusters
```

### Job Monitoring
```python
# Get job run status programmatically
from databricks_sdk import WorkspaceClient
w = WorkspaceClient()
runs = w.jobs.list_runs(job_id=123)
```

---

## 10. S3/ADLS Storage Best Practices

### Challenges with Parquet (no catalog)
1. **No ACID**: Concurrent writes corrupt data
2. **No versioning**: No rollback
3. **Schema drift**: Inconsistent schemas
4. **Small files**: Performance degradation
5. **No partition discovery**: Manual registration

### Solutions
1. **Use Delta Lake**: ACID, versioning, schema evolution
2. **Hive Metastore**: Centralized metadata
3. **Unity Catalog**: Governance + catalog
4. **Regular OPTIMIZE**: Compact small files
5. **Partitioning strategy**: Match query patterns

### Storage Lifecycle
```python
# S3 lifecycle policy (via boto3 or AWS console)
# Move to Glacier after 90 days
# Delete after 365 days
```

---

## 11. Common Interview Questions

### Q: How do you handle job failures?
```
1. Configure retries in job settings
2. Use email/Slack notifications
3. Implement idempotent operations (MERGE, delta)
4. Use checkpoints for streaming
5. Monitor with alerts on system tables
```

### Q: How do you optimize job costs?
```
1. Right-size clusters (analyze metrics)
2. Use spot instances for non-critical jobs
3. Schedule jobs during off-peak
4. Use Photon for SQL workloads
5. Auto-terminate idle clusters
6. Cache intermediate results
```

### Q: How do you handle schema evolution?
```
1. Enable mergeSchema for additive changes
2. Use schema registry for validation
3. Rescue column for unexpected fields
4. Version tables (v1, v2) for breaking changes
5. Communicate schema changes via documentation
```
