# 14 — Data Architecture for AI (LLMOps & ML Infrastructure)

> "The hardest part of AI isn't the model; it's the data plumbing required to feed the model reliably, legally, and at low latency."

A Principal Data Architect in 2026 must know how to design the data layer that sits beneath GenAI, RAG, and predictive models. A brilliant model fed by a fragile, inconsistent data pipeline is a liability, not an asset.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Feature_Stores_and_Serving/`

- **Online vs. Offline Stores**: Bridging the gap between batch training data (Snowflake/S3) and sub-millisecond real-time inference data (Redis/DynamoDB).
- **Point-in-Time Correctness**: The dreaded "Data Leakage" problem. Architecting time-travel joins to ensure a model trained on 2024 data doesn't accidentally see 2025 features.
- **Feature Registries**: Building discoverable, governed catalog of ML features (e.g., Feast, Tecton) to stop teams from recalculating `Customer_LTV_30Day` in 14 different ways.

### `02_RAG_Pipelines_Retrieval_Augmented_Generation/`

- **Vector Embedding Pipelines**: Architecting ingestion streams that parse PDFs, OCR images, chunk text, call OpenAI/Cohere embedding APIs, and sink to a Vector DB.
- **Chunking Strategies for Context Windows**: Semantic chunking vs. fixed-length overlapping window chunking. Graph-based entity chunking.
- **Hybrid Search Architecture**: Combining dense vector search (ANN / HNSW) with sparse keyword search (BM25) and applying cross-encoder reranking algorithms for maximum recall.

### `03_LLMOps_and_Evaluation_Data/`

- **Prompt and Context Logging**: Storing every inference request, the retrieved RAG context, and the model output for safety, compliance, and continuous fine-tuning.
- **Golden Datasets & Ground Truth Orchestration**: Managing the feedback loop. Designing schemas to capture human-in-the-loop (RLHF) feedback to measure data drift.

### `04_Data_Moats_and_Proprietary_Loops/`

- **Architecting the Flywheel**: How to design an application data model specifically to harvest high-quality training data that competitors cannot easily scrape.
- **Synthetic Data Generation Pipelines**: Using models to generate privacy-safe datasets for downstream testing and secondary model training.

### `05_AI_Data_Governance_and_Security/`

- **Copyright and PII Scrubbing**: Architecting deterministic and statistical pipelines to scrub toxic or copyrighted training data before it hits a model.
- **Access Control for Embeddings**: If a user lacks permission to read Document A, ensuring their RAG pipeline query cannot semantically retrieve chunks of Document A.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
