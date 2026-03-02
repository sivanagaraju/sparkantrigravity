# Valid Time vs Transaction Time — Pitfalls and Anti-Patterns

> Specific mistakes, detection methods, and remediation steps.

---

## Anti-Pattern 1: Conflating Valid Time and Transaction Time into One Column

**The mistake**: Using a single `effective_date` column to represent both "when this happened in reality" and "when the system recorded it."

```sql
-- ❌ WRONG: Single timeline
CREATE TABLE dim_customer (
    customer_sk     BIGSERIAL PRIMARY KEY,
    customer_id     INT NOT NULL,
    city            VARCHAR(200),
    effective_from  DATE NOT NULL,       -- Is this valid time? Transaction time? Both?
    effective_to    DATE DEFAULT '9999-12-31',
    is_current      BOOLEAN DEFAULT TRUE
);

-- When a correction comes in, you overwrite the row.
-- The previous state is gone.
```

**What breaks**: Late-arriving corrections cannot be distinguished from real-world changes. A customer who moved (valid time change) looks identical to a customer whose city was misentered (transaction time correction). Auditors cannot reproduce past reports.

**Detection**:

- Query: `SELECT COUNT(*) FROM dim_customer WHERE effective_from = load_date` — if most rows have `effective_from` = load timestamp, the column is acting as transaction time, not valid time
- Check: Can you answer "what did the March report show?" If not, you have no transaction time

**Fix**: Split into four columns: `valid_from`, `valid_to`, `txn_from`, `txn_to`. Migrate existing rows with `txn_from = effective_from, txn_to = 'infinity'`.

---

## Anti-Pattern 2: Mutating Transaction Time Rows (DELETE + INSERT Instead of Close + Insert)

**The mistake**: Physically deleting old versions and inserting corrected versions, destroying the audit trail.

```sql
-- ❌ WRONG: Destroying history
DELETE FROM trade_ledger_bitemporal 
WHERE trade_id = 'T-1001' AND txn_to = 'infinity';

INSERT INTO trade_ledger_bitemporal (trade_id, price, valid_from, txn_from, txn_to)
VALUES ('T-1001', 151.00, '2024-01-15', CURRENT_TIMESTAMP, 'infinity');
-- The original $150 record is GONE
```

**What breaks**: Transaction time is meant to be immutable. If you delete old versions, you cannot answer "what did the system believe at time T?" This violates the fundamental contract of bitemporal databases.

**Detection**:

- Check for DELETE statements on bitemporal tables in ETL code
- Monitor: `pg_stat_user_tables.n_tup_del` — if a "bitemporal" table has any deletes, something is wrong
- Audit: Row count should only ever increase for a bitemporal table

**Fix**: Replace DELETE with UPDATE to close `txn_to`:

```sql
-- ✅ CORRECT: Close, don't delete
UPDATE trade_ledger_bitemporal 
SET txn_to = CURRENT_TIMESTAMP
WHERE trade_id = 'T-1001' AND txn_to = 'infinity';

INSERT INTO trade_ledger_bitemporal (trade_id, price, valid_from, txn_from, txn_to)
VALUES ('T-1001', 151.00, '2024-01-15', CURRENT_TIMESTAMP, 'infinity');
```

---

## Anti-Pattern 3: No Temporal Indexes (Full Table Scans on Every As-Of Query)

**The mistake**: Creating a bitemporal table without specialized temporal indexes, then wondering why as-of queries take minutes.

```sql
-- ❌ Only a PK index exists
CREATE TABLE policy_bitemporal (
    policy_sk    BIGSERIAL PRIMARY KEY,
    policy_id    INT NOT NULL,
    ...
    valid_from   DATE,
    valid_to     DATE,
    txn_from     TIMESTAMP,
    txn_to       TIMESTAMP
);
-- No index on temporal columns → every as-of query scans the full table
```

**What breaks**: Bitemporal tables grow fast (every change creates a new row). A 10M-row base table with 5 changes per record over 3 years = 50M rows. As-of queries without indexes do a full 50M row scan.

**Detection**:

- `EXPLAIN ANALYZE` on an as-of query shows `Seq Scan` on the bitemporal table
- Query times for as-of queries > 10x current-state queries
- Dashboard shows increasing query latency over time (proportional to row growth)

**Fix**: Add composite and range indexes:

```sql
-- Composite B-tree for exact natural key + temporal range
CREATE INDEX idx_bt_lookup 
    ON policy_bitemporal(policy_id, valid_from, valid_to, txn_from, txn_to);

-- PostgreSQL: GiST range index for overlap queries
CREATE INDEX idx_bt_valid_range 
    ON policy_bitemporal USING GIST (daterange(valid_from, valid_to));

-- Partial index for current-state fast path
CREATE INDEX idx_bt_current 
    ON policy_bitemporal(policy_id) 
    WHERE valid_to = '9999-12-31' AND txn_to = '9999-12-31 23:59:59';
```

---

## Anti-Pattern 4: Using Bitemporal Where SCD Type 2 Is Sufficient

**The mistake**: Over-engineering. Implementing a full bitemporal model for a product dimension that changes twice a year and has no regulatory audit requirement.

**What breaks**: Nothing breaks technically — but:

- ETL complexity doubles (correction vs. real-change logic)
- Storage grows 2-4x
- Queries require temporal predicates that BI analysts don't understand
- Every developer touching the pipeline must understand bitemporal semantics

**Detection**:

- Ask: "Has anyone ever queried transaction time on this table?" If the answer is no after 6 months in production, you don't need it.
- Check: Is there a regulatory requirement to reproduce past reports?
- Check: Does data ever get corrected retroactively? If not, transaction time adds no value.

**Fix**: Downgrade to SCD Type 2 (valid time only). Keep the bitemporal infrastructure for tables that actually need it — trade data, financial positions, regulatory submissions.

---

## Anti-Pattern 5: Temporal Gaps and Overlaps in Valid Time Ranges

**The mistake**: ETL bugs that create gaps (no version covers a date) or overlaps (two versions claim to be valid on the same date) in the valid time range.

```sql
-- ❌ GAP: No version covers June 15-July 1
-- customer_id | city     | valid_from | valid_to
-- 1001        | Seattle  | 2024-01-01 | 2024-06-15
-- 1001        | Portland | 2024-07-01 | 9999-12-31
-- What was the city on June 20? No answer.

-- ❌ OVERLAP: Two versions claim June
-- customer_id | city     | valid_from | valid_to
-- 1001        | Seattle  | 2024-01-01 | 2024-07-01
-- 1001        | Portland | 2024-06-15 | 9999-12-31
-- What was the city on June 20? Two answers. Non-deterministic.
```

**Detection**:

```sql
-- Find gaps
SELECT a.customer_id, a.valid_to AS gap_start, b.valid_from AS gap_end
FROM dim_customer_bitemporal a
JOIN dim_customer_bitemporal b ON a.customer_id = b.customer_id
WHERE a.valid_to < b.valid_from
  AND a.txn_to = 'infinity' AND b.txn_to = 'infinity'
  AND NOT EXISTS (
    SELECT 1 FROM dim_customer_bitemporal c
    WHERE c.customer_id = a.customer_id
      AND c.valid_from <= a.valid_to AND c.valid_to >= b.valid_from
      AND c.txn_to = 'infinity'
  );

-- Find overlaps
SELECT a.customer_id, a.valid_from, a.valid_to, b.valid_from, b.valid_to
FROM dim_customer_bitemporal a
JOIN dim_customer_bitemporal b ON a.customer_id = b.customer_id
WHERE a.customer_sk < b.customer_sk
  AND a.valid_from < b.valid_to AND a.valid_to > b.valid_from
  AND a.txn_to = 'infinity' AND b.txn_to = 'infinity';
```

**Fix**: Use PostgreSQL `EXCLUDE USING GIST` constraints to prevent overlaps at the database level. Implement gap-detection in the ETL validation step before committing.

---

## Anti-Pattern 6: Not Materializing Current State for BI

**The mistake**: Forcing all consumers — including BI analysts dragging and dropping in Tableau — to write bitemporal temporal predicates for every query.

```sql
-- ❌ Analyst has to remember to add these filters EVERY TIME
SELECT customer_name, city 
FROM dim_customer_bitemporal
WHERE valid_to = '9999-12-31' 
  AND txn_to = '9999-12-31 23:59:59';
-- Analyst forgets the filter → gets 50M rows instead of 10M
```

**Fix**: Create a materialized view for current state:

```sql
CREATE MATERIALIZED VIEW dim_customer_current AS
SELECT * FROM dim_customer_bitemporal
WHERE valid_to = '9999-12-31' 
  AND txn_to = '9999-12-31 23:59:59';

-- BI tools point to this view. Bitemporal queries go to the base table.
-- Refresh on a schedule or trigger.
REFRESH MATERIALIZED VIEW CONCURRENTLY dim_customer_current;
```

---

## Decision Matrix — When Bitemporal Is the WRONG Choice

| Scenario | Why Bitemporal Is Wrong | Better Alternative |
|---|---|---|
| Sensor/IoT time-series data | Events don't get "corrected" — they're immutable measurements | Append-only time-series table |
| Product catalog with rare changes | No regulatory need, changes are infrequent | SCD Type 2 |
| Click-stream / web analytics | Events are immutable, high volume, no corrections | Append-only fact table |
| Config/settings changes | No business need for "what did the system believe" | SCD Type 1 (overwrite) |
| Real-time ML feature serving | Latency budget doesn't allow temporal JOIN logic | Pre-computed feature snapshots |
