# Snapshot Fact Tables — Pitfalls and Anti-Patterns

> Specific mistakes, detection methods, and remediation steps.

---

## Anti-Pattern 1: Summing Semi-Additive Measures Across Time

**The mistake**: Treating snapshot balances as additive across the time dimension.

```sql
-- ❌ WRONG: Summing daily balances across a month
SELECT account_id, SUM(closing_balance) AS monthly_total
FROM fact_account_daily
WHERE snapshot_date BETWEEN '2024-03-01' AND '2024-03-31'
GROUP BY account_id;
-- Account with $10,000 balance shows $310,000 "monthly total"
-- This number is meaningless.
```

**What breaks**: Semi-additive measures (balance, level, count-on-hand) can be summed across non-time dimensions (across accounts, stores, products) but NOT across time. Summing a daily balance across 31 days produces garbage.

**Detection**:

- Search BI queries for `SUM(balance)` or `SUM(closing_balance)` grouped by month/quarter
- Check Tableau calculated fields for aggregation on balance-type measures
- Review dashboard definitions for "Total Balance" that aggregates across time periods

**Fix**: Use the correct aggregation:

```sql
-- ✅ Period-end balance: take the last day's value
SELECT account_id, closing_balance
FROM fact_account_daily
WHERE snapshot_date = '2024-03-31';

-- ✅ Average daily balance: use AVG
SELECT account_id, AVG(closing_balance) AS avg_daily_balance
FROM fact_account_daily
WHERE snapshot_date BETWEEN '2024-03-01' AND '2024-03-31'
GROUP BY account_id;
```

---

## Anti-Pattern 2: Sparse Snapshots Without Coalesce Logic

**The mistake**: Only creating snapshot rows for entities that had activity, then querying the snapshot without filling gaps.

```sql
-- Sparse snapshot: only active accounts get rows
-- Account 1001 had no transactions in March → no row in March
-- Account 1001 had activity in Feb (balance = $5,000) and April ($4,800)

SELECT closing_balance 
FROM fact_account_daily 
WHERE account_id = 1001 AND snapshot_date = '2024-03-15';
-- Returns: 0 rows. Not "balance was $5,000" — empty.
-- BI dashboard shows blank or zero instead of $5,000.
```

**What breaks**: Users expect to see the balance on any date. Sparse snapshots require `LAST_VALUE` / coalesce logic to fill forward from the last known snapshot. BI analysts won't write this — they'll report zeros.

**Detection**:

- Count rows per period. If row count varies significantly day-to-day (e.g., 8M on Monday, 200K on Saturday), snapshots are sparse
- Check for NULL/zero balances on dates with known account activity

**Fix**: Either use dense snapshots (recommended) or provide a fill-forward view:

```sql
-- Dense snapshot: create row for every active account every day
-- Even if no activity, carry forward previous balance

-- Or: Fill-forward view for sparse snapshots
CREATE VIEW v_account_balance_filled AS
SELECT 
    d.calendar_date,
    a.account_id,
    COALESCE(
        f.closing_balance,
        LAST_VALUE(f2.closing_balance) OVER (
            PARTITION BY a.account_id 
            ORDER BY d.calendar_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )
    ) AS closing_balance
FROM dim_date d
CROSS JOIN dim_account a
LEFT JOIN fact_account_daily f 
    ON d.date_sk = f.date_sk AND a.account_sk = f.account_sk;
```

---

## Anti-Pattern 3: No Reconciliation Between Snapshots and Transactions

**The mistake**: Building a snapshot pipeline without verifying that the snapshot closing balance equals the sum of all transactions.

**What breaks**: Silent data quality issues accumulate over months. A rounding error in the daily snapshot calculation compounds: $0.01/day × 365 days × 100M accounts = $365M discrepancy.

**Detection**:

```sql
-- Reconciliation query: compare snapshot closing to transaction SUM
WITH snap AS (
    SELECT account_id, closing_balance
    FROM fact_account_daily
    WHERE snapshot_date = '2024-03-31'
),
txn_sum AS (
    SELECT account_id, 
           SUM(CASE WHEN txn_type = 'CREDIT' THEN amount ELSE -amount END) AS computed_balance
    FROM fact_transactions
    WHERE txn_date <= '2024-03-31'
    GROUP BY account_id
)
SELECT s.account_id, s.closing_balance, t.computed_balance,
       ABS(s.closing_balance - t.computed_balance) AS diff
FROM snap s
JOIN txn_sum t ON s.account_id = t.account_id
WHERE ABS(s.closing_balance - t.computed_balance) > 0.01
ORDER BY diff DESC;
```

**Fix**: Add reconciliation as a post-snapshot quality gate. If total discrepancy exceeds threshold, alert and block downstream consumers.

---

## Anti-Pattern 4: Using is_current for Snapshot Generation

**The mistake**: Joining to `dim_account WHERE is_current = TRUE` when generating snapshots, which misses accounts that were closed or changed during the snapshot day.

```sql
-- ❌ WRONG: is_current = TRUE misses accounts closed today
SELECT a.account_sk, a.account_id, ...
FROM dim_account a
WHERE a.is_current = TRUE;  -- Accounts closed at 5 PM are already FALSE by 6 PM
```

**What breaks**: Accounts closed on the snapshot day are excluded. The snapshot doesn't capture their final balance, creating reconciliation gaps.

**Fix**: Use temporal predicates:

```sql
-- ✅ CORRECT: Get accounts that were active at any point on snapshot day
SELECT a.account_sk, a.account_id, ...
FROM dim_account a
WHERE a.effective_from <= '2024-03-31'
  AND a.effective_to > '2024-03-31';
```

---

## Anti-Pattern 5: Overwriting Snapshots (Not Append-Only)

**The mistake**: Re-running the snapshot job and overwriting previous results instead of appending.

**What breaks**: If the snapshot generation SQL has a bug that's discovered 2 weeks later, you've lost the original snapshots. Rolling back requires re-running the job with corrected logic against historical transactions — expensive and error-prone.

**Fix**: Snapshots should be append-only. If a regeneration is needed, mark the old snapshot as superseded (not deleted) and insert the corrected snapshot with a new version.

```sql
-- Add a version column to the snapshot table
ALTER TABLE fact_account_daily ADD COLUMN snapshot_version INT DEFAULT 1;

-- On regeneration, increment version; old version stays for audit
INSERT INTO fact_account_daily (..., snapshot_version)
SELECT ..., 2 AS snapshot_version
FROM ... ;

-- Current-state queries filter to latest version
CREATE VIEW v_account_daily_current AS
SELECT * FROM fact_account_daily f
WHERE snapshot_version = (
    SELECT MAX(snapshot_version) 
    FROM fact_account_daily f2 
    WHERE f2.account_sk = f.account_sk 
      AND f2.date_sk = f.date_sk
);
```

---

## Decision Matrix — When Snapshots Are the WRONG Choice

| Scenario | Why Snapshots Are Wrong | Better Alternative |
|---|---|---|
| High-frequency event analysis (sub-second) | Event timestamps are the natural grain — snapshots lose precision | Transaction fact table |
| Real-time balance (must reflect latest txn) | Snapshots are batch — stale within minutes of generation | Materialized view with trigger-based refresh |
| Process with no defined lifecycle milestones | Accumulating snapshot requires known milestones | Transaction fact + status dimension |
| Small data volume (<1M rows total) | Aggregation at query time is fast enough; snapshots add overhead | Direct query on transaction fact |
| Rapidly changing state (thousands of changes/second) | Snapshot would be near-continuous — defeats the purpose | Event-sourced model or streaming aggregation |
