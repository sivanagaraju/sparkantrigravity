# Azure Lakehouse Architecture - Interview Reference

This document provides a comprehensive overview of Azure Lakehouse Architecture
for the Swiss Re Senior Application Engineer interview.

## 1. What is a Lakehouse?

A Lakehouse combines the best of:
- **Data Lakes**: Cheap storage, schema-on-read, raw data
- **Data Warehouses**: ACID transactions, schema enforcement, fast queries

### Key Technologies at Swiss Re:
- **Azure Data Lake Storage Gen2 (ADLS)**: The storage layer
- **Azure Databricks**: The compute layer (Spark)
- **Delta Lake**: The table format (ACID on top of Parquet)
- **Azure Data Factory**: The orchestration layer

---

## 2. Medallion Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MEDALLION ARCHITECTURE                      │
├─────────────┬─────────────────┬─────────────────────────────────┤
│   BRONZE    │     SILVER      │              GOLD               │
│   (Raw)     │   (Cleaned)     │          (Aggregated)           │
├─────────────┼─────────────────┼─────────────────────────────────┤
│ Ingested    │ Schema enforced │ Business-ready                  │
│ as-is       │ Deduplicated    │ Pre-aggregated                  │
│ All history │ Validated       │ Optimized for queries           │
└─────────────┴─────────────────┴─────────────────────────────────┘
```

### Bronze Layer (Raw Zone)
- Data arrives "as-is" from source
- No transformations applied
- Full history retained
- **Format**: Parquet/Delta
- **Example Path**: `/bronze/claims/yyyy/mm/dd/`

### Silver Layer (Curated Zone)
- Cleaned and validated data
- Deduplication applied
- Schema enforced
- Business rules applied
- **Format**: Delta (mandatory)
- **Example Path**: `/silver/claims/`

### Gold Layer (Consumption Zone)
- Aggregated for reporting
- Pre-computed KPIs
- Joined dimension tables
- **Format**: Delta
- **Example Path**: `/gold/daily_claim_summary/`

---

## 3. Delta Lake Features

### ACID Transactions
```python
# Delta supports atomic writes
df.write.format("delta").mode("overwrite").save("/delta/claims")
```

### Merge (Upsert)
```python
from delta.tables import DeltaTable

deltaTable = DeltaTable.forPath(spark, "/delta/claims")

deltaTable.alias("old").merge(
    new_data.alias("new"),
    "old.claim_id = new.claim_id"
).whenMatchedUpdate(set = {
    "status": "new.status",
    "updated_at": "current_timestamp()"
}).whenNotMatchedInsert(values = {
    "claim_id": "new.claim_id",
    "status": "new.status"
}).execute()
```

### Time Travel
```python
# Read data as of a specific version
df = spark.read.format("delta").option("versionAsOf", 5).load("/delta/claims")

# Read data as of a timestamp
df = spark.read.format("delta").option("timestampAsOf", "2024-01-01").load("/delta/claims")
```

### Schema Evolution
```python
# Allow schema changes during write
df.write.format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save("/delta/claims")
```

---

## 4. Azure Data Factory (ADF)

ADF is the orchestration service that:
1. **Ingests** data from sources (SFTP, Oracle, APIs)
2. **Triggers** Databricks notebooks
3. **Monitors** pipeline runs

### Key Components:
- **Linked Services**: Connections to data sources
- **Datasets**: References to data
- **Pipelines**: Workflows with activities
- **Triggers**: Schedule or event-based execution

### Common Activities:
```yaml
Pipeline: Daily_Claims_ETL
  Activities:
    1. Copy Activity: SFTP → ADLS Bronze
    2. Databricks Notebook: Bronze → Silver transformation
    3. Databricks Notebook: Silver → Gold aggregation
    4. Web Activity: Send Slack notification
```

---

## 5. Azure Databricks Configuration

### Cluster Types:
| Type | Use Case | Cost |
|------|----------|------|
| Job Cluster | Ephemeral, spun up for job | Lower |
| All-Purpose | Interactive development | Higher |

### Recommended Settings for Production:
```json
{
  "spark_version": "13.3.x-scala2.12",
  "node_type_id": "Standard_DS3_v2",
  "autoscale": {
    "min_workers": 2,
    "max_workers": 8
  },
  "autotermination_minutes": 30,
  "spark_conf": {
    "spark.sql.adaptive.enabled": "true",
    "spark.sql.shuffle.partitions": "auto"
  }
}
```

---

## 6. Security Best Practices

### Azure Key Vault Integration
```python
# In Databricks, use secret scopes
db_password = dbutils.secrets.get(scope="kv-scope", key="db-password")
api_key = dbutils.secrets.get(scope="kv-scope", key="api-key")

# NEVER hardcode secrets!
```

### Access Control
- **ADLS**: Use Azure AD for authentication
- **Databricks**: Use Unity Catalog for table-level permissions
- **Key Vault**: Grant only necessary permissions

---

## 7. Monitoring & Observability

### Databricks Job Metrics:
- Spark UI: For job execution details
- Ganglia Metrics: For cluster resource usage
- Azure Monitor: For logs and alerts

### Key Metrics to Track:
1. **Job Duration**: Trend over time
2. **Data Volume**: Input/output row counts
3. **Error Rate**: Failed tasks/jobs
4. **Resource Utilization**: CPU, Memory, I/O

### Alerting Setup:
```python
# In your ETL job, log metrics
logger.info(f"Processed {input_count} records")
logger.info(f"Output {output_count} records")
logger.info(f"Duration: {elapsed_time} seconds")
```

---

## 8. Interview Quick Reference

### "Walk me through your ETL architecture"
1. **Source**: Files land on SFTP or arrive via API
2. **Ingestion**: ADF copies to Bronze layer in ADLS
3. **Transformation**: Databricks (PySpark) cleans and enriches
4. **Output**: Delta tables in Silver/Gold layers
5. **Consumption**: Power BI connects to Gold tables

### "How do you handle schema changes?"
"We use Delta Lake's `mergeSchema` option. When a new column arrives,
we write with `mergeSchema=True`. For breaking changes, we version
our tables (e.g., claims_v2) and migrate consumers."

### "How do you handle failures?"
1. **Retry Logic**: ADF retries failed activities
2. **Dead Letter Queue**: Bad records go to a separate path
3. **Alerting**: Azure Monitor sends alerts on failure
4. **Idempotency**: Jobs can be re-run safely (overwrite or merge)

---

## 9. Common Interview Diagrams

### Data Flow
```
[Source Systems] → [ADF Ingest] → [Bronze/ADLS] 
       ↓
[Databricks Silver Job] → [Silver/Delta] 
       ↓
[Databricks Gold Job] → [Gold/Delta] → [Power BI]
```

### CI/CD Flow
```
[Feature Branch] → [Pull Request] → [CI Build] 
       ↓
[Unit Tests] → [Merge to Main] → [CD Deploy to Dev]
       ↓
[Integration Tests] → [Deploy to Prod]
```
