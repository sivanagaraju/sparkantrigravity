# 12 — Data Security & Privacy

> "Security is not a feature you add at the end. It is a constraint that shapes every architectural decision from Day 1."

At FAANG companies, a single data breach can cost billions in fines, lawsuits, and reputation damage. A Principal Data Architect designs security into the data platform's DNA — encryption, access control, PII handling, and audit logging are non-negotiable foundations, not afterthoughts.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Defense_In_Depth_Architecture/`

- **Zero Trust for Data**: Never assume the network is safe. Every data access request must be authenticated, authorized, and audited — even from internal services.
- **Data Security Layers**: Network (VPC, private endpoints) → Transport (TLS 1.3) → Storage (AES-256 at-rest) → Application (column-level encryption) → Governance (access policies). A breach at one layer doesn't expose all data.
- **The Blast Radius**: Designing systems so that a compromised service account can access only its own domain's data, not the entire data lake. IAM granularity, resource-level policies, and service perimeters.

### `02_Encryption_Deep_Dive/`

- **At-Rest Encryption**: Transparent Data Encryption (TDE), S3 Server-Side Encryption (SSE-S3, SSE-KMS, SSE-C). The difference between encrypting the volume vs. encrypting each object with a unique key.
- **In-Transit Encryption**: TLS 1.3, mutual TLS (mTLS) for service-to-service communication. Certificate rotation automation.
- **In-Use / Application-Level Encryption**: Encrypting specific columns (SSN, credit card) with application-managed keys so that even database administrators cannot read the plaintext.
- **Key Management**: AWS KMS, Azure Key Vault, GCP Cloud KMS. Key rotation policies. The catastrophic scenario: what happens when you lose the encryption key.

### `03_Access_Control_Models/`

- **RBAC (Role-Based Access Control)**: The foundation. Roles (Analyst, Engineer, Admin) mapped to permissions. The role explosion problem at 500+ users.
- **ABAC (Attribute-Based Access Control)**: Policy decisions based on user attributes (department, clearance level), resource attributes (data classification, region), and environmental attributes (time of day, IP address).
- **Column-Level and Row-Level Security**: In Snowflake, BigQuery, and Databricks. "Marketing can see customer names but not SSNs." "EU analysts can see EU customer data but not US data."
- **Dynamic Data Masking**: Real-time masking of sensitive fields based on the querying user's role. The analyst sees `***-**-1234` while the compliance officer sees `123-45-1234`.

### `04_PII_Handling_Framework/`

- **Data Classification Taxonomy**: Public → Internal → Confidential → Restricted. Automated classification using regex patterns, NLP models, and catalog tags.
- **Tokenization vs. Pseudonymization vs. Anonymization**: Tokenization (reversible with a token vault), Pseudonymization (reversible with a key), Anonymization (irreversible). GDPR requires knowing which technique satisfies which requirement.
- **Right to Erasure ("Right to Be Forgotten")**: The architectural nightmare. When a GDPR subject requests deletion, you must find and delete their data across 30+ systems, including backups, logs, and derived datasets. Designing for deletability from Day 1.

### `05_Compliance_Frameworks/`

- **GDPR**: Data residency (EU data stays in EU), lawful basis for processing, Data Protection Impact Assessments (DPIA), 72-hour breach notification.
- **CCPA/CPRA**: California's privacy law. The "Do Not Sell" flag. Right to know, right to delete, right to opt-out.
- **HIPAA**: Protected Health Information (PHI). Business Associate Agreements (BAAs). De-identification via Safe Harbor or Expert Determination methods.
- **SOX**: Financial data integrity controls. Audit trails for every change to financial data pipelines.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
