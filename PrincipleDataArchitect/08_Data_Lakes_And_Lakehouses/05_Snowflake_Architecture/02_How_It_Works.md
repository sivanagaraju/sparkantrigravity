# Snowflake Architecture — How It Works

Snowflake’s genius is achieving the complete separation of compute and storage while somehow managing to perform complex SQL queries faster than traditional on-premise systems.

It achieves this via a strict **Three-Layer Architecture**.

---

## Layer 1: Database Storage (The Muscle)

When you load data into Snowflake, it completely reorganizes the data. It does not just dump open-source Parquet files into an S3 bucket.

Instead, Snowflake crunches the data into its proprietary optimized format and stores it on AWS S3, Azure Blob, or Google Cloud Storage.
*   **Columnar:** Data is stored by column, not by row. If you `SELECT SUM(salary) FROM employees`, Snowflake physically only reads the `salary` column from the hard drives, abandoning the `name` and `address` bytes entirely, massively speeding up analytics.
*   **Micro-Partitions:** This is Snowflake's secret weapon. Snowflake completely abandons traditional database "Indexes". Instead, it dynamically chops all incoming data into contiguous, immutable blocks roughly 50-500 MB in size called Micro-Partitions. 

*The Storage layer is "dumb". It just holds encrypted, compressed bytes. You pay purely for the raw AWS S3 passthrough cost (roughly $23 per Terabyte per month).*

---

## Layer 2: Compute / Virtual Warehouses (The Engine)

This is where the actual SQL execution happens. 
A "Virtual Warehouse" is simply a cluster of EC2 Virtual Machines that Snowflake provisions on your behalf.
*   **T-Shirt Sizing:** You select sizes (X-Small, Small, Medium, Large, X-Large). An X-Small is exactly 1 server. A Small is exactly 2 servers. A Large is 8 servers. Every jump exactly doubles the compute power, and exactly doubles the cost per hour.
*   **Scaling Up (Performance):** If a massive 10-Billion row query takes 10 minutes on a Small warehouse, you can execute an `ALTER WAREHOUSE SET SIZE = LARGE` command. The query now finishes in roughly 1 minute.
*   **Scaling Out (Concurrency):** If 5,000 dashboard users hit your Small warehouse simultaneously, the single server will choke, and queries will queue. You can configure **Multi-Cluster Warehouses**. Snowflake will magically spin up identical Small warehouses parallel to each other dynamically to absorb the tsunami of users, then shut them down when the users go to sleep.

*You pay for Compute strictly by the second (after a 1-minute minimum). If a warehouse auto-suspends on Friday at 5:00 PM and wakes up on Monday at 9:00 AM, you pay $0.00 for the weekend compute.*

---

## Layer 3: Cloud Services (The Brain)

This is the globally distributed control plane sitting strictly above the Compute and Storage layers. It is fully managed by Snowflake and handles everything required to bind the system together.
*   **Authentication & Security:** Handles login, RBAC (Role-Based Access Control), and encryption keys.
*   **Query Parsing & Optimization:** When you submit a SQL query, this layer builds the execution plan before handing it to the Virtual Warehouse.
*   **The Metadata Manager:** This is the most critical component. It tracks exactly which Micro-Partitions contain which data.

### How Micro-Partitions and Metadata Enable Microsecond Queries

If you write `SELECT * FROM sales WHERE date = '2023-10-01'`, how does Snowflake return the answer instantly from a 10 Petabyte table?
1. The Cloud Services layer heavily analyzes the Metadata it captured when the data was originally ingested.
2. It knows physically there are 1,000,000 Micro-Partitions on S3.
3. Crucially, the Metadata specifically contains the **Min/Max stat values** for every single column exactly within every individual Micro-Partition.
4. The Brain sees that Micro-Partition #42 only contains dates from `2020-01-01` to `2021-01-01`.
5. The Brain instantly prunes Micro-Partition #42 from the execution plan. It requires exactly ZERO compute power to ignore it.
6. Ultimately, the Brain realizes that out of 1,000,000 Micro-Partitions, only 15 actually contain data for `2023-10-01`. 
7. It hands those 15 explicit S3 URLs to the Virtual Warehouse. The Warehouse connects to S3, executes 15 rapid `GET` requests, and returns the data in milliseconds.
