# SPARK DEEP DIVESHEET - Lead Engineer Interview

## 🔧 Cluster Architecture
```
RESOURCE MANAGER ─► APPLICATION MASTER (Driver)
        │                    │
        ▼                    ▼
   NODE MANAGERs ────► EXECUTORs ────► TASKs
```

**Modes:**
- `cluster`: Driver in Application Master (production)
- `client`: Driver on local machine (debugging)

---

## 📊 Job → Stage → Task
```
ACTION ────► JOB ────► STAGEs (by shuffle) ────► TASKs (by partition)

df.read().filter().groupBy().count().show()
   │         │         │         │        │
   Stage 0   Stage 0   │         │        │
                    SHUFFLE   Stage 1    ACTION
```

**Wide (shuffle):** groupBy, join, distinct, repartition, orderBy
**Narrow (no shuffle):** filter, select, map, withColumn

---

## 🧠 Memory Layout (8GB executor)
```
┌────────────────────────────────────────────┐
│ UNIFIED MEMORY (60%) = 4.8GB               │
│  ├── Storage (50%) = 2.4GB (cache)        │
│  └── Execution (50%) = 2.4GB (shuffle)    │
├────────────────────────────────────────────┤
│ USER MEMORY (40%) = 3.2GB                  │
│  └── UDFs, data structures                 │
├────────────────────────────────────────────┤
│ + memoryOverhead (10% or 384MB min)        │
│    └── Python workers, JVM overhead        │
└────────────────────────────────────────────┘
```

---

## ⚙️ Key Configurations
```python
# Parallelism
spark.default.parallelism = 200
spark.sql.shuffle.partitions = 200

# Memory
spark.executor.memory = 8g
spark.executor.memoryOverhead = 2g
spark.memory.fraction = 0.6

# Serialization
spark.serializer = org.apache.spark.serializer.KryoSerializer

# Adaptive (Spark 3.0+)
spark.sql.adaptive.enabled = true
spark.sql.adaptive.skewJoin.enabled = true

# Broadcast
spark.sql.autoBroadcastJoinThreshold = 10485760  # 10MB
```

---

## 🔄 Shuffle Internals
```
Map Tasks          Shuffle Files        Reduce Tasks
    │                   │                    │
    ▼                   ▼                    ▼
Write to disk ──► Sort by key ──► Read + Merge

spark.shuffle.spill = true (spill to disk when memory full)
spark.local.dir = /ssd1,/ssd2 (use multiple SSDs)
```

---

## 💾 Caching Levels
| Level | Memory | Disk | Serialized |
|-------|--------|------|------------|
| MEMORY_ONLY | ✓ | | |
| MEMORY_AND_DISK | ✓ | ✓ | |
| MEMORY_ONLY_SER | ✓ | | ✓ |
| DISK_ONLY | | ✓ | |
| OFF_HEAP | Off-heap | | ✓ |

**cache()** = persist(MEMORY_AND_DISK)

---

## 🚀 mapPartitions vs map
```python
# map: Function per ELEMENT (N calls)
rdd.map(lambda x: process(x))

# mapPartitions: Function per PARTITION (P calls)
def process_partition(iterator):
    conn = create_connection()  # Once per partition!
    for row in iterator:
        yield process(conn, row)
    conn.close()

rdd.mapPartitions(process_partition)
```

**Use mapPartitions for:** DB connections, API sessions, loading models

---

## 📦 Bucketing
```python
df.write.bucketBy(16, "join_key").sortBy("join_key").saveAsTable("bucketed")
```
- Same bucket count = no shuffle on join
- Must use saveAsTable (not parquet)

---

## ⚠️ Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| One task slow | Skew | Salting, AQE |
| OOM | Too few partitions | repartition() |
| Many small files | Too many partitions | coalesce() |
| High GC | Large cached data | OFF_HEAP, reduce cache |
| Driver OOM | collect() on big data | write() instead |

---

## 🎯 RDD When?
Use RDD when:
- Low-level control (mapPartitions)
- Unstructured data
- Legacy code

Use DataFrame when:
- Structured data (99% of cases)
- Need Catalyst optimization
- SQL queries

---

## 📈 Catalyst Optimizer
```
Parse → Analyze → Optimize → Physical Plan → Code Gen

# See plan
df.explain(True)

# Enable CBO
spark.sql.cbo.enabled = true
ANALYZE TABLE t COMPUTE STATISTICS
```

---

## 🔥 AQE (Adaptive Query Execution)
```
spark.sql.adaptive.enabled = true
```
1. **Coalesce partitions**: Merge small shuffle partitions
2. **Broadcast conversion**: Small table → broadcast at runtime
3. **Skew join**: Split skewed partitions automatically

---

## 📍 Data Locality
```
PROCESS_LOCAL → NODE_LOCAL → RACK_LOCAL → ANY
    (best)                              (worst)

spark.locality.wait = 3s (wait before falling back)
```
