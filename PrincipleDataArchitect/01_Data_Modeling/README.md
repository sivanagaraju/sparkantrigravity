# 01 — Data Modeling: The Architect's First Principles

> "Data outlives code. Code is rewritten every 5 years; data models persist for decades."

At the Principal level, data modeling is not about drawing boxes in ER Studio. It is about understanding the fundamental physics of the business domain, predicting how it will evolve over the next decade, and designing structures that can bend without breaking.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Logical_Domain_Modeling/`

- **Event Storming & Domain Driven Design**: Extracting the true ubiquitous language from business stakeholders who don't know what they want.
- **Bounded Contexts in Data**: Mapping DDD to Data Mesh. When should "User" in the Billing domain be physically separated from "User" in the Auth domain?
- **The Polymorphism Trap**: Why developers love polymorphic associations (EntityID, EntityType) and why data architects know they destroy query performance and referential integrity.

### `02_Dimensional_Modeling_Advanced/`

- **Beyond the Basics**: We skip Kimball 101. This focuses on degenerate dimensions, junk dimensions, and outrigger dimensions at petabyte scale.
- **SCD Extreme Cases**: Handling Type 6 and Type 7 Slowly Changing Dimensions when the source system is a chaotic microservice firing out-of-order events.
- **Factless Fact Tables & Accumulating Snapshots**: Modeling complex state machines (e.g., the lifecycle of an Amazon order from Cart → Placed → Shipped → Returned).

### `03_Data_Vault_2_0_Architecture/`

- **The Case for Data Vault**: Why highly acquisitive companies (M&A) or heavily regulated banks use Data Vault instead of Kimball.
- **Hubs, Links, and Satellites**: The philosophy of "100% of the data, 100% of the time" (no hard deletes, no updates).
- **Hash Keys vs Natural Keys**: Collision probabilities, MD5 vs SHA-256 for integration, and business vault vs raw vault.

### `04_Temporal_and_Bitemporal_Modeling/`

- **Valid Time vs. Transaction Time**: Modeling reality vs. modeling our *awareness* of reality. Critical for FinTech and Healthcare.
- **The "As-Of" Query Problem**: Designing schemas that allow a regulator to ask: "What did the risk model think the customer's balance was on Tuesday, based on the data we had on Monday?"

### `05_Graph_Data_Modeling/`

- **Property Graphs**: Modeling super-nodes in social networks (e.g., a celebrity with 10M followers) without crashing the database.
- **Fraud Detection Schemas**: Using graph traversals for synthetic identity rings or money laundering patterns.

### `06_NoSQL_and_Document_Modeling/`

- **Query-Driven Modeling**: Why NoSQL modeling is the exact reverse of RDBMS modeling. Modeling based on access patterns (e.g., DynamoDB Single-Table Design).
- **The "Embedding vs. Referencing" Math**: Calculating the exact payload size and read/write ratio to decide if a 1:N relationship should be a nested JSON array or a separate collection.
- **Handling Schema Evolution in Schema-less DBs**: The "Schema Version" attribute pattern and read-time migration strategies.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
