import requests
from pyspark.sql import SparkSession
from pyspark.sql.functions import pandas_udf, udf, col
from pyspark.sql.types import StringType
from typing import Iterator
import pandas as pd
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_spark_session():
    return SparkSession.builder \
        .appName("OptimizationDemo") \
        .master("local[*]") \
        .getOrCreate()

# ---------------------------------------------------------
# APPROACH 1: The "Bad" Way (Row-by-Row UDF)
# ---------------------------------------------------------
def get_hash_api_row_by_row(claim_id):
    """
    Makes a network call for EVERY row.
    Anti-pattern for high volume data.
    """
    if not claim_id:
        return ""
    try:
        # Simulate API call
        # response = requests.get(f"https://api.hashify.net/hash/md4/hex?value={claim_id}")
        # return response.json().get("Digest", "")
        return f"hash_{claim_id}" # Mock return for demo
    except Exception:
        return ""

def run_udf_approach(df):
    logger.info("Running UDF Approach...")
    # Register UDF
    hash_udf = udf(get_hash_api_row_by_row, StringType())
    
    # Apply UDF
    return df.withColumn("hash_id", hash_udf(col("claim_id")))

# ---------------------------------------------------------
# APPROACH 2: The "Better" Way (mapPartitions)
# ---------------------------------------------------------
def fetch_hashes_batch(iterator: Iterator[pd.DataFrame]) -> Iterator[pd.DataFrame]:
    """
    Processes a partition of data.
    1. Initializes session ONCE per partition.
    2. Processes rows in batches (if API supports it) or reuses connection.
    """
    # Initialize session once per partition (Connection Pooling)
    session = requests.Session()
    
    for pdf in iterator:
        # pdf is a pandas DataFrame chunk
        results = []
        for claim_id in pdf['claim_id']:
            if not claim_id:
                results.append("")
                continue
            
            try:
                # In a real scenario, you might batch these IDs and send 1 request for 100 IDs
                # url = f"https://api.hashify.net/batch_hash"
                # response = session.post(url, json={"ids": batch})
                
                # For demo, we still loop but reuse the 'session' object
                # response = session.get(f"https://api.hashify.net/hash/md4/hex?value={claim_id}")
                results.append(f"optimized_hash_{claim_id}")
            except Exception:
                results.append("")
        
        yield pd.DataFrame({'claim_id': pdf['claim_id'], 'hash_id': results})

def run_map_partitions_approach(df):
    logger.info("Running mapPartitions Approach...")
    
    # MapPartitions usually works with RDDs or Pandas UDFs (Scalar Iterator) in newer Spark
    # Here we use mapInPandas (available in Spark 3.0+) which is the modern mapPartitions for DataFrames
    
    schema = "claim_id string, hash_id string"
    
    return df.mapInPandas(fetch_hashes_batch, schema=schema)

# ---------------------------------------------------------
# APPROACH 3: The "Best" Way (Join with Pre-fetched Data)
# ---------------------------------------------------------
# If the API data is static or we can fetch all relevant keys upfront
def run_join_approach(spark, main_df):
    logger.info("Running Join Approach...")
    
    # 1. Get distinct IDs to fetch
    distinct_ids = main_df.select("claim_id").distinct().collect()
    
    # 2. Fetch hashes in bulk on the Driver (or using a separate efficient job)
    # This avoids hitting the API from executors entirely
    hashes = []
    for row in distinct_ids:
        # Fetch hash...
        hashes.append((row.claim_id, f"hash_{row.claim_id}"))
        
    # 3. Create a DataFrame from the hashes
    hashes_df = spark.createDataFrame(hashes, ["claim_id", "hash_id"])
    
    # 4. Join back
    return main_df.join(hashes_df, "claim_id", "left")

if __name__ == "__main__":
    spark = get_spark_session()
    
    # Create Dummy Data
    data = [(f"claim_{i}",) for i in range(100)]
    df = spark.createDataFrame(data, ["claim_id"])
    
    # Run Approaches
    df_udf = run_udf_approach(df)
    df_udf.show(5)
    
    df_optimized = run_map_partitions_approach(df)
    df_optimized.show(5)
    
    df_join = run_join_approach(spark, df)
    df_join.show(5)
    
    spark.stop()
