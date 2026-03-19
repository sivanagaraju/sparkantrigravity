# Time-Series Databases — Common Pitfalls & Anti-Patterns

## The Performance Killers

## Anti-Pattern 1: High-Cardinality Poisoning

**The Trap**: Treating TSDB **Tags** (Labels) like database columns and inserting values with high unique counts (e.g., `user_id`, `order_uuid`, `precise_lat_long`).
**The Danger**: TSDBs build an inverted index across every unique tag combination. If cardinality explodes, the index occupies too much RAM, causing the ingestion pipeline to stall or the database to crash.
**Detection**:
```sql
-- InfluxDB: Find tag cardinality
SHOW CARDINALITY ON metrics;

-- Prometheus: List top high-cardinality metrics
topk(10, count by (__name__) ({__name__=~".+"}))
```
**The Fix**: Move high-cardinality metadata into a related relational database (SQL) or into a Logging system (Elasticsearch/Loki). Only use low-to-medium cardinality values (region, host, version) in TSDB tags.

## Anti-Pattern 2: The "Over-Ingestion" Bloat

**The Trap**: Setting a 1-second scrape interval for 100,000 servers because "more data is better".
**The Danger**: Storage costs skyrocket and query performance drops linearly. Reading 1 month of 1s data requires processing 2.5 million points per series.
**The Fix**: Use **Tiered Retention** and **Downsampling**.
*   Raw Data: Keep for 7 days.
*   1-Minute Rollups: Keep for 3 months.
*   1-Hour Rollups: Keep for 2 years.

## Anti-Pattern 3: Treating TSDB as a Transactional Store

**The Trap**: Using a TSDB to track "User Balances" or "Order Statuses" because of the time component.
**The Danger**: TSDBs are optimized for immutable appends. Updating a value or deleting a specific point is computationally expensive and often results in "Tombstone" bloat that degrades read performance.
**The Fix**: If you need to change data (Update/Delete/ACID), use a standard RDBMS (Postgres). If the data is truly immutable events, use a TSDB.

## Anti-Pattern 4: The "Now" Hotspot (Ingestion Lag)

**The Trap**: Batching local data for 10 minutes before sending it to the TSDB to save network overhead.
**The Danger**: Query engines (especially Prometheus) expect data to be close to "Now". Sending data with 10m old timestamps causes "Lookback" issues where dashboards show empty data for the current window.
**The Fix**: Stream data in small batches or individually with sub-second latency. If backfilling is required, use specialized backfill tools that bypass the real-time buffer.

## Decision Matrix: TSDB vs. Logs vs. Tracing

| Requirement | TSDB (Metrics) | Logging (Logs) | Dist. Tracing (Traces) |
| :--- | :--- | :--- | :--- |
| **"What is happening?"** | ✅ Optimal | ⚠️ Expensive | ❌ No |
| **"Why is it happening?"** | ❌ No | ✅ Optimal | ✅ Optimal |
| **"Where is the bottleneck?"** | ⚠️ Limited | ⚠️ Manual | ✅ Optimal |
| **Cost Scale** | $ (Low) | $$$ (High) | $$ (Medium) |
| **Retention** | Years | Days/Weeks | Days |
| **Data Type** | Numbers (Floats) | Text (Strings) | Spans / IDs |

## The "Wrong Tool" Test

If you find yourself writing queries like `SELECT * FROM metrics WHERE error_message LIKE '%timeout%'`, you have used the wrong tool. **TSDBs are for numbers; Logging engines are for text.**
