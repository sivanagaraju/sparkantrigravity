# PYSPARK CHEATSHEET - Interview Quick Reference

## 🔥 MEMORY TRICKS

### Transformations vs Actions
**"Transformations are LAZY, Actions TRIGGER execution"**
```
TRANSFORMATIONS (Build DAG):
filter, select, join, groupBy, withColumn, drop, distinct

ACTIONS (Execute):
show, collect, count, write, take, first, reduce
```

### Narrow vs Wide
**"Wide = Shuffle = Slow"**
```
NARROW (No shuffle): filter, select, map, withColumn
WIDE (Shuffle): groupBy, join, repartition, distinct, orderBy
```

### Join Strategy
**"Small table? BROADCAST it!"**
```python
from pyspark.sql.functions import broadcast
large_df.join(broadcast(small_df), "key")
```

---

## 📊 DATAFRAME BASICS

### Create DataFrame
```python
# From list
df = spark.createDataFrame([(1, "a"), (2, "b")], ["id", "val"])

# From dict
df = spark.createDataFrame([{"id": 1, "val": "a"}])

# From Pandas
df = spark.createDataFrame(pandas_df)

# From file
df = spark.read.csv("path", header=True, inferSchema=True)
df = spark.read.parquet("path")
df = spark.read.json("path")
```

### Basic Operations
```python
df.show(5)                    # Display 5 rows
df.printSchema()              # Show schema
df.columns                    # List column names
df.count()                    # Row count
df.describe().show()          # Statistics
df.distinct().count()         # Unique rows
```

---

## 🔧 TRANSFORMATIONS

### Select & Filter
```python
from pyspark.sql.functions import col, lit

# Select columns
df.select("col1", "col2")
df.select(col("col1"), col("col2") * 2)

# Filter
df.filter(col("age") > 25)
df.filter((col("a") > 1) & (col("b") < 10))  # AND
df.filter((col("a") > 1) | (col("b") < 10))  # OR
df.filter(col("name").isNull())
df.filter(col("name").isNotNull())
df.filter(col("status").isin(["A", "B"]))
```

### Add/Modify Columns
```python
# Add column
df.withColumn("new_col", col("old_col") * 2)
df.withColumn("constant", lit("value"))

# Rename
df.withColumnRenamed("old", "new")

# Drop
df.drop("col1", "col2")

# Cast type
df.withColumn("age", col("age").cast("integer"))
```

### String Functions
```python
from pyspark.sql.functions import upper, lower, trim, concat, substring

df.withColumn("upper", upper(col("name")))
df.withColumn("full_name", concat(col("first"), lit(" "), col("last")))
df.withColumn("prefix", substring(col("id"), 1, 3))
```

---

## 🔗 JOINS

### Join Types
```python
# Inner (default)
df1.join(df2, "key")
df1.join(df2, df1.key == df2.key, "inner")

# Left
df1.join(df2, "key", "left")

# Left Anti (rows in df1 NOT in df2)
df1.join(df2, "key", "left_anti")

# Left Semi (rows in df1 that ARE in df2, no df2 cols)
df1.join(df2, "key", "left_semi")

# Broadcast join
from pyspark.sql.functions import broadcast
df1.join(broadcast(df2), "key")
```

### Join on Multiple Keys
```python
df1.join(df2, ["key1", "key2"])
df1.join(df2, (df1.a == df2.a) & (df1.b == df2.b))
```

---

## 📈 AGGREGATIONS

### GroupBy + Agg
```python
from pyspark.sql.functions import sum, avg, count, min, max, countDistinct

df.groupBy("region").agg(
    count("*").alias("total"),
    sum("amount").alias("total_amount"),
    avg("amount").alias("avg_amount"),
    countDistinct("product").alias("unique_products")
)
```

### Window Functions
```python
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number, rank, lag, lead, sum

# Define window
window = Window.partitionBy("region").orderBy("date")

# Apply
df.withColumn("row_num", row_number().over(window))
df.withColumn("rank", rank().over(window))
df.withColumn("prev_val", lag("value", 1).over(window))
df.withColumn("next_val", lead("value", 1).over(window))

# Running total
df.withColumn("running_total", sum("amount").over(
    Window.partitionBy("region").orderBy("date").rowsBetween(Window.unboundedPreceding, 0)
))
```

---

## ⚡ PERFORMANCE

### Partitioning
```python
df.repartition(10)              # Shuffle into 10 partitions
df.repartition("key")           # Partition by column
df.coalesce(1)                  # Reduce partitions (no shuffle)

# Check partitions
df.rdd.getNumPartitions()
```

### Caching
```python
df.cache()               # Cache in memory
df.persist()             # Same as cache
df.unpersist()           # Remove from cache

# Storage levels
from pyspark.storagelevel import StorageLevel
df.persist(StorageLevel.MEMORY_AND_DISK)
```

### Broadcast Variables
```python
lookup = {"A": "Apple", "B": "Banana"}
broadcast_lookup = spark.sparkContext.broadcast(lookup)

# Access in UDF
broadcast_lookup.value["A"]
```

---

## ⚠️ GOTCHAS

### 1. UDF Performance
```python
# ❌ SLOW: Python UDF
@udf
def slow_func(x):
    return x * 2

# ✅ FAST: Built-in function
df.withColumn("doubled", col("x") * 2)

# ✅ FASTER: Pandas UDF
@pandas_udf("long")
def fast_func(x: pd.Series) -> pd.Series:
    return x * 2
```

### 2. API Calls in UDF (ANTI-PATTERN!)
```python
# ❌ TERRIBLE: 1 API call per row
@udf
def get_hash(id):
    return requests.get(f"...{id}").json()

# ✅ CORRECT: mapPartitions
def process_partition(iterator):
    session = requests.Session()  # Reuse connection
    for pdf in iterator:
        # Batch process
        yield pdf
        
df.mapInPandas(process_partition, schema)
```

### 3. Shuffle Partitions
```python
# Default is 200, too many for small data
spark.conf.set("spark.sql.shuffle.partitions", "10")
```

### 4. Collect is Dangerous
```python
# ❌ Can OOM the driver
all_data = df.collect()

# ✅ Sample instead
sample = df.limit(1000).collect()
```

---

## 🎯 COMMON PATTERNS

### Deduplicate
```python
# Keep first
df.dropDuplicates(["key"])

# Keep latest (using window)
window = Window.partitionBy("key").orderBy(col("date").desc())
df.withColumn("rn", row_number().over(window)).filter(col("rn") == 1)
```

### Fill NULLs
```python
df.fillna(0)                    # All numeric
df.fillna({"col1": 0, "col2": "N/A"})  # Specific columns
df.na.fill(0)                   # Alternative
```

### Explode (Array to Rows)
```python
from pyspark.sql.functions import explode, explode_outer

# [1, 2, 3] → 3 rows
df.withColumn("item", explode(col("items")))

# Keeps NULL arrays
df.withColumn("item", explode_outer(col("items")))
```

### Pivot
```python
df.groupBy("region").pivot("product").sum("sales")
# Columns: region, ProductA, ProductB, ...
```

---

## 📁 DELTA LAKE

### Read/Write
```python
# Write
df.write.format("delta").mode("overwrite").save("/path")

# Read
df = spark.read.format("delta").load("/path")

# Time travel
df = spark.read.format("delta").option("versionAsOf", 5).load("/path")
```

### Merge (Upsert)
```python
from delta.tables import DeltaTable

target = DeltaTable.forPath(spark, "/path")
target.alias("t").merge(
    source.alias("s"),
    "t.id = s.id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()
```

---

## 💡 INTERVIEW TIPS

1. **"How would you optimize this?"** → Broadcast join, filter early, cache
2. **"What's wrong with this UDF?"** → API call per row, use mapPartitions
3. **"High memory usage?"** → Check for skew, reduce partitions, cache wisely
4. **"Slow job?"** → Check Spark UI, look for shuffle, look for skew
