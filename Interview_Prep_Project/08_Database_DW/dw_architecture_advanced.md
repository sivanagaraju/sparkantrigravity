# Data Warehouse Architecture - Lead/Architect Interview

## 1. Data Warehouse Evolution

### Generations
```
Gen 1: Traditional DW (Teradata, Oracle, Netezza)
  - On-premise, expensive, tightly coupled storage + compute
  
Gen 2: Cloud DW (Redshift, BigQuery, Snowflake)
  - Cloud-native, separate storage, elastic compute
  
Gen 3: Lakehouse (Databricks, Iceberg, Hudi)
  - Open formats, unified analytics, ML integration
```

### Data Warehouse vs Data Lake vs Lakehouse

| Aspect | Data Warehouse | Data Lake | Lakehouse |
|--------|---------------|-----------|-----------|
| Data Type | Structured | Any | Any |
| Schema | Schema-on-write | Schema-on-read | Schema enforcement |
| ACID | Yes | No | Yes (Delta/Iceberg) |
| Cost | High | Low | Medium |
| Users | BI, Analysts | Data Scientists | All |
| Query Speed | Fast | Variable | Fast |
| Governance | Strong | Weak | Strong |

---

## 2. Dimensional Modeling (Kimball vs Inmon)

### Kimball Approach (Bottom-Up)
```
Build data marts first, integrate later

         ┌─────────────┐
         │  Data Mart  │ ◄─── Star Schema
         │   (Sales)   │
         └─────────────┘
                ▲
    ┌───────────┴───────────┐
    │    Staging Layer      │
    └───────────┬───────────┘
                │
         ┌──────┴──────┐
         │   Sources   │
         └─────────────┘
```
- **Pros**: Fast to deliver, business-focused
- **Cons**: Integration challenges, potential redundancy

### Inmon Approach (Top-Down)
```
Build enterprise DW first, derive data marts

         ┌─────────────┐
         │  Data Marts │
         └──────┬──────┘
                │
    ┌───────────▼───────────┐
    │   Enterprise DW (3NF) │ ◄─── Normalized
    └───────────┬───────────┘
                │
         ┌──────┴──────┐
         │   Sources   │
         └─────────────┘
```
- **Pros**: Single source of truth, consistent
- **Cons**: Longer to build, more complex

### Modern Hybrid Approach
```
Medallion Architecture + Data Products

Bronze → Silver → Gold
  │         │        │
  │         │        └── Dimensional Models (Kimball)
  │         └── Conformed Dimensions
  └── Raw ingestion
```

---

## 3. Fact Table Design Patterns

### Transaction Grain
```sql
-- One row per transaction
| txn_id | customer_key | product_key | date_key | amount | qty |
|--------|--------------|-------------|----------|--------|-----|
| T001   | C100         | P50         | 20240115 | 99.99  | 1   |
| T002   | C100         | P51         | 20240115 | 49.99  | 2   |
```
- Most detailed
- Additive facts (amount, qty)

### Periodic Snapshot
```sql
-- One row per period per entity
| account_key | date_key | balance | transactions_count |
|-------------|----------|---------|-------------------|
| A001        | 20240115 | 5000.00 | 15                |
| A001        | 20240116 | 5200.00 | 8                 |
```
- Regular intervals (daily, weekly)
- Semi-additive (balance can't be summed across time)

### Accumulating Snapshot
```sql
-- One row per lifecycle, updated
| order_key | order_date | ship_date | deliver_date | status      |
|-----------|------------|-----------|--------------|-------------|
| O001      | 2024-01-10 | 2024-01-12| 2024-01-15   | DELIVERED   |
| O002      | 2024-01-11 | 2024-01-13| NULL         | IN_TRANSIT  |
```
- Tracks process milestones
- Row updated as events occur

### Factless Fact Table
```sql
-- Records events without measures
| student_key | course_key | date_key |
|-------------|------------|----------|
| S001        | C100       | 20240115 |
| S002        | C100       | 20240115 |
```
- Coverage tracking
- Event recording
- Many-to-many bridge

---

## 4. Dimension Design Patterns

### Junk Dimension
```sql
-- Combine low-cardinality flags into one dimension
| junk_key | is_promotion | is_online | payment_type | gift_wrap |
|----------|--------------|-----------|--------------|-----------|
| 1        | Y            | Y         | CREDIT       | N         |
| 2        | Y            | N         | DEBIT        | Y         |
```
- Reduces fact table width
- All combinations pre-generated

### Degenerate Dimension
```sql
-- Dimension value stored in fact table (no separate dim)
| order_line_key | order_number | product_key | amount |
|----------------|--------------|-------------|--------|
| 1              | ORD-12345    | P50         | 99.99  |
```
- Transaction/document numbers
- No attributes to store

### Role-Playing Dimension
```sql
-- Same dimension used multiple ways
| sale_key | order_date_key | ship_date_key | deliver_date_key |
|----------|----------------|---------------|------------------|
| 1        | 20240110       | 20240112      | 20240115         |

-- All three keys reference DIM_DATE
```

### Conformed Dimension
```sql
-- Shared across multiple fact tables / data marts
DIM_CUSTOMER used by:
  - FACT_SALES
  - FACT_SUPPORT_TICKETS
  - FACT_WEBSITE_VISITS
```
- Master data management
- Enterprise-wide consistency

### Mini-Dimension
```sql
-- Fast-changing attributes split out
DIM_CUSTOMER (stable):
| customer_key | customer_id | name | join_date |

DIM_CUSTOMER_DEMOGRAPHICS (changing):
| demo_key | age_band | income_band | segment |

FACT_SALES:
| customer_key | demo_key | ... |
```
- Avoids SCD2 bloat
- Snapshot demographics at transaction time

---

## 5. Advanced SCD Patterns

### SCD Type 2 with Hash
```python
# Generate hash for change detection
from pyspark.sql.functions import md5, concat_ws

df = df.withColumn("row_hash", 
    md5(concat_ws("||", 
        col("name"), 
        col("address"), 
        col("phone")
    ))
)

# Compare hash to detect changes efficiently
```

### SCD Type 2 Implementation (Delta Lake)
```python
from delta.tables import DeltaTable
from pyspark.sql.functions import current_timestamp, lit

target = DeltaTable.forPath(spark, "/dim_customer")

# Step 1: Close existing current records that have changed
target.alias("t").merge(
    source.alias("s"),
    "t.customer_id = s.customer_id AND t.is_current = true"
).whenMatchedUpdate(
    condition="t.row_hash != s.row_hash",
    set={
        "end_date": current_timestamp(),
        "is_current": lit(False)
    }
).execute()

# Step 2: Insert new/changed records
changed_or_new = source.join(
    target.toDF().filter("is_current = true"),
    "customer_id",
    "left_anti"  # New customers
).union(
    source.alias("s").join(
        target.toDF().filter("is_current = false").alias("t"),
        (col("s.customer_id") == col("t.customer_id")) & 
        (col("t.end_date") > current_timestamp() - expr("INTERVAL 1 SECOND"))
    ).select("s.*")  # Changed customers
)

changed_or_new.withColumn("start_date", current_timestamp()) \
    .withColumn("end_date", lit("9999-12-31")) \
    .withColumn("is_current", lit(True)) \
    .write.format("delta").mode("append").save("/dim_customer")
```

### SCD Type 6 (Hybrid)
```sql
| customer_key | customer_id | current_city | historical_city | 
| start_date   | end_date    | is_current   |
|--------------|-------------|--------------|-----------------|
|--------------|-------------|--------------|
| 1001         | C100        | New York     | Boston          |
| 2020-01-01   | 2024-01-15  | false        |
| 1002         | C100        | New York     | New York        |
| 2024-01-15   | 9999-12-31  | true         |
```
- Combines Type 1 (current_ columns) + Type 2 (history) + Type 3 (prior)
- Supports "as-was" and "as-is" reporting

---

## 6. Data Vault Modeling

### Core Concepts
```
HUB: Business keys (what)
LINK: Relationships (how connected)
SATELLITE: Descriptive attributes (context)
```

### Example
```sql
-- HUB_CUSTOMER
| hub_customer_key | customer_bk | load_date | record_source |

-- HUB_ORDER
| hub_order_key | order_bk | load_date | record_source |

-- LINK_CUSTOMER_ORDER
| link_key | hub_customer_key | hub_order_key | load_date |

-- SAT_CUSTOMER
| hub_customer_key | name | address | load_date | hash_diff |
```

### When to Use Data Vault
- Multiple source systems with different keys
- Frequently changing requirements
- Need full audit trail
- Enterprise-scale integration

---

## 7. Query Optimization Strategies

### Partition Pruning
```sql
-- Table partitioned by date
SELECT * FROM sales 
WHERE sale_date = '2024-01-15'  -- Only reads one partition
```

### Predicate Pushdown
```sql
-- Filter pushed to storage layer
SELECT * FROM orders 
WHERE status = 'SHIPPED'
-- Only reads relevant data, not entire table
```

### Materialized Views
```sql
CREATE MATERIALIZED VIEW daily_sales_summary AS
SELECT 
    sale_date,
    region,
    SUM(amount) as total_sales,
    COUNT(*) as txn_count
FROM sales
GROUP BY sale_date, region;

-- Query uses pre-computed aggregation
SELECT * FROM daily_sales_summary 
WHERE sale_date = '2024-01-15';
```

### Aggregate Tables
```sql
-- Pre-aggregate at different grains
FACT_SALES_DAILY
FACT_SALES_WEEKLY  
FACT_SALES_MONTHLY

-- Query engine picks appropriate level
```

---

## 8. Data Modeling Best Practices

### Naming Conventions
```
Tables:
  DIM_CUSTOMER, FACT_SALES, STG_ORDERS

Keys:
  customer_key (surrogate), customer_id (natural)

Measures:
  amount, quantity, count (nouns)

Flags:
  is_active, has_promotion (is_, has_ prefix)

Dates:
  order_date, created_at, updated_at
```

### Surrogate vs Natural Keys
```
SURROGATE KEY:
  - System-generated (auto-increment, GUID)
  - Never changes
  - Better join performance
  - Required for SCD2

NATURAL KEY (Business Key):
  - Comes from source (customer_id, order_number)
  - May change or be reused
  - Meaningful to business
  - Keep for lookups
```

### Grain Statement
```
"One row per [entity] per [time period/event]"

Examples:
- "One row per sales transaction"
- "One row per customer per day"
- "One row per order status change"
```

---

## 9. Data Quality in DW Context

### Dimensions of Quality
```
Completeness: Are all expected records present?
Accuracy: Do values reflect reality?
Consistency: Same data, same value across systems?
Timeliness: Is data fresh enough?
Uniqueness: No duplicates?
Validity: Values in expected format/range?
```

### Quality Checks for DW
```sql
-- Referential integrity
SELECT f.* FROM fact_sales f
LEFT JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE c.customer_key IS NULL;  -- Orphan facts

-- Null surrogate keys
SELECT COUNT(*) FROM fact_sales 
WHERE customer_key = -1;  -- Unknown member count

-- Late arriving facts
SELECT COUNT(*) FROM fact_sales 
WHERE load_date > event_date + INTERVAL 7 DAYS;
```

### Unknown Member Pattern
```sql
-- Handle missing dimension references
INSERT INTO DIM_CUSTOMER (customer_key, customer_id, name)
VALUES (-1, 'UNKNOWN', 'Unknown Customer');

-- Facts with missing dimension use unknown member
INSERT INTO FACT_SALES (customer_key, amount)
VALUES (COALESCE(lookup_customer_key, -1), 100.00);
```

---

## 10. Performance Tuning

### Indexing Strategy
```
Primary Key Index: Always
Foreign Key Index: For joins
Covering Index: Frequent queries
Partial Index: Filtered queries

Don't Index:
- Low cardinality (gender, boolean)
- Frequently updated columns
- Wide columns (long text)
```

### Statistics Management
```sql
-- Spark/Databricks
ANALYZE TABLE fact_sales COMPUTE STATISTICS;
ANALYZE TABLE fact_sales COMPUTE STATISTICS FOR COLUMNS amount, customer_key;

-- Check stats
DESCRIBE EXTENDED fact_sales;
```

### Join Optimization
```
1. Filter before join (reduce data early)
2. Broadcast small dimensions
3. Partition on join keys
4. Use bucketing for frequent joins
5. Avoid cross joins
```

---

## 11. Architect Interview Questions

### Q: How do you design a DW for a new organization?
```
1. Understand business processes (sales, inventory, etc.)
2. Identify measures and dimensions (what to track)
3. Choose grain (level of detail)
4. Define conformed dimensions (shared across facts)
5. Document business rules and transformations
6. Plan for SCD handling
7. Design ETL architecture
8. Establish data governance
9. Create data dictionary
10. Build incrementally, iterate
```

### Q: Star Schema vs 3NF for DW?
```
Star Schema:
  + Fast queries (fewer joins)
  + Simple to understand
  + Optimized for aggregations
  - Data redundancy
  
3NF:
  + No redundancy
  + Flexible for ad-hoc queries
  - More joins, slower
  - Complex for business users
  
Recommendation: Star schema for data marts, 3NF for staging
```

### Q: How do you handle late arriving dimensions?
```
1. Use unknown member (-1 key) initially
2. Reprocess facts when dimension arrives
   OR
3. Use Type 2 SCD with effective dates
   - Fact points to dimension version valid at transaction time
4. Implement "pipeline replay" capability
```

### Q: How do you ensure data consistency across systems?
```
1. Conformed dimensions (single source of truth)
2. Master data management (MDM)
3. Data contracts between teams
4. Reconciliation checks
5. Unity Catalog / Data Governance tools
6. Regular audits and profiling
```

### Q: How do you scale a DW to petabytes?
```
1. Partition by date/region (query pruning)
2. Columnar storage (Parquet, ORC)
3. Separate compute from storage
4. Incremental processing (not full reloads)
5. Aggregate tables for common queries
6. Data lifecycle (archive old data)
7. Workload management (isolate heavy queries)
```

---

## 12. Modern DW Architecture Patterns

### Data Mesh
```
Domain-oriented, decentralized ownership

         ┌─────────────────────────────────┐
         │      Data Platform              │
         │  (Infrastructure, Tools)        │
         └─────────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    ▼                 ▼                 ▼
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Sales   │     │Marketing│     │ Finance │
│ Domain  │     │ Domain  │     │ Domain  │
│ (Team)  │     │ (Team)  │     │ (Team)  │
└─────────┘     └─────────┘     └─────────┘
    │                 │                 │
    ▼                 ▼                 ▼
 Data Product     Data Product     Data Product
```

### Data Products Principles
1. **Domain ownership**: Teams own their data
2. **Data as a product**: Treat data like a product (SLA, docs)
3. **Self-serve platform**: Enable teams to build independently
4. **Federated governance**: Consistent policies, local control

### Event-Driven Architecture
```
Source → Event Stream → Consumer
          (Kafka)
                │
        ┌───────┼───────┐
        ▼       ▼       ▼
     Bronze  Silver   Gold
     (Raw)  (Clean) (Aggregate)
```

### Lambda vs Kappa Architecture
```
LAMBDA: Batch + Stream (two paths)
  ├── Batch Layer (complete, slow)
  └── Speed Layer (recent, fast)
  
KAPPA: Stream only (unified)
  └── Stream Layer (all data as events)
```
