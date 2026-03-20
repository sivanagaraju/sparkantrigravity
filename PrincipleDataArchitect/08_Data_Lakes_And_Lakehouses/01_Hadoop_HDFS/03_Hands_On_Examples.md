# Hadoop & HDFS — Hands-On Examples

While Hadoop cluster engineering is highly complex, interacting with the HDFS storage layer via command line feels fundamentally like navigating a standard Bash/Linux file system.

## Scenario 1: Interacting with the HDFS File System

You interact with HDFS largely using the `hdfs dfs` command wrapper.

### Execution

```bash
# List the root directory of the distributed file system
$ hdfs dfs -ls /
Found 3 items
drwxr-xr-x   - hdfs supergroup          0 2023-10-01 10:00 /tmp
drwxr-xr-x   - hdfs supergroup          0 2023-10-01 10:05 /user
drwxr-xr-x   - hive supergroup          0 2023-10-01 10:10 /warehouse

# Create a new directory for user data
$ hdfs dfs -mkdir /user/analytics/raw_logs

# Upload a massive 5GB local CSV file directly into HDFS
# (Under the hood, the client asks the NameNode for DataNode IPs, splits the file into 
# roughly 40 x 128MB blocks, and streams them in parallel to the cluster)
$ hdfs dfs -put ./local_server_logs_2023.csv /user/analytics/raw_logs/

# Check the file size and replication factor inside HDFS
$ hdfs dfs -ls /user/analytics/raw_logs
Found 1 items
-rw-r--r--   3 sivan supergroup 5368709120 2023-10-01 10:30 /user/analytics/raw_logs/local_server_logs_2023.csv
# Notice the '3' right after the permissions. That indicates a replication factor of 3 for this file.

# Read the first few lines of the distributed file
# (Fetches only the beginning of Block 0 from whatever server holds it)
$ hdfs dfs -cat /user/analytics/raw_logs/local_server_logs_2023.csv | head -n 5
```

## Scenario 2: Changing Replication Factor Dynamically

Sometimes, a dataset relies on heavy parallel reads. If 500 Spark jobs are attempting to read the exact same 3 blocks simultaneously from 3 DataNodes, the network interfaces of those 3 nodes will saturate. You can dynamically crank up the replication factor to heavily distribute the read-load physically across the cluster.

### Execution

```bash
# Increase the replication factor of a critical lookup table from 3 to 10
$ hdfs dfs -setrep -w 10 /user/analytics/critical_lookup.csv
Replication 10 set: /user/analytics/critical_lookup.csv
Waiting for /user/analytics/critical_lookup.csv ...
WARNING: the waiting time may be long for DECREASING the number of replications.
. done

# Behind the scenes: The NameNode immediately commands DataNodes possessing the file
# to begin copying blocks over the data-center network onto 7 new physical machines.
```

## Scenario 3: Checking the Heartbeat (fsck)

Just like Linux has `fsck` to check disk consistency, Hadoop has a command allowing the administrator to query the NameNode for any corrupted or dangerously under-replicated blocks.

### Execution

```bash
# Run a File System Check on the root directory
$ hdfs fsck /

Total size:    5368709120 B
Total dirs:    4
Total files:   1
Total blocks (validated):      40 (avg. block size 134217728 B)
Minimally replicated blocks:   40 (100.0 %)
Over-replicated blocks:        0 (0.0 %)
Under-replicated blocks:       0 (0.0 %)
Mis-replicated blocks:         0 (0.0 %)
Default replication factor:    3
Average block replication:     3.0
Corrupt blocks:                0
Missing replicas:              0

The filesystem under path '/' is HEALTHY
```

## Scenario 4: Querying Data via Apache Hive

Writing native Java MapReduce jobs was notoriously difficult—requiring hundreds of lines of boilerplate code just to run a basic `GROUP BY` summation. 
Facebook invented **Apache Hive** largely to resolve this. Hive translates standard SQL directly into complex Java MapReduce (or Tez) DAGs in the background, making Hadoop accessible to analysts.

### Execution

```sql
-- In the Hive CLI interface:
-- We define a logical table mapping to the physical unstructured directory in HDFS
CREATE EXTERNAL TABLE web_logs (
    ip_address STRING,
    event_timestamp TIMESTAMP,
    url STRING,
    status_code INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LOCATION '/user/analytics/raw_logs/';

-- Now an analyst can run a simple SQL query. 
-- Hive intercepts this, spins up YARN containers, parses the HDFS blocks, shuffles 
-- the IP addresses over the network, and reduces the counts.
SELECT ip_address, COUNT(*) as hit_count
FROM web_logs
WHERE status_code = 404
GROUP BY ip_address
ORDER BY hit_count DESC
LIMIT 10;
```
