# Data Warehouse Concepts - Lead Engineer Interview

## 1. Schema Design

### Star Schema
```
              ┌─────────────┐
              │  FACT TABLE │
              │   (Sales)   │
              │             │
              │ product_key │──────┐
              │ customer_key│────┐ │
              │ date_key    │──┐ │ │
              │ store_key   │┐ │ │ │
              │             ││ │ │ │
              │ amount      ││ │ │ │
              │ quantity    ││ │ │ │
              └─────────────┘│ │ │ │
                             │ │ │ │
    ┌────────────────────────┘ │ │ │
    ▼                          │ │ │
┌─────────┐  ┌─────────┐  ┌───┴─┴─┴───┐  ┌─────────┐
│  DIM    │  │  DIM    │  │    DIM    │  │  DIM    │
│ Store   │  │  Date   │  │ Customer  │  │ Product │
└─────────┘  └─────────┘  └───────────┘  └─────────┘
```

**Pros:** Simple queries, fast aggregations
**Cons:** Denormalized, data redundancy

### Snowflake Schema
```
Dimension tables further normalized into sub-dimensions

DIM_Product → DIM_Category → DIM_Department
```

**Pros:** Less redundancy, normalized
**Cons:** More joins, slower queries

---

## 2. Fact Table Types

### Transaction Fact
- One row per event
- Most common type
- Example: Sales transactions

### Periodic Snapshot
- One row per time period
- Example: Daily account balance

### Accumulating Snapshot
- One row per lifecycle
- Updated as process progresses
- Example: Order lifecycle (ordered → shipped → delivered)

---

## 3. Dimension Types (SCD - Slowly Changing Dimensions)

### SCD Type 0 - Retain Original
```
No updates, keep original value forever
```

### SCD Type 1 - Overwrite
```sql
-- Before: John, Address: 123 Main St
-- After:  John, Address: 456 Oak Ave
UPDATE dim_customer SET address = '456 Oak Ave' WHERE id = 1
```
**Lost:** Historical tracking

### SCD Type 2 - Add New Row
```sql
| id | name | address      | start_date | end_date   | is_current |
|----|------|--------------|------------|------------|------------|
| 1  | John | 123 Main St  | 2020-01-01 | 2024-01-15 | false      |
| 1  | John | 456 Oak Ave  | 2024-01-15 | 9999-12-31 | true       |
```
**Keeps:** Full history

### SCD Type 2 Implementation
```python
from delta.tables import DeltaTable

target = DeltaTable.forPath(spark, "/dim_customer")

# Close existing records
target.alias("t").merge(
    source.alias("s"),
    "t.customer_id = s.customer_id AND t.is_current = true"
).whenMatchedUpdate(
    condition="t.hash != s.hash",  # Only if changed
    set={
        "end_date": "current_date()",
        "is_current": "false"
    }
).execute()

# Insert new records
new_records = source.withColumn("start_date", current_date()) \
                   .withColumn("end_date", lit("9999-12-31")) \
                   .withColumn("is_current", lit(True))

new_records.write.format("delta").mode("append").save("/dim_customer")
```

### SCD Type 3 - Add Column
```sql
| id | name | current_address | previous_address |
|----|------|-----------------|------------------|
| 1  | John | 456 Oak Ave     | 123 Main St      |
```
**Limited:** Only one previous value

### SCD Type 4 - History Table
```
Main table: Current values only
History table: All changes
```

### SCD Type 6 - Hybrid (1+2+3)
```sql
| id | name | current_addr | historical_addr | start | end | current |
```

---

## 4. Normalization

### 1NF - First Normal Form
- Atomic values (no arrays/lists in cells)
- No repeating groups

### 2NF - Second Normal Form
- 1NF + No partial dependencies
- All non-key columns depend on FULL primary key

### 3NF - Third Normal Form
- 2NF + No transitive dependencies
- Non-key columns don't depend on other non-key columns

### BCNF - Boyce-Codd Normal Form
- Stronger 3NF
- Every determinant is a candidate key

### When to Denormalize:
- Read-heavy workloads
- Complex join patterns
- Analytics/reporting
- Star schema for DW

---

## 5. Medallion Architecture

```
┌───────────┐     ┌───────────┐     ┌───────────┐
│  BRONZE   │ ──► │  SILVER   │ ──► │   GOLD    │
│   (Raw)   │     │ (Cleaned) │     │(Aggregated│
└───────────┘     └───────────┘     └───────────┘
     │                  │                  │
     ▼                  ▼                  ▼
  As-is from      Deduplicated,     Business-ready,
  source, full    validated,        aggregated,
  history        standardized      optimized
```

### Bronze Layer
- Raw ingestion, no transformation
- Full fidelity to source
- Append-only
- Schema: Source schema

### Silver Layer
- Cleaned and validated
- Deduplicated
- Business entities formed
- Schema enforced

### Gold Layer
- Business aggregations
- KPIs and metrics
- Optimized for reporting
- Often denormalized

---

## 6. Managed vs External Tables

### Managed Table
```sql
CREATE TABLE my_table (id INT, name STRING)
USING DELTA
-- Location: dbfs:/user/hive/warehouse/my_table
```
- Spark manages data AND metadata
- DROP TABLE deletes data

### External Table
```sql
CREATE TABLE my_table (id INT, name STRING)
USING DELTA
LOCATION '/mnt/data/my_table'
```
- Spark manages metadata only
- DROP TABLE keeps data

### When to Use:
- **Managed:** Internal analytics, temp tables
- **External:** Shared data, data lake, multi-tool access

---

## 7. Partitioning Strategies

### Partition by Date
```sql
CREATE TABLE sales (
    id BIGINT,
    amount DOUBLE,
    sale_date DATE
)
PARTITIONED BY (sale_date)
```

### Partition Guidelines:
- **Cardinality:** ~10,000 partitions max
- **Size:** Each partition ~1GB+
- **Query Patterns:** Match WHERE clauses
- **Avoid:** High-cardinality columns (user_id)

### Dynamic Partition Pruning
```sql
-- Spark pushes filter to partitions
SELECT * FROM sales WHERE sale_date = '2024-01-15'
```

---

## 8. Views

### View (Logical)
```sql
CREATE VIEW active_customers AS
SELECT * FROM customers WHERE status = 'active'
```
- Computed at query time
- No storage

### Materialized View
```sql
CREATE MATERIALIZED VIEW sales_summary AS
SELECT date, SUM(amount) FROM sales GROUP BY date
```
- Pre-computed, stored
- Refresh manually or on schedule

### Temporary View
```sql
CREATE OR REPLACE TEMP VIEW my_temp AS
SELECT * FROM ...
```
- Session-scoped

---

## 9. Constraints

### Primary Key
```sql
ALTER TABLE customers ADD CONSTRAINT pk_customer PRIMARY KEY (id)
```
*Note: Delta Lake PK is informational, not enforced*

### Foreign Key
```sql
ALTER TABLE orders ADD CONSTRAINT fk_customer 
FOREIGN KEY (customer_id) REFERENCES customers(id)
```
*Informational, helps query optimizer*

### CHECK Constraint
```sql
ALTER TABLE orders ADD CONSTRAINT valid_amount CHECK (amount > 0)
```
*Enforced on write*

### NOT NULL
```sql
ALTER TABLE customers ALTER COLUMN name SET NOT NULL
```

---

## 10. Indexes

### B-Tree Index
- Default, most common
- Good for: =, <, >, BETWEEN

### Hash Index
- Equality only
- O(1) lookup

### Bitmap Index
- Low cardinality columns
- Fast AND/OR operations

### Bloom Filter (Delta Lake)
```sql
CREATE BLOOMFILTER INDEX ON TABLE my_table FOR COLUMNS(id)
```
- Probabilistic: May say "maybe present"
- Never false negative
- Use for: Point lookups

### Covering Index
```sql
CREATE INDEX idx ON table(key) INCLUDE (col1, col2)
```
- Index-only scan (no table access)

### Clustered vs Non-Clustered

| Clustered | Non-Clustered |
|-----------|---------------|
| Data sorted by index | Pointer to data |
| One per table | Many per table |
| IS the table | Separate structure |

---

## 11. Query Optimization

### Cost-Based Optimizer (CBO)
```sql
-- Analyze table for statistics
ANALYZE TABLE my_table COMPUTE STATISTICS
ANALYZE TABLE my_table COMPUTE STATISTICS FOR COLUMNS col1, col2
```

### Query Hints
```sql
-- Broadcast join hint
SELECT /*+ BROADCAST(small_table) */ *
FROM large_table JOIN small_table ON ...

-- Repartition hint
SELECT /*+ REPARTITION(100) */ ...
```

---

## 12. Data Lake Architecture

```
┌────────────────────────────────────────────────────────┐
│                    UNITY CATALOG                        │
│                  (Governance Layer)                     │
└────────────────────────────────────────────────────────┘
                          │
┌────────────────────────────────────────────────────────┐
│                   COMPUTE LAYER                         │
│              (Databricks, Spark, Presto)               │
└────────────────────────────────────────────────────────┘
                          │
┌────────────────────────────────────────────────────────┐
│                   TABLE FORMAT                          │
│              (Delta Lake, Iceberg, Hudi)               │
└────────────────────────────────────────────────────────┘
                          │
┌────────────────────────────────────────────────────────┐
│                   STORAGE LAYER                         │
│              (S3, ADLS, GCS, HDFS)                     │
└────────────────────────────────────────────────────────┘
```

---

## 13. Data Lake vs Data Warehouse

| Aspect | Data Lake | Data Warehouse |
|--------|-----------|----------------|
| Data | Raw, any format | Structured, curated |
| Schema | On-read | On-write |
| Users | Data Scientists, Engineers | Business Analysts |
| Queries | Exploratory, ML | Reports, Dashboards |
| Cost | Lower storage | Higher (optimized) |
| Governance | Harder | Easier |

**Lakehouse:** Best of both (Delta Lake, Iceberg, Hudi)

---

## 14. ETL vs ELT

### ETL (Extract, Transform, Load)
```
Source → Transform (external) → Target
```
- Transform before loading
- Traditional DW approach
- Tools: Informatica, Talend, SSIS

### ELT (Extract, Load, Transform)
```
Source → Target → Transform (in target)
```
- Load raw, transform in warehouse
- Modern data lake approach
- Tools: dbt, Spark, SQL

**Why ELT is preferred now:**
- Cheaper storage (cloud)
- Powerful compute (Spark)
- Keep raw data (audit, re-process)
- Schema-on-read flexibility
