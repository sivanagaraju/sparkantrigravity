# Swiss Re Interview Preparation - Lead Engineer Guide

## 📚 How to Use This Project

This is a comprehensive interview prep for **Lead/Senior Data Engineer** roles. All content is organized into topic areas with Q&A formats, runnable code, and cheatsheets.

---

## 📂 Project Structure

```
Interview_Prep_Project/
│
├── 01_PySpark/                          # Spark Deep Dive
│   ├── 01_spark_fundamentals.py         # RDD vs DataFrame, Lazy Eval
│   ├── 02_joins_optimization.py         # Broadcast, Skew, Salting
│   ├── 03_udfs_and_api_calls.py         # ⭐ CRITICAL: UDF anti-pattern
│   ├── 04_spark_internals.py            # AQE, Catalyst, Performance
│   ├── 05_cluster_internals.py          # ⭐ YARN, DAG, Stages, Tasks
│   └── 06_memory_configs.py             # ⭐ memoryOverhead, GC, Kryo
│
├── 02_SQL/                              # SQL Advanced
│   ├── 01_basics_and_windows.sql        # Window functions, aggregations
│   ├── 02_joins_subqueries.sql          # Joins, EXISTS, subqueries
│   ├── 03_advanced_patterns.sql         # Recursive CTE, Gaps & Islands
│   ├── 04_null_gotchas.sql              # ⚠️ NULL behavior traps!
│   ├── 05_acid_indexes.sql              # ACID, Indexes, Query Plans
│   └── 06_advanced_patterns.sql         # ⭐ EXCEPT, Windows Deep, Constraints
│
├── 03_Python/                           # Python Advanced
│   ├── 01_data_structures.py            # Flatten dict, joins, generators
│   ├── 02_oop_patterns.py               # Factory, Singleton, Strategy
│   ├── 03_tricky_questions.py           # ⚠️ is vs ==, mutability
│   └── 04_advanced_python.py            # ⭐ Decorators, Pytest, Duck Typing
│
├── 04_Architecture/                     # System Design
│   └── 01_azure_lakehouse.md            # Medallion, Delta Lake
│
├── 05_Behavioral/                       # Soft Skills
│   └── star_examples.md                 # STAR method examples
│
├── 06_Cheatsheets/                      # 📋 PRINT THESE!
│   ├── sql_cheatsheet.md                # CTEs, Windows, NULL
│   ├── python_cheatsheet.md             # is vs ==, Gotchas
│   ├── pyspark_cheatsheet.md            # Transformations, UDFs
│   ├── spark_internals_cheatsheet.md    # ⭐ Memory, Configs, DAG
│   ├── delta_lake_cheatsheet.md         # ⭐ MERGE, OPTIMIZE, Z-ORDER
│   └── database_dw_cheatsheet.md        # ⭐ SCD, Star Schema, Indexes
│
├── 07_Notebooks/                        # 📓 INTERACTIVE
│   ├── python_tricky.ipynb              # Python gotchas
│   ├── pyspark_tricky.ipynb             # PySpark concepts
│   └── pandas_tricky.ipynb              # Pandas gotchas
│
├── 08_Database_DW/                      # Database Concepts
│   └── data_warehouse_concepts.md       # ⭐ SCD Types, Normalization, Medallion
│
├── 09_DeltaLake_Advanced/               # Delta Lake Deep
│   └── delta_internals.md               # ⭐ All Delta features, ACID
│
├── 10_Databricks/                       # Databricks Ops
│   └── databricks_operations.md         # ⭐ Unity Catalog, dbutils, Jobs
│
└── 11_DataQuality/                      # Data Quality
    └── data_quality.md                  # ⭐ Expectations, Reconciliation
```

---

## ⭐ Lead Engineer Priority Topics

### Day 1 - Spark Internals (THE DIFFERENTIATOR)
1. **`01_PySpark/05_cluster_internals.py`** - YARN, Application Master, DAG flow
2. **`01_PySpark/06_memory_configs.py`** - memoryOverhead, GC, Kryo serialization
3. **`06_Cheatsheets/spark_internals_cheatsheet.md`** - Quick reference

### Day 2 - Delta Lake & Data Warehouse
4. **`09_DeltaLake_Advanced/delta_internals.md`** - MERGE, Z-ORDER, VACUUM, CDF
5. **`08_Database_DW/data_warehouse_concepts.md`** - SCD Type 2, Star Schema
6. **`10_Databricks/databricks_operations.md`** - Unity Catalog, dbutils, Auto Loader

### Day 3 - SQL & Python Advanced
7. **`02_SQL/06_advanced_patterns.sql`** - EXCEPT, Window frames, Constraints
8. **`03_Python/04_advanced_python.py`** - Decorators, Pytest, Duck Typing
9. **`11_DataQuality/data_quality.md`** - Great Expectations, DLT

---

## 🎯 Lead Engineer Interview Questions

### Spark Internals
- How does spark-submit work? (Resource Manager → AM → Executors)
- Explain the DAG and how stages are created (shuffle boundaries)
- What is spark.executor.memoryOverhead and when to increase it?
- Difference between Kryo and Java serialization?
- When do you use mapPartitions vs map?

### Delta Lake
- How does Delta achieve ACID? (Transaction log, OCC)
- When to use Z-ORDER vs Liquid Clustering?
- What does VACUUM do and what's the danger?
- Explain Change Data Feed (CDF)
- What are Deletion Vectors?

### Data Warehouse
- Explain SCD Type 2 implementation
- Star vs Snowflake schema trade-offs
- When to use partitioning vs bucketing?
- Managed vs External tables
- What is the Medallion architecture?

---

## ✅ Pre-Interview Checklist

- [ ] Know cluster architecture: RM → AM → Executor → Task
- [ ] Explain memory layout: Unified Memory, Storage vs Execution
- [ ] Delta Lake MERGE syntax from memory
- [ ] SCD Type 2 implementation pattern
- [ ] mapPartitions for API calls (not UDF!)
- [ ] 3 STAR method behavioral stories ready
- [ ] Print cheatsheets from 06_Cheatsheets/

---

## 🍀 Good Luck!

Remember:
- For Lead roles, they expect you to know **WHY**, not just **HOW**
- Explain trade-offs, not just solutions
- Show you understand production considerations
