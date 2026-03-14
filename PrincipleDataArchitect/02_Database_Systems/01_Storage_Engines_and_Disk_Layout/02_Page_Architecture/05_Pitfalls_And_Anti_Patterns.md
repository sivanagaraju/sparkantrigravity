# Page Architecture — Pitfalls & Anti-Patterns

---

## Anti-Pattern 1: VARCHAR(255) for Every String Column

**Wrong way**: Defaulting to `VARCHAR(255)` or `TEXT` for all string columns without measuring actual data lengths.

**Why it's wrong**: While PostgreSQL doesn't pre-allocate storage for `VARCHAR(255)`, it affects the query planner's row width estimates. The planner uses `avg_width` from `pg_statistic` for cost calculations. Wider estimated rows → higher estimated scan costs → suboptimal plans.

**Detection**:
```sql
-- Check actual vs declared column widths
SELECT attname, 
       atttypmod - 4 AS declared_max,  -- VARCHAR length
       avg_width
FROM pg_stats 
WHERE tablename = 'your_table' AND avg_width IS NOT NULL
ORDER BY avg_width DESC;
-- If declared_max >> avg_width, columns are over-declared
```

**Fix**: Right-size columns based on actual data analysis. Use `VARCHAR(30)` if max observed length is 25 characters. Use `UUID` type (16 bytes) instead of `VARCHAR(36)`.

---

## Anti-Pattern 2: Ignoring Tuple Header Overhead

**Wrong way**: Assuming a 4-byte INT column only uses 4 bytes on disk.

**Why it's wrong**: Every tuple has a 23-byte header + null bitmap (1 bit per column). A single `INT` column still costs 23 (header) + 1 (null bitmap) + 4 (data) = 28 bytes → padded to 32 bytes. That's 8x the "data" cost.

**Detection**: Check actual table size vs expected:
```sql
-- Expected: 10M rows × 4 bytes = 40 MB
-- Actual:
SELECT pg_size_pretty(pg_relation_size('my_int_table'));
-- Returns: 364 MB (because 10M × 32 bytes = 320 MB + overhead)
```

**Fix**: For narrow, frequently-accessed data, consider denormalization or array types. For columns that are always NULL, add them at the end (null bitmap bit is free; the column takes 0 bytes when NULL).

---

## Anti-Pattern 3: Not Monitoring Buffer Hit Ratio

**Wrong way**: Running a multi-GB database with default `shared_buffers = 128MB` and never checking cache performance.

**Detection**:
```sql
-- Buffer hit ratio query
SELECT 
    sum(heap_blks_hit) AS hits,
    sum(heap_blks_read) AS misses,
    round(sum(heap_blks_hit)::numeric / 
          GREATEST(sum(heap_blks_hit) + sum(heap_blks_read), 1) * 100, 2) AS hit_ratio
FROM pg_statio_user_tables;
-- If hit_ratio < 95%, you need more shared_buffers or better schema design
```

**Fix**: 
- Set `shared_buffers` to 25% of total RAM (PostgreSQL recommendation)
- Set `effective_cache_size` to 75% of RAM (tells planner about OS cache)
- If hit ratio still low: optimize row widths to fit more rows per page

---

## Anti-Pattern 4: Storing BLOBs in Main Table

**Wrong way**: Storing images, PDFs, or large JSON documents (>2KB) directly in the main table.

**Why it's wrong**: PostgreSQL TOAST threshold is ~2KB. Values exceeding this are stored in a separate TOAST table. Every row fetch that touches a TOASTed column requires an additional I/O to the TOAST table. Even `SELECT *` on a table with one TOASTed column triggers TOAST reads for EVERY row.

**Detection**: 
```sql
-- Check TOAST usage
SELECT relname, 
       pg_size_pretty(pg_relation_size(reltoastrelid)) AS toast_size
FROM pg_class 
WHERE reltoastrelid != 0 AND relkind = 'r'
ORDER BY pg_relation_size(reltoastrelid) DESC;
```

**Fix**: Store large objects in a separate table or external storage (S3). Keep the main table narrow for fast sequential scans.

---

## Anti-Pattern 5: Default fillfactor=100 on Write-Heavy Indexes

**Wrong way**: Creating B-Tree indexes with default `fillfactor=100` on tables with frequent inserts/updates.

**Why it's wrong**: 100% fill → every insert into a full page causes a page split. Page splits are expensive: allocate new page + move half the entries + update parent + WAL-log everything. Under concurrent load, this creates lock contention.

**Detection**: Monitor `pg_stat_user_indexes` for `idx_tup_insert` rate. Correlate with latency spikes.

**Fix**:
```sql
-- Leave 30% headroom for future inserts
CREATE INDEX idx_orders_ts ON orders (created_at) WITH (fillfactor = 70);
-- Or ALTER existing index
ALTER INDEX idx_orders_ts SET (fillfactor = 70);
REINDEX INDEX idx_orders_ts;  -- rebuild with new fillfactor
```
