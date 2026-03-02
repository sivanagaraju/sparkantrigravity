# Degenerate & Outrigger Dimensions — Pitfalls & Anti-Patterns

> The top mistakes, detection, and remediation.

---

## ❌ Pitfall 1: Creating a 1:1 Dimension Table for Transaction IDs

### What Happens

```sql
-- ANTI-PATTERN: a dimension table with one row per fact row
CREATE TABLE dim_order (
    order_sk    BIGINT PRIMARY KEY,
    order_number VARCHAR(30)
);
-- This table has EXACTLY the same number of rows as the fact table
-- It adds a JOIN but provides zero analytical value
```

### Fix

Make `order_number` a degenerate dimension — a column directly in the fact table. No separate table. No JOIN.

---

## ❌ Pitfall 2: Too Many Degenerate Dims Bloating the Fact Table

### What Happens

The architect adds 8 identifier columns to the fact table: `order_number`, `invoice_number`, `receipt_id`, `session_id`, `trace_id`, `request_id`, `confirmation_code`, `batch_id`.

### Why It's Dangerous

Each VARCHAR(50) degenerate dim adds ~50 bytes per row. At 1B rows/year, that's 50 GB × 8 = 400 GB of storage for columns that are rarely queried.

### Detection

```sql
-- Check which degenerate dims are actually queried
SELECT column_name, COUNT(*) AS query_count
FROM query_history_parsed  -- parse your query log
WHERE table_name = 'fact_sales'
  AND column_name IN ('order_number','invoice_number','receipt_id',
                       'session_id','trace_id','request_id',
                       'confirmation_code','batch_id')
GROUP BY column_name
ORDER BY query_count DESC;
```

### Fix

Keep only the 2-3 degenerate dims that analysts actually use. Move the rest to a separate `fact_audit_trail` table.

---

## ❌ Pitfall 3: Outrigger with SCD Type 2 Temporal Mismatch

### What Happens

`dim_product.brand_sk` points to `dim_brand`. Both are SCD Type 2. A product was created in 2023 when the brand was "Nike, Inc." In 2024, Nike updates its parent_company. The product still points to the 2023 brand_sk — it doesn't know about the 2024 version.

### Why It's Dangerous

A query for "current brand info" returns stale 2023 data for products that haven't changed since then.

### Fix

Two approaches:

1. **Point-in-time join**: Always join with `WHERE b.is_current = TRUE` — ignores the FK and uses the brand's natural key + current flag
2. **Cascade update**: When brand changes, update all product brand_sk values to the new brand_sk version (simpler but more ETL work)

---

## ❌ Pitfall 4: Using Outriggers When Denormalization Is Better

### What Happens

Creating `dim_brand` (5K rows) as an outrigger when brand has only 3 attributes: `brand_name`, `brand_country`, `parent_company`.

### Why It's Dangerous

An extra JOIN for 3 columns that could have been denormalized into `dim_product`. The JOIN overhead exceeds the storage savings.

### Rule of Thumb

- Outrigger has < 5 columns → denormalize instead
- Outrigger has > 10 columns or its own SCD lifecycle → outrigger is justified
- Outrigger is queried independently (e.g., "show all brands by country") → outrigger is justified

---

## Decision Matrix

| Factor | Use Degenerate Dim | Use Regular Dim | Use Outrigger | Use Junk Dim |
|---|---|---|---|---|
| High cardinality, no descriptions | ✅ | | | |
| Low cardinality, rich descriptions | | ✅ | | |
| Dimension of a dimension, own SCD | | | ✅ | |
| Low cardinality boolean flags | | | | ✅ |
| Unique transaction identifier | ✅ | | | |
| Hierarchical attribute (geo, org) | | | ✅ | |
