# As-Of Queries — Pitfalls and Anti-Patterns

> Specific mistakes, detection methods, and remediation steps.

---

## Anti-Pattern 1: Naive JOIN Instead of Point-in-Time JOIN (ML Data Leakage)

**The mistake**: Joining training events to the *current* feature values instead of the values that were valid at each event's timestamp.

```python
# ❌ WRONG: Naive join uses current feature state for all events
training_df = events_df.join(
    current_features_df,  # This is today's feature values
    on="customer_id",
    how="left"
)
# An event from January 2024 gets December 2024 features.
# The model trains on "future" data → data leakage.
```

**What breaks**: Inflated offline metrics (10-20% higher AUC/precision than reality). Model performance drops immediately in production because it no longer has access to future information.

**Detection**:

- Compare offline evaluation metrics to online A/B test metrics. Gap >5% = probable data leakage
- Check if the feature table has temporal columns (`valid_from`, `valid_to`). If it does and the join doesn't use them, it's a naive join
- Profile: `MAX(feature_update_date) - MAX(event_date)` — if feature dates are consistently newer than event dates, the join is leaking

**Fix**: Use point-in-time correct as-of joins:

```python
# ✅ CORRECT: Each event gets features valid AT THAT TIME
training_df = events_df.join(
    features_df,
    on=[
        events_df.customer_id == features_df.customer_id,
        events_df.event_ts >= features_df.valid_from,
        events_df.event_ts < features_df.valid_to
    ],
    how="left"
)
```

---

## Anti-Pattern 2: Delta Lake Time Travel as a Substitute for Bitemporal Modeling

**The mistake**: Assuming Delta Lake's time travel (transaction-time snapshots via the `_delta_log`) eliminates the need for valid-time modeling.

**What breaks**: Delta Lake time travel gives you transaction-time as-of queries for free. But it does NOT handle:

1. **Late-arriving data**: A record that arrives today with `valid_from = last_month` will appear in the current Delta version but not in the version from last month
2. **Valid-time queries**: "What address was valid on June 15?" requires `valid_from/valid_to` columns in your schema — Delta time travel can't infer this from commit timestamps
3. **Correction tracking**: Delta time travel shows commit-level snapshots, not row-level corrections. A correction to one row changes the entire table version.

**Detection**:

- Ask: "Can you query what was valid on date X (not when it was committed)?" If the answer involves Delta `TIMESTAMP AS OF`, the team is conflating transaction time with valid time.
- Check: Does the schema have `valid_from/valid_to` columns? If not, there's no valid-time modeling.

**Fix**: Use Delta Lake time travel for transaction time AND add explicit valid-time columns to the schema. Both are needed for bitemporal capability.

---

## Anti-Pattern 3: Unbounded Time Travel Retention (Storage Explosion)

**The mistake**: Enabling time travel with no retention policy. Delta Lake keeps all historical versions indefinitely if not configured otherwise.

```python
# ❌ WRONG: No vacuum, no retention configuration
spark.sql("CREATE TABLE positions USING DELTA LOCATION '/data/positions'")
# After 2 years: 500TB of historical files, 95% of which are never queried
```

**What breaks**: Storage costs grow linearly (or worse) with time. A 10TB table with daily updates generates ~3.6PB of history over 1 year without compaction.

**Detection**:

- `DESCRIBE HISTORY delta.\`/data/positions\`` — check how many versions exist
- Compare total physical storage to current logical table size. Ratio >5:1 suggests no vacuum
- Check for `delta.logRetentionDuration` and `delta.deletedFileRetentionDuration` settings

**Fix**: Set retention policies based on business needs:

```python
# Set retention to 90 days (covers quarterly reporting cycles)
spark.sql("""
    ALTER TABLE delta.`/data/positions`
    SET TBLPROPERTIES (
        'delta.logRetentionDuration' = 'interval 90 days',
        'delta.deletedFileRetentionDuration' = 'interval 90 days'
    )
""")

# Vacuum old files (run weekly via Airflow/scheduler)
spark.sql("VACUUM delta.`/data/positions` RETAIN 90 HOURS")

# For dates beyond 90 days, pre-materialize key snapshots
# (month-end, quarter-end) to S3 as Parquet files
```

---

## Anti-Pattern 4: As-Of Queries Without Temporal Indexes (Full Scan Every Time)

**The mistake**: Running as-of queries on bitemporal tables with only a primary key index. Every as-of query degrades to a full table scan.

```sql
-- Table has 500M rows, only PK index
-- This query scans ALL 500M rows to find the ~10M current on March 15
SELECT * FROM position_bitemporal
WHERE valid_from <= '2024-03-15' 
  AND valid_to > '2024-03-15'
  AND txn_from <= '2024-03-15 18:00:00'
  AND txn_to > '2024-03-15 18:00:00';
-- Execution time: 45 seconds. Unacceptable.
```

**Detection**:

- `EXPLAIN ANALYZE` shows `Seq Scan` with estimated rows = table size
- As-of query latency grows proportionally with table size
- CPU spikes when multiple analysts run as-of queries simultaneously

**Fix**: Layered indexing strategy:

```sql
-- 1. Composite index for natural key + temporal lookup
CREATE INDEX idx_pos_asof 
    ON position_bitemporal(account_id, instrument_id, valid_from, txn_from);

-- 2. GiST range indexes (PostgreSQL)
CREATE INDEX idx_pos_valid_gist 
    ON position_bitemporal USING GIST (daterange(valid_from, valid_to));
CREATE INDEX idx_pos_txn_gist 
    ON position_bitemporal USING GIST (tstzrange(txn_from, txn_to));

-- 3. Partial index for current state (most common query)
CREATE INDEX idx_pos_current 
    ON position_bitemporal(account_id, instrument_id) 
    WHERE valid_to = '9999-12-31' AND txn_to = '9999-12-31 23:59:59';
```

---

## Anti-Pattern 5: Exposing Raw Bitemporal Tables to BI Users

**The mistake**: Giving Tableau/Power BI users direct access to bitemporal tables with 500M rows and expecting them to add temporal predicates.

**What breaks**:

- Analysts forget the temporal filter → get 50M rows instead of 5M → dashboards crash
- Analysts misunderstand valid time vs transaction time → wrong data in reports
- Performance degrades because BI tools generate suboptimal queries against temporal tables

**Detection**:

- Check Tableau/Power BI query logs for queries missing `valid_to` or `txn_to` predicates
- Look for BI reports with suspiciously high row counts
- User complaints about slow dashboards

**Fix**: Create abstraction layers:

```sql
-- 1. Current-state view for everyday BI
CREATE MATERIALIZED VIEW mv_positions_current AS
SELECT account_id, instrument_id, quantity, market_value
FROM position_bitemporal
WHERE valid_to = '9999-12-31' AND txn_to = '9999-12-31 23:59:59';

-- 2. End-of-month snapshot view for period reports
CREATE MATERIALIZED VIEW mv_positions_eom AS
SELECT snapshot_month, account_id, instrument_id, quantity, market_value
FROM position_monthly_snapshot;

-- BI tools connect to these views. Raw bitemporal table is for engineers only.
```

---

## Anti-Pattern 6: Not Testing As-Of Query Correctness

**The mistake**: Building as-of query infrastructure without a test that verifies the results match a known baseline.

**What breaks**: Subtle bugs in temporal predicates (off-by-one on `<=` vs `<`, timezone mismatches, missing `infinity` sentinel handling) produce silently wrong results. You discover the error months later when an auditor finds a discrepancy.

**Detection**:

- Ask: "Is there a reconciliation test that compares as-of(yesterday) to a known baseline?"
- Check: Are there timezone conversions in the temporal columns? If `valid_from` is a `DATE` but `txn_from` is `TIMESTAMPTZ`, mixed timezone/date comparisons can cause off-by-one errors

**Fix**: Build automated reconciliation tests:

```python
# Daily reconciliation: compare as-of(yesterday_eod) to the 
# known snapshot taken at yesterday's EOD
def test_asof_correctness():
    eod_snapshot = load_snapshot("2024-03-14")  # known baseline
    asof_result = query_asof("2024-03-14 23:59:59")
    
    diff = eod_snapshot.exceptAll(asof_result)
    assert diff.count() == 0, f"As-of query differs from snapshot: {diff.count()} rows"
```

---

## Decision Matrix — When As-Of Queries Are the WRONG Choice

| Scenario | Why As-Of Is Wrong | Better Alternative |
|---|---|---|
| Real-time dashboard (current state only) | As-of adds latency and complexity for no benefit | Direct query on current-state table |
| Append-only event log (IoT, clickstream) | Events are immutable — no corrections, no valid-time changes | Time-range filter on event_timestamp |
| Config/feature flags (current state only) | Config is either on or off right now | Key-value store with current state |
| High-frequency analytics (<10ms latency) | Temporal joins too expensive for real-time | Pre-materialized feature vectors |
