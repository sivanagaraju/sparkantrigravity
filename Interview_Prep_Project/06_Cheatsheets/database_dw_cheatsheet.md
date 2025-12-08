# DATABASE & DATA WAREHOUSE CHEATSHEET

## 📊 Schema Types
```
STAR SCHEMA:            SNOWFLAKE:
  ┌───┐                   ┌───┐
  │DIM├─┐               ┌─┤DIM│
  └───┘ │               │ └─┬─┘
        ▼               │   │
     ┌──────┐           │ ┌─┴─┐
     │ FACT │           │ │DIM│
     └──────┘           │ └───┘
        ▲               │
  ┌───┐ │               ▼
  │DIM├─┘            ┌──────┐
  └───┘              │ FACT │
                     └──────┘
```
- **Star**: Simple, fast queries, denormalized
- **Snowflake**: Normalized dimensions, less redundancy

---

## 🔄 SCD Types (Slowly Changing Dimensions)

| Type | Action | History |
|------|--------|---------|
| 0 | Keep original | None |
| 1 | Overwrite | None |
| 2 | Add row | Full |
| 3 | Add column | Limited |

### SCD Type 2 Pattern
```sql
| id | name | start_date | end_date   | is_current |
|----|------|------------|------------|------------|
| 1  | John | 2020-01-01 | 2024-01-15 | false      |
| 1  | John | 2024-01-15 | 9999-12-31 | true       |
```

---

## 📐 Normalization

| Form | Rule |
|------|------|
| 1NF | Atomic values, no repeating groups |
| 2NF | 1NF + No partial dependencies |
| 3NF | 2NF + No transitive dependencies |

**Denormalize for:** Read-heavy, analytics, reporting

---

## 🏆 Medallion Architecture
```
BRONZE (Raw) → SILVER (Cleaned) → GOLD (Aggregated)
    │              │                    │
 As-is         Validated            Business KPIs
 Append-only   Deduplicated         Optimized reads
```

---

## 🗄️ Table Types

**Managed Table:**
- Spark controls data + metadata
- DROP deletes data
- `CREATE TABLE t (...)`

**External Table:**
- Spark controls metadata only
- DROP keeps data
- `CREATE TABLE t LOCATION '/path'`

---

## 📁 Partitioning Guidelines
```sql
PARTITIONED BY (date, region)
```
- Max ~10K partitions
- Each partition ~1GB+
- Match query WHERE clauses
- Avoid high-cardinality columns

---

## 📇 Index Types
| Type | Use Case |
|------|----------|
| B-Tree | =, <, >, BETWEEN |
| Hash | Equality only |
| Bitmap | Low cardinality |
| Bloom | Point lookups |
| Clustered | Data sorted |
| Non-clustered | Pointer to data |

---

## 🔗 Constraints
```sql
PRIMARY KEY (id)
FOREIGN KEY (col) REFERENCES t(id)
UNIQUE (email)
CHECK (amount > 0)
NOT NULL
DEFAULT current_date()
```

---

## 📊 GROUPING
```sql
-- All combinations
GROUP BY CUBE (a, b)

-- Hierarchical subtotals
GROUP BY ROLLUP (a, b)

-- Custom groupings
GROUP BY GROUPING SETS ((a,b), (a), ())
```

---

## 🔍 ETL vs ELT
| | ETL | ELT |
|-|-----|-----|
| Transform | Before load | After load |
| Approach | Traditional DW | Modern data lake |
| Tools | Informatica, SSIS | dbt, Spark |

---

## 💡 Quick Facts
- **Star schema**: 1 fact, many dims, direct join
- **SCD2**: Full history via start/end dates
- **Bronze**: Raw, append-only, full fidelity
- **External table**: DROP keeps data
- **B-Tree**: Most common index type
