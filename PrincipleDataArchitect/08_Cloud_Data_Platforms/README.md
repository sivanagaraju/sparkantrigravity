# 08 — Cloud Data Platforms

> "The cloud bill is the new org chart. Which team consumes what tells you more about the real architecture than any diagram."

A Principal Data Architect must possess multi-cloud fluency: not just knowing what each service *does*, but understanding the architectural trade-offs, pricing models, and vendor lock-in implications that determine whether you'll save or waste millions.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_AWS_Data_Stack/`

- **S3 as the Data Lake Foundation**: Storage classes (Standard, IA, Glacier, Glacier Deep Archive). S3 Select for in-place querying. Request pricing traps — why 1 billion LIST requests cost more than the storage itself.
- **Glue and the AWS Catalog**: Glue crawlers (automatic schema inference), Glue ETL (PySpark jobs), Glue Data Catalog (Hive Metastore compatible). Why Glue ETL jobs are 3x more expensive than equivalent EMR Spark jobs for identical workloads.
- **Athena and Lake Formation**: Serverless querying via Presto. Column-level and row-level security through Lake Formation tag-based access control. The per-query pricing model vs. provisioned capacity.
- **Kinesis (Data Streams, Firehose, Analytics)**: The AWS-native Kafka competitor. Why Kinesis shards are simpler but less flexible than Kafka partitions.

### `02_Azure_Data_Stack/`

- **ADLS Gen2**: Built on Azure Blob Storage with hierarchical namespace (real directories). ACLs at folder/file level. Why ADLS Gen2 is the de facto standard for Azure data lakes.
- **Synapse Analytics**: The unified analytics service. Dedicated SQL pools (MPP), Serverless SQL pools (pay-per-query), Spark pools. Synapse Pipelines (Azure Data Factory rebranded).
- **Azure Purview / Microsoft Purview**: Unified data governance. Automated data classification, sensitivity labeling, and lineage tracking across Azure, AWS, and on-premises.
- **Databricks on Azure**: First-class integration. Unity Catalog for cross-workspace governance. DBFS vs. direct ADLS access. When to use Azure-native vs. Databricks-native services.

### `03_GCP_Data_Stack/`

- **BigQuery Architectural Deep Dive**: Dremel execution engine, Colossus distributed storage, Jupiter network. How BigQuery achieves petabyte-scale queries in seconds. Slot-based pricing vs. on-demand pricing.
- **Dataflow (Apache Beam)**: The only cloud-native unified batch+streaming engine. Autoscaling workers. Why Google built Beam to avoid the Spark-vs-Flink debate.
- **Pub/Sub vs. Kafka**: Pub/Sub is serverless, infinitely scalable, and requires zero operational overhead. But no consumer groups, no key-based ordering guarantees, and limited replay.

### `04_Databricks_Unified_Platform/`

- **Unity Catalog**: Cross-workspace, cross-cloud governance. Three-level namespace: catalog.schema.table. Fine-grained access control on tables, volumes, and ML models.
- **Delta Live Tables (DLT)**: Declarative pipeline framework. Define expectations (data quality rules) inline. Automatic dependency resolution.
- **Photon Engine**: C++ native query engine replacing Spark's JVM-based execution for 2-8x performance on SQL workloads.
- **SQL Warehouses**: Serverless SQL compute replacing traditional Spark clusters for BI and ad-hoc analytics.

### `05_Multi_Cloud_Strategy/`

- **Data Gravity**: Data attracts applications. Moving 1 PB of data between clouds costs $20,000+ in egress fees alone. Architectures should move compute to data, not data to compute.
- **Cloud-Agnostic Abstraction Layers**: The promise (freedom from lock-in) vs. the reality (lowest-common-denominator features, doubled operational complexity). When Iceberg serves as the abstraction layer.
- **The "Best of Breed" Pattern**: BigQuery for analytics + AWS for ML/SageMaker + Azure for enterprise integration. Making this work without doubling your platform team.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
