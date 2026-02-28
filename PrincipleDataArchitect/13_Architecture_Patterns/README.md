# 13 — Architecture Patterns

> "An architecture pattern is not a solution. It is a language for thinking about trade-offs."

A Principal doesn't blindly adopt Lambda Architecture because a blog post said so. They understand that each pattern solves specific problems and creates specific new ones. Mastery means knowing when to combine patterns, when to deviate, and when to invent something entirely new.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Lambda_Architecture/`

- **The Three Layers**: Batch layer (immutable master dataset, recomputed from scratch), Speed layer (real-time approximation), Serving layer (merged view). Nathan Marz's original design from Storm at Twitter.
- **The Operational Pain**: Maintaining two codebases (batch + streaming) that must produce identical results. The "dual compute" cost problem.
- **When Lambda is Still the Right Choice**: When regulatory requirements demand a recomputable batch layer as the source of truth, with streaming providing best-effort real-time.

### `02_Kappa_Architecture/`

- **Streaming as the Single Source of Truth**: Jay Kreps's simplification. One codebase, one processing engine (Kafka + Flink/Spark Streaming). Replay the stream to recompute.
- **The Replay Problem**: Reprocessing 2 years of Kafka data requires either infinite retention or archival to S3 + replay tooling. The cost implications of extended Kafka retention.
- **When Kappa Breaks**: Complex aggregations (e.g., "average revenue per customer per quarter over the last 3 years") that are trivial in SQL batch but extremely expensive in streaming state.

### `03_Data_Mesh_Architecture/`

- **The Four Principles**: Domain-oriented ownership, Data as a Product, Self-serve data platform, Federated computational governance. Zhamak Dehghani's 2019 thesis.
- **Organizational Prerequisites**: Data Mesh is primarily an organizational architecture, not a technology. It requires autonomous domain teams with data engineering skills — which most companies don't have.
- **The Central Platform's Role**: What the platform team provides: compute provisioning, cataloging, policy enforcement, CI/CD templates, monitoring. What it does NOT provide: schema design, business logic, quality definitions.

### `04_Data_Fabric_Architecture/`

- **Metadata-Driven Integration**: Using active metadata, knowledge graphs, and AI to automatically discover, integrate, and govern data across hybrid/multi-cloud environments.
- **Data Fabric vs. Data Mesh**: Mesh is organizational (who owns the data). Fabric is technological (how the data is integrated). They are complementary, not competing.
- **Vendor Landscape**: Informatica IDMC, Talend, Denodo, IBM Cloud Pak. The gap between vendor marketing and operational reality.

### `05_Event_Driven_And_Microservices_Data_Patterns/`

- **Database-per-Service**: Each microservice owns its database. No shared databases. The consequence: distributed queries become the application's problem.
- **API Composition**: Aggregating data from multiple services at the API gateway level. The N+1 query problem across microservices.
- **Event Choreography vs. Orchestration**: Choreography (services react to events independently) vs. Orchestration (a central coordinator directs the flow). Choreography scales better but is harder to debug.
- **The Strangler Fig Pattern**: Incrementally migrating from monolith to microservices by routing traffic to new services one endpoint at a time while the monolith slowly atrophies.

### `06_Reference_Architectures/`

- **Netflix Data Platform**: Keystone (real-time event pipeline), Metacat (federated catalog), Dataflow (batch ETL), Runway (ML platform). How they evolved from Hadoop to a Spark/Flink/Iceberg stack.
- **LinkedIn Data Platform**: Brooklin (streaming data delivery), Datahub (metadata catalog), Gobblin (data ingestion), Unified Metrics Platform.
- **Uber Data Platform**: Michelangelo (ML), AthenaX (streaming SQL), Hudi (incremental processing). How Uber processes 100+ PB across multiple data centers.
- **Airbnb Data Platform**: Minerva (metrics layer), Dataportal (catalog), Zipline (feature store), Airflow (orchestration — they invented it).

---
*Part of [Principal Data Architect Learning Path](../README.md)*
