from pyspark.sql import SparkSession
from pyspark.sql.functions import col, rand, floor, broadcast, lit, expr
import random

# =========================================================
# ADVANCED PYSPARK SCENARIOS
# =========================================================

def get_spark():
    return SparkSession.builder.appName("AdvancedPySpark").master("local[*]").getOrCreate()

# ---------------------------------------------------------
# SCENARIO 1: Handling Data Skew (The "Salting" Technique)
# Problem: One key has 90% of the data. Joining on this key causes OOM on one executor.
# Solution: Add a random "salt" to the skewed key to distribute it across partitions.
# ---------------------------------------------------------
def skew_handling_demo(spark):
    print("--- Running Skew Handling Demo (Salting) ---")
    
    # 1. Create Skewed Data (Key 'A' has mostly all data)
    large_data = [("A", i) for i in range(100000)] + [("B", i) for i in range(100)]
    large_df = spark.createDataFrame(large_data, ["key", "value"])
    
    small_data = [("A", "Info A"), ("B", "Info B")]
    small_df = spark.createDataFrame(small_data, ["key", "info"])
    
    # 2. The "Salted" Join Strategy
    SALT_FACTOR = 10
    
    # Step A: Add Salt to the Large (Skewed) Table
    # New Key = key + "_" + random_int(0, 10)
    salted_large_df = large_df.withColumn(
        "salted_key", 
        expr(f"concat(key, '_', floor(rand() * {SALT_FACTOR}))")
    )
    
    # Step B: Explode the Small Table to match the salts
    # We need 'A_0', 'A_1', ... 'A_9' for every 'A' in the small table
    # This replicates the small table rows, but allows even distribution of the large table
    exploded_small_df = small_df.withColumn(
        "salt_array", 
        expr(f"sequence(0, {SALT_FACTOR}-1)")
    ).select(
        "key", "info", 
        expr("explode(salt_array)").alias("salt")
    ).withColumn(
        "salted_key", 
        expr("concat(key, '_', salt)")
    )
    
    # Step C: Join on the Salted Key
    # Now the join is evenly distributed across 10 partitions instead of 1
    result_df = salted_large_df.join(exploded_small_df, "salted_key", "inner")
    
    print(f"Joined Count: {result_df.count()}")
    result_df.explain() # Show plan to verify no broadcast (if we pretended it was too big to broadcast)

# ---------------------------------------------------------
# SCENARIO 2: Bucketing (Optimization for frequent joins)
# Problem: You join two large tables on 'user_id' every day. It always shuffles.
# Solution: Pre-bucket both tables by 'user_id' so they are co-located.
# ---------------------------------------------------------
def bucketing_demo(spark):
    print("\n--- Running Bucketing Demo ---")
    
    df1 = spark.range(0, 1000).select(col("id").alias("user_id"), lit("data1").alias("val1"))
    df2 = spark.range(0, 1000).select(col("id").alias("user_id"), lit("data2").alias("val2"))
    
    # Save as Bucketed Tables
    # spark.conf.set("spark.sql.sources.bucketing.enabled", "true")
    
    # df1.write.bucketBy(4, "user_id").sortBy("user_id").saveAsTable("bucketed_table_1")
    # df2.write.bucketBy(4, "user_id").sortBy("user_id").saveAsTable("bucketed_table_2")
    
    # When joining bucketed tables, Spark skips the Shuffle phase!
    # joined = spark.table("bucketed_table_1").join(spark.table("bucketed_table_2"), "user_id")
    # joined.explain()
    print("Bucketing code provided in comments (requires Hive support/tables)")

# ---------------------------------------------------------
# SCENARIO 3: Broadcast Join (The "Map-Side" Join)
# Problem: Joining a 10TB table with a 100MB table. Standard join shuffles 10TB.
# Solution: Broadcast the 100MB table to all nodes.
# ---------------------------------------------------------
def broadcast_join_demo(spark):
    print("\n--- Running Broadcast Join Demo ---")
    
    large_df = spark.range(0, 100000).withColumn("key", (col("id") % 10).cast("string"))
    small_df = spark.createDataFrame([("0", "Zero"), ("1", "One")], ["key", "label"])
    
    # Force broadcast (though Spark does this automatically for small tables < 10MB)
    joined = large_df.join(broadcast(small_df), "key")
    
    joined.explain()
    print(f"Broadcast Join Count: {joined.count()}")

if __name__ == "__main__":
    spark = get_spark()
    skew_handling_demo(spark)
    broadcast_join_demo(spark)
    # bucketing_demo(spark)
    spark.stop()
