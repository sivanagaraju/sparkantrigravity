# Bounded Contexts — Common Pitfalls & Anti-Patterns

> The top mistakes, why they are dangerous, and how to detect and fix them.

---

## ❌ Pitfall 1: One Giant Bounded Context

### What Happens

Everything is in one context: orders, payments, shipping, returns, reviews — one database, one schema, one team responsible for everything.

### Why It's Dangerous

You've built a data monolith. Every schema change requires coordinating with every consumer. A migration that touches `orders.status` breaks 15 downstream dashboards, 3 ML pipelines, and 2 regulatory reports.

### Detection

```sql
-- Count distinct "owners" querying the same table
-- If > 3 teams, the table spans multiple BCs
SELECT 
    query_user,
    COUNT(DISTINCT query_text) AS queries_count
FROM snowflake.account_usage.query_history
WHERE query_text ILIKE '%orders%'
GROUP BY query_user
ORDER BY queries_count DESC;
```

If 5+ different teams query the same table for fundamentally different purposes, it spans multiple BCs.

### Fix

Run Event Storming. Identify pivot events where ownership changes. Split the table along those boundaries.

---

## ❌ Pitfall 2: Bounded Contexts Too Granular

### What Happens

Every micro-feature gets its own BC: `CartAddition BC`, `CartRemoval BC`, `CartQuantityUpdate BC`. You end up with 50 BCs for a 10-person team.

### Why It's Dangerous

Distributed systems overhead without distributed systems benefits. Cross-BC queries become the norm, not the exception. Every simple report requires joining 10+ databases.

### Detection

- If a single user request requires synchronous calls to 5+ BCs, you've over-decomposed
- If your context map has more edges than nodes, something is wrong

### Fix

A good heuristic: **one BC per team** (±1). If you have 8 engineers, you probably need 3-5 BCs, not 30.

---

## ❌ Pitfall 3: No Context Map

### What Happens

Teams create BCs independently without documenting how they relate to each other. Nobody knows which BC is upstream. Nobody knows where Customer data comes from.

### Why It's Dangerous

Without a context map, integration is ad-hoc. Team A calls Team B's internal API. Team C reads Team D's database directly. No ACLs, no published language, no versioning. When Team D changes their schema, Team C's pipeline breaks silently.

### Fix

Draw a context map (see the How_It_Works file for examples). Review it quarterly. Mandate it in your data governance process.

---

## ❌ Pitfall 4: Shared Database Between BCs

### What Happens

Two BCs use the same database for "efficiency." The Payments team reads directly from the Orders team's tables.

### Why It's Dangerous

It creates invisible coupling. The Orders team can't change their schema without breaking the Payments team. This is the exact problem BCs are designed to prevent.

### Detection

```sql
-- Check for cross-schema queries (PostgreSQL)
SELECT schemaname, tablename, query_user
FROM pg_stat_user_tables
CROSS JOIN pg_stat_statements
WHERE query ILIKE '%payments%' AND schemaname = 'order_mgmt'
LIMIT 20;
```

### Fix

Each BC gets its own database or schema. Cross-BC data flows through Kafka/CDC or published APIs.

---

## ❌ Pitfall 5: Ignoring Cross-BC Analytics

### What Happens

Each BC owns its data perfectly. But nobody planned how the Data Warehouse would join them together. Analytics queries require 5-way JOINs across 5 different databases with no common keys.

### Why It's Dangerous

The CEO asks "How many orders were shipped within 24 hours?" — and nobody can answer because `order_id` in Order Management BC has no relationship to `shipment_id` in Fulfillment BC.

### Fix

Design **conformed dimensions** from Day 1. Every BC must include a shared business key (e.g., `order_id`) in its events/tables, even though it doesn't have a foreign key relationship. The DW uses this business key to build the unified view.

---

## Decision Matrix: When BCs Are The Wrong Tool

| Scenario | BC Appropriate? | Alternative |
|---|---|---|
| Small team (< 5 engineers), simple domain | ❌ | Single schema is fine, don't over-engineer |
| POC or prototype | ❌ | Move fast, refactor later |
| Read-only analytics workload | ⚠️ Maybe | BCs are for operational systems; the DW can be monolithic |
| Regulatory requirement for data isolation | ✅ | BCs enforce physical separation |
