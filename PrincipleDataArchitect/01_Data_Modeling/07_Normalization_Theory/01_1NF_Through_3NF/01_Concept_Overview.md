# 1NF Through 3NF — Concept Overview

> The foundation normalization forms that every data architect must internalize — not just know, but *feel* in their bones when looking at a schema.

---

## Why This Exists

**Origin**: Edgar F. Codd introduced normalization in 1970 at IBM Research. His goal was not elegance — it was **eliminating anomalies**. Update anomalies, insertion anomalies, and deletion anomalies are bugs in your schema that silently corrupt data over time.

**The problem it solves**: If a customer's city is stored in 50 order rows, and the customer moves, you must update 50 rows. If you update 49, you now have inconsistent data with no error thrown and no log entry. This is an **update anomaly** — the most insidious kind of bug because it's silent and cumulative.

**Principal-level nuance**: Normalization is a *design-time* tool, not a *deployment-time* mandate. You normalize to understand your data's dependencies, then selectively denormalize for performance. An architect who blindly normalizes everything produces an unusable 30-JOIN reporting schema. An architect who skips normalization produces a write-anomaly minefield.

## Mindmap

```mermaid
mindmap
  root((Normal Forms 1-3))
    1NF First Normal Form
      Atomic values
        No repeating groups
        No arrays in cells
        Each cell = one value
      Each row is unique
      Has a primary key
      Violation examples
        phone1, phone2, phone3 columns
        CSV in a single column
        JSON array inline
    2NF Second Normal Form
      Must be in 1NF
      No partial dependencies
        Every non-key column depends on ALL of PK
        Only matters for composite PKs
      Violation examples
        product_name depends only on product_id
        not on order_id + product_id composite
    3NF Third Normal Form
      Must be in 2NF
      No transitive dependencies
        Non-key depends only on PK
        Not on another non-key column
      Violation examples
        city depends on zip_code
        zip_code depends on customer_id
        city transitively depends on customer_id
    Anomalies Eliminated
      Update anomaly
        Change city in 50 rows vs 1
      Insertion anomaly
        Cant add a new city without an order
      Deletion anomaly
        Delete last order loses city info
```

## Key Terminology

| Term | Precise Definition |
|---|---|
| **Functional Dependency** | Column B is functionally dependent on column A if each value of A determines exactly one value of B (A → B) |
| **Partial Dependency** | A non-key column depends on only PART of a composite primary key (violates 2NF) |
| **Transitive Dependency** | A → B → C where C depends on A only through B (violates 3NF) |
| **Candidate Key** | A minimal set of columns that uniquely identifies a row |
| **Update Anomaly** | Inconsistency caused by updating a repeated value in some rows but not all |
| **Insertion Anomaly** | Inability to insert valid data because of missing unrelated data |
| **Deletion Anomaly** | Unintended loss of data when deleting a row that contains the only copy of some information |
