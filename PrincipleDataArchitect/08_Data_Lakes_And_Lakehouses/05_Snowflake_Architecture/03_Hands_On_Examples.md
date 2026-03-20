# Snowflake Architecture — Hands-On Examples

The primary interface for Snowflake is simply the Snowflake Web App (Snowsight) writing standard ANSI SQL. Almost every architectural aspect of the cloud environment—including provisioning literal hardware—is perfectly controllable via standard SQL DDL commands.

## Scenario 1: Provisioning and Suspending Hardware via SQL

In the old world, getting a new server meant calling AWS or physical IT. In Snowflake, you summon and destroy CPU clusters natively in SQL.

### Execution (SQL)

```sql
-- 1. Create a brand new Compute cluster completely isolated from the rest of the company
CREATE WAREHOUSE data_science_wh WITH 
  WAREHOUSE_SIZE = 'LARGE'  -- 8 Servers
  AUTO_SUSPEND = 60         -- Shut down and stop billing me after exactly 60 seconds of inactivity
  AUTO_RESUME = TRUE        -- If someone sends a query while it's sleeping, instantly wake it up
  INITIALLY_SUSPENDED = TRUE;

-- 2. Tell the system to explicitly use this new hardware for the next query
USE WAREHOUSE data_science_wh;

-- 3. Execute the massive query
SELECT count(*) FROM petabyte_sales_table;
-- The warehouse immediately wakes up, takes ~2 seconds to provision, executes the query, 
-- and then goes perfectly to sleep 60 seconds later, halting the billing meter.
```

---

## Scenario 2: Zero-Copy Cloning

Creating a "Staging" environment historically required copying a 10-Terabyte Production database over the network, taking 3 days and instantly doubling your storage bill. Snowflake uses metadata pointers to explicitly point the new clone at the exact same physical Micro-Partitions as the original table, achieving this in milliseconds for $0.00.

### Execution (SQL)

```sql
-- 1. A developer wants a sandbox to test a destructive script.
-- This command executes in ~3 seconds, regardless of whether the production DB is 1 GB or 100 PB.
CREATE DATABASE analytics_dev_sandbox CLONE analytics_production;

-- 2. The developer can completely drop tables in the sandbox or insert new rows. 
-- Because Snowflake uses Copy-On-Write, only the new rows the developer inserts will 
-- physically consume new S3 storage and generate AWS billing costs. 
-- The production database remains 100% untouched and perfectly safe.
```

---

## Scenario 3: Time Travel (Querying Historical States)

Like Delta Lake and Iceberg, Snowflake retains older Micro-Partitions temporarily before Garbage Collecting them. By default, Standard edition saves 1 day of Time Travel. Enterprise edition allows up to 90 days of Time Travel natively.

### Execution (SQL)

```sql
-- A junior analyst accidentally ran this without a WHERE clause at exactly 12:00 PM
-- UPDATE users SET account_status = 'BANNED'

-- 1. We can view the table safely exactly as it existed before the massacre at 11:55 AM.
SELECT * FROM users AT(TIMESTAMP => '2023-10-01 11:55:00'::timestamp_tz);

-- 2. We can view the table based on the explicit internal Query ID of the bad UPDATE statement
SELECT * FROM users BEFORE(STATEMENT => '8e5d0ca9-005e-44e6-b858-a8f5b37c5726');

-- 3. To completely restore the damaged table in seconds:
CREATE TABLE users_restored AS 
SELECT * FROM users AT(TIMESTAMP => '2023-10-01 11:55:00'::timestamp_tz);

ALTER TABLE users SWAP WITH users_restored;
```

---

## Scenario 4: Secure Data Sharing

Historically, giving a partner vendor (e.g., a marketing agency) access to your data meant writing an ETL script to dump CSVs to an SFTP server every night. The data was immediately stale and highly insecure. Snowflake allows you to grant read-access to your live database pointers directly to another Snowflake account.

### Execution (SQL)

```sql
-- 1. Create a "Share" object
CREATE SHARE marketing_agency_share;

-- 2. Grant the explicit table to the share
GRANT SELECT ON TABLE production.marketing.clicks TO SHARE marketing_agency_share;

-- 3. Add the partner's unique Snowflake Account ID to the share.
ALTER SHARE marketing_agency_share ADD ACCOUNTS = xy12345;

-- The partner instantly sees the live data in their Snowflake account query pane. 
-- They pay for their own Compute (Virtual Warehouses) to query the data. 
-- You do not pay for their compute, and no data is copied.
```
