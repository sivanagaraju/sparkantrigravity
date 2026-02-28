import sys
import os
import requests
import hashlib
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

# FORCE SPARK TO USE THE SAME PYTHON INTERPRETER
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

def verify_full_stack():
    print("Initializing Spark for Full Stack Check...")
    spark = SparkSession.builder \
        .appName("Verify_Full_Stack") \
        .master("local[*]") \
        .getOrCreate()

    # 1. Verify API Connectivity (Real Request)
    print("Verifying External API Connectivity (hashify.net)...")
    try:
        url = "https://api.hashify.net/hash/md4/hex?value=test"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            print(f"API Success! MD4('test') = {resp.json().get('Digest')}")
        else:
            print(f"API Warning: Status Code {resp.status_code}")
    except Exception as e:
        print(f"API Warning (Not Blocked): {e}")

    # 2. Verify Local Computation (MD5 substitute)
    print("Verifying Local Computation Logic...")
    data = [("test_claim",)]
    df = spark.createDataFrame(data, ["claim_id"])
    
    # Check if we can run the local hex(unhex(md5)) logic
    df.withColumn("hash_local", F.expr("hex(unhex(md5(claim_id)))")).show()

    spark.stop()
    print("Verification Completed.")

if __name__ == "__main__":
    verify_full_stack()
