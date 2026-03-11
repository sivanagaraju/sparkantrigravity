# 5NF and 6NF — Concept Overview & Deep Internals

> The exotic normal forms: join dependencies and temporal decomposition.

---

## Why This Exists

**5NF (Fifth Normal Form / Project-Join Normal Form)**: Addresses cases where a table can be decomposed into three or more smaller tables and reconstructed by joining them — but NOT into just two tables. This is rare in practice but occurs with ternary relationships.

**6NF (Sixth Normal Form)**: Each relation contains a candidate key + at most one other attribute. This is extreme decomposition — primarily useful for temporal data and Data Vault Satellites. Every attribute change creates a new row in its own table.

## When 5NF/6NF Matter

| Normal Form | Practical Use | Where You'll See It |
|---|---|---|
| **5NF** | Rare. Only when ternary relationships have join dependencies | Academic exercises, some scheduling systems |
| **6NF** | Temporal databases where each attribute changes independently | Data Vault Satellites, temporal DW |

## 5NF Example — Ternary Relationship

```sql
-- A supplier can supply certain parts to certain projects
-- But NOT all combinations are valid
-- This is a ternary relationship that CANNOT be decomposed into three binary relationships

CREATE TABLE supplier_part_project (
    supplier_id   INT,
    part_id       INT,
    project_id    INT,
    PRIMARY KEY (supplier_id, part_id, project_id)
);

-- If the constraint is: "if supplier S supplies part P, and supplier S supplies to project J,
-- and part P is used in project J, then supplier S supplies part P to project J"
-- THEN it CAN be decomposed into 5NF:

CREATE TABLE supplier_part (supplier_id INT, part_id INT, PRIMARY KEY(supplier_id, part_id));
CREATE TABLE supplier_project (supplier_id INT, project_id INT, PRIMARY KEY(supplier_id, project_id));
CREATE TABLE part_project (part_id INT, project_id INT, PRIMARY KEY(part_id, project_id));

-- The original table = natural join of all three
-- This is 5NF: no remaining join dependencies
```

## 6NF — Data Vault Connection

```sql
-- 6NF: each attribute in its own satellite (Data Vault style)
-- Instead of one wide customer table, decompose to maximum granularity

CREATE TABLE sat_customer_name (
    customer_hk  BINARY(16),
    load_ts      TIMESTAMPTZ,
    customer_name VARCHAR(300),
    PRIMARY KEY (customer_hk, load_ts)
);

CREATE TABLE sat_customer_email (
    customer_hk  BINARY(16),
    load_ts      TIMESTAMPTZ,
    email        VARCHAR(255),
    PRIMARY KEY (customer_hk, load_ts)
);

CREATE TABLE sat_customer_city (
    customer_hk  BINARY(16),
    load_ts      TIMESTAMPTZ,
    city         VARCHAR(200),
    PRIMARY KEY (customer_hk, load_ts)
);

-- BENEFIT: name changes don't create new city rows and vice versa
-- COST: query requires joining 3 tables to get a full customer record
```

## Interview — Q: "Have you ever used 5NF or 6NF in practice?"

**Strong Answer**: "5NF is academic — I've seen it in scheduling systems with ternary constraints, but it's rare. 6NF is practical in Data Vault architectures: each Satellite decomposed to one attribute per table. The benefit is that independent attribute changes don't pollute each other's history. I applied this at scale when customer name changes 10x more frequently than customer address — separate Satellites prevented unnecessary SCD2 row explosion."

## References

| Resource | Link |
|---|---|
| *An Introduction to Database Systems* | C.J. Date — Ch. 13-14 |
| *Temporal Data & The Relational Model* | Date, Darwen, Lorentzos |
| Cross-ref: Data Vault Satellites | [../../03_Data_Vault_2_0_Architecture/02_Hubs_Links_Satellites](../../03_Data_Vault_2_0_Architecture/02_Hubs_Links_Satellites/) |
