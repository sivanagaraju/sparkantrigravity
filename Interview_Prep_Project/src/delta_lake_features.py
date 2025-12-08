from pyspark.sql import SparkSession
from delta.tables import *
import shutil
import os

# =========================================================
# DELTA LAKE FEATURES (The "Lakehouse" Engine)
# =========================================================

# Note: To run this, you need the Delta Lake packages installed.
# spark-submit --packages io.delta:delta-core_2.12:2.4.0 ...

def get_delta_spark():
    return SparkSession.builder \
        .appName("DeltaLakeDemo") \
        .master("local[*]") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

def delta_demo():
    spark = get_delta_spark()
    path = "/tmp/delta-table-demo"
    
    # Cleanup
    if os.path.exists(path):
        shutil.rmtree(path)
        
    # 1. Create Delta Table (Bronze)
    data = [("1", "A", 100), ("2", "B", 200)]
    df = spark.createDataFrame(data, ["id", "val", "amount"])
    df.write.format("delta").save(path)
    
    print("--- Initial Data ---")
    spark.read.format("delta").load(path).show()
    
    # 2. UPSERT (Merge) - The "Silver" Layer Logic
    # Scenario: New data arrives. ID 1 is updated, ID 3 is new.
    new_data = [("1", "A_updated", 150), ("3", "C", 300)]
    new_df = spark.createDataFrame(new_data, ["id", "val", "amount"])
    
    deltaTable = DeltaTable.forPath(spark, path)
    
    deltaTable.alias("old").merge(
        new_df.alias("new"),
        "old.id = new.id"
    ).whenMatchedUpdate(set = {
        "val": "new.val",
        "amount": "new.amount"
    }).whenNotMatchedInsert(values = {
        "id": "new.id",
        "val": "new.val",
        "amount": "new.amount"
    }).execute()
    
    print("--- After Upsert (Merge) ---")
    spark.read.format("delta").load(path).show()
    
    # 3. Time Travel (History)
    print("--- Table History ---")
    deltaTable.history().show()
    
    # Read version 0 (Before update)
    print("--- Time Travel (Version 0) ---")
    spark.read.format("delta").option("versionAsOf", 0).load(path).show()
    
    # 4. Schema Evolution (Adding a column)
    # Delta allows schema evolution if enabled
    extra_data = [("4", "D", 400, "USA")]
    extra_df = spark.createDataFrame(extra_data, ["id", "val", "amount", "country"])
    
    extra_df.write.format("delta").mode("append").option("mergeSchema", "true").save(path)
    
    print("--- After Schema Evolution ---")
    spark.read.format("delta").load(path).show()

if __name__ == "__main__":
    # This might fail if Delta jars are not in the environment, 
    # but the code is valid for the interview discussion.
    try:
        delta_demo()
    except Exception as e:
        print(f"Delta Demo skipped (requires Delta jars): {e}")
