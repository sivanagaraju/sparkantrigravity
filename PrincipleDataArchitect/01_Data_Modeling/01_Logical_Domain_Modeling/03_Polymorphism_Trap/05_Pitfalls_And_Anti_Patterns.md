# Polymorphism Trap — Common Pitfalls & Anti-Patterns

> The top mistakes, detection, and remediation.

---

## ❌ Pitfall 1: Defaulting to STI Because the ORM Makes It Easy

### What Happens

The ORM (Rails ActiveRecord, Django, SQLAlchemy) supports STI with a single `type` column. The developer creates `class EmailNotification < Notification` and the ORM auto-generates the schema with 40 NULL columns.

### Why It's Dangerous

What works for 10K rows in development becomes a performance disaster at 100M rows in production. The ORM hides the cost of wide, sparse tables behind clean class hierarchies.

### Detection

```sql
-- Find tables with high NULL density (STI indicator)
SELECT 
    table_name,
    COUNT(*) AS total_columns,
    SUM(CASE WHEN is_nullable = 'YES' THEN 1 ELSE 0 END) AS nullable_columns,
    ROUND(100.0 * SUM(CASE WHEN is_nullable = 'YES' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
GROUP BY table_name
HAVING COUNT(*) > 10
ORDER BY pct_nullable DESC;
-- Tables with > 50% nullable columns are STI candidates
```

### Fix

Evaluate whether CTI or CCI is more appropriate. For analytical workloads, almost always switch to CCI.

---

## ❌ Pitfall 2: Polymorphic Associations Without Referential Integrity

### What Happens

```sql
-- The morphable pattern — NO FK possible
commentable_type VARCHAR(50),  -- 'Post', 'Video', 'Photo'
commentable_id   BIGINT        -- could point to ANY table
```

### Why It's Dangerous

- The database cannot enforce that `commentable_id` actually exists in the referenced table
- Deleting a Post does not cascade to its comments (orphaned data)
- The query optimizer cannot plan JOINs efficiently

### Detection

```sql
-- Find columns named *_type + *_id (polymorphic association pattern)
SELECT table_name, column_name
FROM information_schema.columns
WHERE column_name LIKE '%_type'
   OR column_name LIKE '%able_type'
ORDER BY table_name;
```

### Fix

Replace with explicit FK columns + CHECK constraint (see Hands-On Examples).

---

## ❌ Pitfall 3: Using EAV (Entity-Attribute-Value) for Flexibility

### What Happens

```sql
CREATE TABLE entity_attributes (
    entity_id   BIGINT,
    attr_name   VARCHAR(100),  -- 'color', 'size', 'weight'
    attr_value  VARCHAR(500)   -- everything is a string
);
```

### Why It's Dangerous

- All values are strings — no type safety, no numeric comparisons without CAST
- No column-level constraints possible
- JOINs are impossible to optimize (self-joins for every attribute)
- Impossible to index effectively
- Violates every normal form

### When EAV Is AcceptableThe ONE case: highly dynamic user-defined attributes with 100+ possible attribute names that change frequently. Even then, JSONB is usually better

### Fix

Use JSONB with functional indexes, or CTI.

---

## ❌ Pitfall 4: Mirroring Application STI in the Data Warehouse

### What Happens

The CDC pipeline copies the application's STI `events` table as-is into the DW. Now the DW has a 200-column, 70%-NULL fact table.

### Why It's Dangerous

Columnar storage engines (Snowflake, BigQuery, Redshift) scan columns, not rows. A query on 3 columns still scans metadata for all 200 columns. The STI pattern negates the primary advantage of columnar storage.

### Fix

The CDC pipeline or dbt staging layer should **split by type** before loading into the DW:

```sql
-- dbt model: split STI into type-specific fact tables
-- models/staging/stg_events_page_view.sql
SELECT event_id, user_id, url, referrer, time_on_page_ms, created_at
FROM {{ source('raw', 'events') }}
WHERE type = 'page_view'
```

---

## ❌ Pitfall 5: Discriminator Column with Skewed Distribution

### What Happens

The `type` column has 95% `page_view`, 3% `click`, 2% `purchase`. The query optimizer sees "95% of the table is page_view" and chooses a full table scan for `WHERE type = 'purchase'` instead of an index seek.

### Why It's Dangerous

The optimizer's cardinality estimate is correct on average but wrong for minority types. A query for `purchase` events should scan 2% of the table but scans 100%.

### Detection

```sql
-- Check type distribution skew
SELECT type, COUNT(*), ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) AS pct
FROM events
GROUP BY type
ORDER BY pct DESC;
-- If any type > 80%, you have a skew problem
```

### Fix

- Use partial indexes: `CREATE INDEX idx_purchases ON events(created_at) WHERE type = 'purchase'`
- Use list partitioning by type: `PARTITION BY LIST (type)`
- Or switch to CCI (separate tables)

---

## Decision Matrix: When Inheritance Is The Wrong Tool Entirely

| Signal | What To Do Instead |
|---|---|
| No shared behavior between types | Use separate tables (composition) |
| Types evolve independently | Use separate tables |
| Analytical workload is primary | Use CCI or star schema |
| Type-specific columns outnumber shared columns | Use CCI |
| Only 1-2 types and few type-specific columns | STI is acceptable |
