# 07 — Data Integration & APIs

> "The average Fortune 500 company has 900+ applications. A Principal Architect's real job is making them all talk to each other without creating spaghetti."

Data integration is the unglamorous, mission-critical work that determines whether a company's data platform is a cohesive asset or a fragmented liability. You must master every integration pattern and know which one to deploy based on latency requirements, data volume, and organizational maturity.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Integration_Patterns/`

- **Point-to-Point**: Direct connections between systems. Works for 3 systems, becomes O(n²) chaos at 30 systems. Why it's the default choice and why it always fails at scale.
- **Hub-and-Spoke (ESB)**: Centralized integration bus. MuleSoft, Informatica, TIBCO. The operational bottleneck of a single integration team gatekeeping all connections.
- **Publish-Subscribe**: Kafka/EventBridge as the universal backbone. Producers don't know (or care) who the consumers are. The scaling advantages and the schema contract challenges.
- **API-Led Connectivity**: System APIs → Process APIs → Experience APIs. MuleSoft's 3-tier API pattern. Building reusable integration layers.

### `02_Data_Virtualization/`

- **Query Federation**: Trino/Presto, Dremio, Denodo — querying data where it lives without copying it. The latency reality: federated queries across S3 + PostgreSQL + Snowflake will never match a pre-materialized table.
- **When Virtualization Wins**: Exploratory analytics, data discovery, and environments where data movement is blocked by compliance (e.g., EU health data cannot be copied).
- **When Virtualization Fails**: Sub-second dashboards, high-concurrency reporting, and any scenario requiring SLA guarantees on query latency.

### `03_Schema_Management_And_Evolution/`

- **Schema Registry (Confluent, AWS Glue)**: Centralized schema store for Kafka topics. Compatibility enforcement: what happens when a producer adds a required field that 15 downstream consumers don't know about?
- **Schema Evolution Rules**: BACKWARD (new schema can read old data), FORWARD (old schema can read new data), FULL (both). Why FULL compatibility is the only safe choice for production Kafka topics.
- **Data Contracts**: Explicit, versioned agreements between data producers and consumers. Defining SLAs for schema stability, freshness, and completeness. Andrew Jones's "Data Contracts" movement.

### `04_API_Design_For_Data_Products/`

- **REST vs. GraphQL vs. gRPC for Data**: REST for simple CRUD data access. GraphQL for flexible client-driven queries (avoiding over-fetching). gRPC for high-performance internal service-to-service data transfer.
- **Pagination Patterns**: Offset-based (simple, breaks under concurrent writes) vs. Cursor-based (stable, complex). Keyset pagination for large datasets.
- **Rate Limiting and Throttling**: Protecting your data APIs from a rogue consumer that sends 10,000 requests/second and DoS-es your database.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
