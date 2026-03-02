# SCD Extreme Cases — Hands-On, War Stories, Pitfalls, Interview, Further Reading

> Combined file covering practical examples, real-world scenarios, anti-patterns, interview prep, and references.

---

## Hands-On: Type 4 Mini-Dimension in dbt

```sql
-- models/marts/dim_customer_profile.sql
-- Build the mini-dimension from distinct combinations in source data

WITH distinct_profiles AS (
    SELECT DISTINCT
        CASE 
            WHEN credit_score >= 800 THEN 'A'
            WHEN credit_score >= 700 THEN 'B'
            WHEN credit_score >= 600 THEN 'C'
            WHEN credit_score >= 500 THEN 'D'
            ELSE 'F'
        END AS credit_score_band,
        risk_tier,
        loyalty_level,
        CASE 
            WHEN annual_income < 50000 THEN '0-50K'
            WHEN annual_income < 100000 THEN '50K-100K'
            ELSE '100K+'
        END AS income_band
    FROM {{ ref('stg_customers') }}
)

SELECT 
    {{ dbt_utils.generate_surrogate_key(['credit_score_band','risk_tier','loyalty_level','income_band']) }} AS profile_sk,
    *
FROM distinct_profiles
```

## Hands-On: Type 6 ETL in SQL

```sql
-- Step 1: Detect changed customers
WITH changes AS (
    SELECT s.customer_id, s.city AS new_city, d.city_historical AS old_city
    FROM staging.customers s
    JOIN dim_customer_type6 d ON s.customer_id = d.customer_id AND d.is_current = TRUE
    WHERE s.city != d.city_historical
)

-- Step 2: Close old rows
UPDATE dim_customer_type6 d
SET effective_to = CURRENT_DATE - 1, is_current = FALSE
FROM changes c WHERE d.customer_id = c.customer_id AND d.is_current = TRUE;

-- Step 3: Insert new version (Type 2 row)
INSERT INTO dim_customer_type6 (customer_id, customer_name, city_historical, city_current, city_previous, effective_from, is_current)
SELECT c.customer_id, d.customer_name, c.new_city, c.new_city, c.old_city, CURRENT_DATE, TRUE
FROM changes c
JOIN dim_customer_type6 d ON c.customer_id = d.customer_id AND d.effective_to = CURRENT_DATE - 1;

-- Step 4: Overwrite current city on ALL historical rows (Type 1 update)
UPDATE dim_customer_type6 d
SET city_current = c.new_city, city_previous = c.old_city
FROM changes c WHERE d.customer_id = c.customer_id;
```

---

## FAANG War Stories

### Amazon: Type 4 for Customer Behavioral Segments

Amazon's customer dimension uses a mini-dimension for behavioral segments (`frequent_buyer`, `prime_status`, `browsing_intensity`, `purchase_recency_band`). These change monthly based on ML scoring. Without Type 4, the 500M-row dim_customer would add 6B rows/year from monthly SCD2 versioning.

### Netflix: Type 6 for Content Region Availability

Netflix content licensing changes frequently by region. They use Type 6 so analysts can query both: "which regions was this title available in when this view happened?" (historical) AND "which regions is the title currently available in?" (current) — without a second query.

### Uber: Type 7 for Driver Ratings

Uber's driver dimension uses Type 7 (dual FK). The fact table has both `driver_sk` (historical rating at ride time) and `driver_id` (join to current rating). This lets the safety team compare "driver rating then" vs "driver rating now" in a single query.

---

## Pitfalls

| Pitfall | Danger | Fix |
|---|---|---|
| Using Type 2 for rapidly changing attributes | SCD2 explosion: 100M customers × 12 changes/year = 1.2B rows/year | Use Type 4 (mini-dimension) |
| Type 6 without updating ALL historical rows | `city_current` is stale on old rows → incorrect "current" analysis | Ensure the Type 1 overwrite step touches ALL rows for that customer_id |
| Type 7 without index on natural key | `JOIN ON customer_id AND is_current = TRUE` does full scan on large dim | Create partial index: `CREATE INDEX idx_current ON dim_customer(customer_id) WHERE is_current = TRUE` |
| Mixing SCD types without documentation | Nobody knows which columns are Type 1 vs Type 2 | Document SCD type per column in data dictionary |

---

## Interview Questions

### Q: "Customer attributes change monthly. How do you handle SCD?"

**Strong Answer**: "Type 4 Mini-Dimension. Split rapidly changing attributes into a small, separate dimension. The fact table has two FKs: one to the stable `dim_customer`, one to the `dim_customer_profile` mini-dim. The mini-dim has only ~200 rows (all combinations of banded attributes), so it never grows with SCD2. This prevents the main customer dimension from growing 12x per year."

### Q: "An analyst needs both historical AND current customer city in the same query. How?"

**Strong Answer**: "Type 6 Hybrid. Each SCD2 row carries a `city_historical` column (the value at that point in time) AND a `city_current` column (overwritten to the latest value on ALL rows). The analyst can use `city_historical` for point-in-time analysis and `city_current` for current-state reporting — in the same SELECT statement, no self-join needed."

---

## Further Reading

| Resource | Link |
|---|---|
| *The Data Warehouse Toolkit* 3rd Ed. | Kimball & Ross — Ch. 5: SCD techniques |
| Kimball Group Design Tip #152 | [SCD Mini-Dimensions](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/) |
| [dbt-labs/dbt-utils SCD macro](https://github.com/dbt-labs/dbt-utils) | `snapshot` strategy for SCD2 in dbt |
| [DataEngineer-io/data-engineer-handbook](https://github.com/DataEngineer-io/data-engineer-handbook) | Data engineering resources |

### Cross-References

- Degenerate & Outrigger → [../01_Degenerate_Outrigger](../01_Degenerate_Outrigger/) — outriggers interact with SCD temporal alignment
- Conformed Dimensions → [../04_Conformed_Dimensions](../04_Conformed_Dimensions/) — conformed dims need consistent SCD strategy across fact tables
