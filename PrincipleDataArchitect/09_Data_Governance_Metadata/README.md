# 09 — Data Governance & Metadata

> "Governance is not a bureaucratic overlay; it is the immune system of the data platform. Without it, the organization slowly poisons itself with conflicting definitions, unknown data sources, and untraceable errors."

A Principal Architect designs governance that *accelerates* teams rather than slowing them down. The goal is self-serve data discovery with guardrails, not a ticket queue for data access.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Governance_Frameworks/`

- **DAMA-DMBOK 2.0**: The 11 knowledge areas of data management. Data Architecture, Data Modeling, Data Quality, Metadata, Data Security, Reference & Master Data, Data Warehousing, Data Integration, Document & Content, Data Storage & Operations, Data Governance.
- **DCAM (Data Management Capability Assessment Model)**: The maturity model used by regulators and financial institutions. The 8 components and 38 capabilities.
- **Data Stewardship Models**: Centralized (one governance team), Federated (domain stewards), Hybrid. How Netflix uses domain-level data ownership with platform guardrails.

### `02_Data_Catalog_And_Discovery/`

- **Modern Catalogs**: DataHub (LinkedIn open-source), Atlan, Collibra, Alation, Unity Catalog. Comparing push-based cataloging (metadata ingested from connectors) vs. pull-based (agents that crawl data sources).
- **Active Metadata**: Moving beyond passive catalogs. Using metadata to automatically trigger pipeline orchestration, data quality checks, and access requests.
- **Search and Discovery UX**: Why a data catalog is useless if nobody can find anything. Implementing relevance ranking, popularity signals, and collaborative annotations.

### `03_Data_Lineage/`

- **Column-Level Lineage**: Tracking not just "this table came from that table," but "column `revenue` in the gold table was derived from `price * quantity` in the silver table, which came from `orders.unit_price` and `orders.qty` in the bronze table."
- **OpenLineage Standard**: The open-source specification for lineage metadata. Integration with Airflow, Spark, dbt, and Flink.
- **Impact Analysis**: When someone asks, "If I change the data type of column X in the source system, what breaks?" — lineage provides the answer in seconds instead of days.

### `04_Data_Mesh_Architecture/`

- **Domain-Oriented Ownership**: Each business domain (Payments, Logistics, Marketing) owns its data products end-to-end, including quality, SLAs, and documentation.
- **Data as a Product**: Applying product thinking to data. Data products have customers, SLAs, versioning, deprecation policies, and discoverability.
- **Self-Serve Data Platform**: The central platform team provides infrastructure (compute, storage, CI/CD, governance tooling) as a product that domain teams consume.
- **Federated Computational Governance**: Global policies (PII classification, retention) enforced automatically via code, not committee meetings.

### `05_Data_Contracts/`

- **The Contract Specification**: Schema definition (fields, types, constraints), SLAs (freshness, completeness), ownership, and breaking change policies.
- **Contract Testing in CI/CD**: Running automated contract validation on every pull request. If a producer changes a field, the build fails before it reaches production.
- **The Organizational Challenge**: Getting 15 different engineering teams to agree on data contracts requires executive sponsorship, not just good tooling.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
