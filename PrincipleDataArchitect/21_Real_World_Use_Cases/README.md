# 21 — Real World Use Cases

> "Theory without application is academic exercise. These use cases are where every domain comes together — modeling, pipelines, security, performance, cost — into a single coherent architecture."

Each use case in this domain is a full Principal-level system design exercise. They combine data modeling, pipeline architecture, security, performance, cost optimization, and organizational design into end-to-end solutions modeled on real FAANG-scale problems.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_E_Commerce_Data_Platform/` (Amazon-style)

- **Product Catalog at Billion-SKU Scale**: Schema design for 2 billion products with wildly varying attributes (a TV has "screen size"; a shirt has "sleeve length"). Modeling with the EAV anti-pattern alternatives (JSON columns, wide tables, category-specific extension tables).
- **Order Pipeline Architecture**: From cart-click to delivered. Event-driven order state machine, SAGA pattern for distributed transactions across Inventory, Payment, and Shipping.
- **Real-Time Pricing Engine**: Dynamic pricing based on demand, competition, and inventory. Sub-100ms pricing queries served from a Redis + DynamoDB architecture.
- **Recommendation Data Architecture**: Collaborative filtering requires user-item interaction matrices at petabyte scale. Feature store for real-time model serving.

### `02_Media_Streaming_Data_Platform/` (Netflix-style)

- **Content Ingestion Pipeline**: Metadata ingestion from studios, encoding pipeline telemetry, rights management data across 190 countries.
- **Viewing History at 200M+ Users**: Designing for 100 billion events/day. Partition key strategies to avoid hot spots for trending shows ("Squid Game launches and 50M people watch simultaneously").
- **A/B Testing Infrastructure**: Persistent user bucketing, feature exposure logging, metric computation at scale. Ensuring statistical significance with proper sample sizes.
- **Personalization Data Flow**: Real-time feature pipelines feeding recommendation models. Balancing exploration (showing new content) vs. exploitation (showing what the user will definitely watch).

### `03_Financial_Services_Data_Platform/`

- **Transaction Processing**: Bi-temporal modeling for regulatory compliance. "Show me the state of this account as it was known on January 15th, reflecting transactions valid through January 10th."
- **Fraud Detection Pipeline**: Real-time scoring on every transaction. Graph-based analysis for synthetic identity rings. Balancing false positive rate (blocking legitimate transactions) vs. false negative rate (missing fraud).
- **Regulatory Reporting**: BCBS 239 data aggregation and reporting. SOX compliance audit trails. Data lineage from source to report for regulatory traceability.

### `04_Healthcare_Data_Platform/`

- **HIPAA-Compliant Data Lake**: PHI de-identification (Safe Harbor: remove 18 identifiers), BAA requirements, encryption at rest and in transit, audit logs for every data access.
- **Clinical Trial Data Integration**: Harmonizing data from 50 different hospital systems with different EHR formats (HL7 FHIR, CDA). Entity resolution for patient matching across institutions.
- **Real-Time Patient Monitoring**: IoT sensor data from ICU devices → Kafka → Flink → Alert engine. Sub-second anomaly detection on vital signs.

### `05_IoT_And_Manufacturing/`

- **Time-Series Data at Scale**: 10,000 sensors × 1 sample/second = 864 million records/day. TimescaleDB vs. InfluxDB vs. Cassandra for this workload.
- **Predictive Maintenance Pipeline**: Batch-trained ML models deployed for real-time inference on edge devices. Feature engineering from raw vibration, temperature, and pressure signals.
- **Digital Twin Data Architecture**: Maintaining a virtual replica of physical assets updated in real-time. MQTT → Kafka → Lake → Visualization.

### `06_Cross_Domain_Migration_Scenarios/`

- **On-Prem DW → Cloud Lakehouse Migration**: The 18-month playbook. Assessment → Proof of Concept → Parallel Running → Cutover → Decommission. Managing the "dual stack" period where both systems must produce identical results.
- **Monolith → Data Mesh Transformation**: Identifying domain boundaries, building the self-serve platform, training domain teams, and managing the 2-3 year organizational transition.
- **Cost Optimization Exercise**: Taking a $3M/year cloud data bill and reducing it to $800K without degrading SLAs. Storage tiering, right-sizing compute, query optimization, and eliminating zombie resources.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
