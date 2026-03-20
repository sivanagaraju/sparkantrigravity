# Snowflake Architecture — Pitfalls and Anti-Patterns

## Anti-Pattern 1: The Infinite Compute Bill (Failing to Auto-Suspend)

Snowflake charges by the second. If you treat Snowflake like an On-Premise Oracle database and simply turn the server on and leave it running permanently, your bill will be astronomical.

### The Trap
A database administrator provisions an X-Large Virtual Warehouse (16 Servers) for the Data Science team. The DBA creates the warehouse using standard traditional SQL, intentionally omitting the `AUTO_SUSPEND` parameter because they assume the data scientists need it "available" all day.
The data scientists run a massive ML aggregation query at 9:00 AM that takes 5 minutes. They then spend the next 7 hours analyzing the resulting CSV locally on their laptops. At 5:00 PM they go home.
Because `AUTO_SUSPEND` was missing, the 16 servers literally sit there executing zero queries, idling for the entire month. The company receives an absolutely staggering $20,000 monthly invoice for a cluster that did exactly 5 minutes of actual mathematical work.

### Concrete Fix
Almost every single Virtual Warehouse must be explicitly configured to shut itself off the instant the query queue hits zero.
- **Correction:** `ALTER WAREHOUSE data_science_wh SET AUTO_SUSPEND = 60;`
- This ensures the warehouse immediately destroys its underlying AWS EC2 servers after 60 seconds of complete inactivity. When the data scientist sends another query at 3:00 PM the next day, the `AUTO_RESUME = TRUE` parameter automatically wakes the warehouse up in roughly 1-2 seconds, rendering the sleeping state practically invisible to the user.

---

## Anti-Pattern 2: The "Select Star" Full Table Scan (Micro-Partition Failure)

Snowflake doesn't use standard B-Tree indexes. It uses Metadata Pruning against its Micro-Partitions. If you structure your data poorly, the Brain cannot prune the partitions, causing massive Full Table Scans.

### The Trap
A company dumps 5 years of Global Sales Data (1 Petabyte) into Snowflake. They ingest the data completely randomly as it arrives from 50 different countries.
A user executes: `SELECT * FROM global_sales WHERE country = 'Japan';`
1. Snowflake's Cloud Services layer checks the metadata.
2. It looks at the Min/Max values for `country` across all 4 million Micro-Partitions.
3. Because the data was ingested completely randomly, *every single* Micro-Partition contains at least one sale from Japan. The Min value is alphabetically "Afghanistan" and the Max is "Zimbabwe".
4. The Brain fails to prune a single file. It tells the Virtual Warehouse it must physically download and scan all 4 million Micro-Partitions (1 PB) to find the Japanese sales. The query takes 45 minutes and costs $50 in compute.

### Concrete Fix
You must explicitly sort/cluster massively queried tables so the micro-partitions group mathematically.
- **Correction:** `ALTER TABLE global_sales CLUSTER BY (country);`
- Snowflake will mathematically rewrite the background Parquet files to group Japanese rows exclusively with other Japanese rows. Now, when the user queries Japan, the Brain realizes that exactly 95 of the 4,000,000 Micro-Partitions contain "Japan", and it instantly prunes 99.999% of the S3 files. The query executes in 2 seconds.

---

## Anti-Pattern 3: Utilizing X-Large Warehouses for High Concurrency (Scaling Up instead of Out)

T-Shirt sizing (Scaling Up) gives you more CPU horsepower to crunch a *single* massive query faster. It is entirely the wrong tool for rescuing a struggling dashboard experiencing thousands of *small* queries.

### The Trap
At 9:00 AM on Monday, 5,000 external customers log into a customer-facing reporting dashboard. The dashboard fires 5,000 tiny, simple 1-second queries at a `SMALL` Snowflake warehouse. 
The Small warehouse (2 servers) can only process about 16 queries simultaneously. The remaining 4,984 queries are shoved into a queue. Customers stare at a spinning loading wheel for 10 minutes. 
The DevOps engineer panics and executes `ALTER WAREHOUSE SET WAREHOUSE_SIZE = 'X-LARGE'`.
The X-Large warehouse (16 servers) is designed to scan Petabytes of data. It still only has 16 primary processing nodes, meaning it only marginally improves concurrency to maybe 128 simultaneous queries. The queue drops slightly, but the dashboard fundamentally remains broken, and the company is now burning $16/hour instead of $2/hour.

### Concrete Fix
When dealing with massive "Dashboard" user volumes (Concurrency), you must Scale Out, not Up.
- **Correction:** Keep the warehouse `SMALL`, but convert it to a **Multi-Cluster Warehouse**.
- `ALTER WAREHOUSE reporting_wh SET MIN_CLUSTER_COUNT = 1, MAX_CLUSTER_COUNT = 10;`
- Now, when the 5,000 queries hit, Snowflake instantly clones the Small warehouse 10 times sideways. You now have 10 isolated Small clusters collectively destroying the 5,000-query backlog in parallel, solving the dashboard nightmare instantly. When the users leave, the clusters gracefully shut down 9 -> 8 -> 1.
