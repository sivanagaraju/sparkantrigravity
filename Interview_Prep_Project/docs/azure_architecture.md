# Azure Lakehouse Architecture Design (Swiss Re Context)

This document outlines the target architecture for the "Cashflow Enhancement" product, based on the Medallion Architecture (Bronze/Silver/Gold) on Azure.

## 1. High-Level Diagram

```mermaid
graph LR
    Sources[Source Systems<br/>(CSVs, APIs, Oracle)] -->|Ingest| ADF[Azure Data Factory]
    ADF -->|Raw Data| ADLS_Bronze[(ADLS Gen2<br/>Bronze Layer)]
    
    subgraph "Databricks Lakehouse"
        ADLS_Bronze -->|Stream/Batch| Spark_Silver[Spark Job<br/>(Cleaning & Enrichment)]
        Spark_Silver -->|Delta| ADLS_Silver[(ADLS Gen2<br/>Silver Layer)]
        ADLS_Silver -->|Aggregation| Spark_Gold[Spark SQL<br/>(Business Logic)]
        Spark_Gold -->|Delta| ADLS_Gold[(ADLS Gen2<br/>Gold Layer)]
    end
    
    ADLS_Gold -->|Serve| PBI[Power BI / Reporting]
    ADLS_Gold -->|Serve| Downstream[Downstream Systems]
    
    KV[Azure Key Vault] -.->|Secrets| ADF
    KV -.->|Secrets| Spark_Silver
```

## 2. Component Details

### **Ingestion Layer (Azure Data Factory)**
*   **Role:** Orchestrator and Data Mover.
*   **Pipelines:**
    *   `Copy Activity`: Moves data from on-premise Oracle or SFTP servers to ADLS Gen2 (Bronze).
    *   `Execute Databricks Notebook`: Triggers the PySpark transformation jobs.
*   **Triggers:** Event-based (when file lands) or Schedule-based (e.g., Daily at 2 AM).

### **Storage Layer (ADLS Gen2)**
*   **Format:** Delta Lake (Parquet + Transaction Log).
*   **Structure:**
    *   `container/bronze/source_system/table/yyyy/mm/dd/` (Raw, Immutable)
    *   `container/silver/domain/table/` (Cleaned, Enriched, Schema Enforced)
    *   `container/gold/domain/aggregate/` (Business KPIs)

### **Processing Layer (Azure Databricks)**
*   **Cluster Configuration:**
    *   **Job Clusters:** Ephemeral clusters created just for the job (Cost effective).
    *   **Autoscaling:** Enabled (e.g., 2 to 8 workers) to handle variable loads.
    *   **Runtime:** Databricks Runtime 13.3 LTS (Spark 3.4).
*   **Optimization:**
    *   **Photon Engine:** Enabled for high-performance SQL execution.
    *   **Optimize/Z-Order:** Scheduled maintenance jobs to compact small files and index key columns.

### **Security & Governance**
*   **Azure Key Vault:** Stores API keys, database passwords, and connection strings. Accessed via Databricks Secret Scopes (`dbutils.secrets.get`).
*   **Unity Catalog:** (Modern Approach) Centralized governance for tables, files, and ML models. Manages access control (ACLs) at the column/row level.

## 3. The "Cashflow Enhancement" Workflow

1.  **Input:** Daily CSVs containing Claims and Policyholder data land in the Bronze container.
2.  **Trigger:** ADF detects the new file and starts the `Claims_ETL` pipeline.
3.  **Silver Job (PySpark):**
    *   Reads Bronze Delta table.
    *   **Validation:** Checks for null `claim_id` or negative `amount`.
    *   **Enrichment:** Calls the Hashing API (using `mapPartitions` optimization).
    *   **Join:** Joins with Policyholder dimension.
    *   **Write:** Upserts (Merge) into the Silver Delta table to handle duplicates.
4.  **Gold Job (SQL):**
    *   Aggregates claims by Region and Month.
    *   Calculates "Urgent" vs "Normal" ratios.
    *   Writes to Gold Delta table.

## 4. Disaster Recovery & DevOps
*   **Infrastructure as Code (IaC):** Terraform is used to provision the Databricks Workspace, Clusters, and ADF.
*   **CI/CD:** Azure DevOps pipelines build the Python Wheel, run unit tests, and deploy the artifacts.
