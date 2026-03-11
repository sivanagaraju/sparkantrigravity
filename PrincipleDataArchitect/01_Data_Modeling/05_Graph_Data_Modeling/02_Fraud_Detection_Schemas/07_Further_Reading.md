# Fraud Detection Schemas — Further Reading

> Papers, books, engineering blogs, conference talks, repositories, and cross-references.

---

## Papers

| Title | Authors | Year | URL |
|---|---|---|---|
| *Graph-Based Anomaly Detection and Description: A Survey* | Akoglu, Tong, Koutra | 2015 | <https://dl.acm.org/doi/10.1007/s10618-014-0365-y> |
| *Fraud Detection using Graph Analysis* | Various | 2020 | <https://neo4j.com/whitepapers/fraud-detection-graph-analysis/> |
| *EvilCohort: Detecting Communities of Malicious Accounts on Online Services* | Ruan et al. (LinkedIn) | 2016 | <https://dl.acm.org/doi/10.5555/3016100.3016360> |
| *Mining Billion-Scale Graphs for Fraud Detection on Alibaba* | Liu et al. (Alibaba) | 2019 | <https://arxiv.org/abs/1907.11285> |
| *FinancialGraph: Knowledge Graph for Financial Services* | Various | 2023 | <https://arxiv.org/search/?query=financial+graph+fraud+detection> |

---

## Books

| Title | Author(s) | ISBN | Relevant Chapters |
|---|---|---|---|
| *Graph-Powered Machine Learning* | Alessandro Negro | 978-1617295645 | Ch 5 (fraud detection), Ch 6 (anomaly detection) |
| *Graph Databases* (2nd Ed) | Robinson, Webber, Eifrem | 978-1491930892 | Ch 7 (fraud detection use case) |
| *Graph Algorithms* | Mark Needham, Amy Hodler | 978-1492047674 | Ch 4 (centrality), Ch 5 (community detection) |
| *Responsible AI: Best Practices for Creating Trustworthy AI Systems* | Mhatre, Tadimeti | 978-1098102425 | Ch 9 (bias in fraud detection — important for fairness) |

---

## Blog Posts — Engineering Blogs

| Title | Source | URL |
|---|---|---|
| *Real-Time Fraud Detection with Graph* | PayPal Engineering | <https://medium.com/paypal-tech/real-time-graph-based-fraud-detection-at-paypal-c0e2c1d89e04> |
| *Using Graph Analytics for Fraud Detection* | Neo4j Blog | <https://neo4j.com/use-cases/fraud-detection/> |
| *TigerGraph for Fraud Detection* | TigerGraph | <https://www.tigergraph.com/solutions/fraud-detection/> |
| *Amazon Neptune for Fraud Detection* | AWS Blog | <https://aws.amazon.com/blogs/database/detect-fraud-using-amazon-neptune/> |
| *Anti-Money Laundering with Graph* | Neo4j Blog | <https://neo4j.com/use-cases/anti-money-laundering/> |
| *Stripe Radar: ML Fraud Detection* | Stripe Engineering | <https://stripe.com/radar> |

---

## Conference Talks

| Title | Speaker | Event | URL |
|---|---|---|---|
| *Graph-Based Fraud Detection at Scale* | Various | GraphSummit | <https://www.youtube.com/results?search_query=graph+fraud+detection+summit> |
| *Fighting Financial Crime with Graphs* | Neo4j | GIDS | <https://www.youtube.com/results?search_query=neo4j+financial+crime+graph> |
| *Real-Time Graph Analytics for AML* | TigerGraph | FinTech Summit | <https://www.youtube.com/results?search_query=tigergraph+aml+graph+analytics> |
| *Community Detection for Fraud* | Various | KDD | <https://www.youtube.com/results?search_query=community+detection+fraud+kdd> |

---

## GitHub Repos

| Repository | Description | URL |
|---|---|---|
| `neo4j-graph-examples/fraud-detection` | Neo4j fraud detection example dataset | <https://github.com/neo4j-graph-examples/fraud-detection> |
| `neo4j/graph-data-science` | Neo4j GDS library (community detection, centrality, etc.) | <https://github.com/neo4j/graph-data-science> |
| `tigergraph/ecosys` | TigerGraph fraud detection examples | <https://github.com/tigergraph/ecosys> |
| `dmlc/dgl` | Deep Graph Library (graph neural networks for fraud) | <https://github.com/dmlc/dgl> |
| `yelp/yelp-fraud-detection` | Yelp review fraud detection research | <https://www.yelp.com/dataset> |
| `safe-graph/DGFraud` | Deep graph-based fraud detection toolkit | <https://github.com/safe-graph/DGFraud> |

---

## Official Documentation

| Product | Doc Title | URL |
|---|---|---|
| **Neo4j** | Fraud Detection Use Case | <https://neo4j.com/use-cases/fraud-detection/> |
| **Neo4j GDS** | Community Detection Algorithms | <https://neo4j.com/docs/graph-data-science/current/algorithms/community-detection/> |
| **TigerGraph** | Fraud & AML Solution | <https://www.tigergraph.com/solutions/fraud-detection/> |
| **Amazon Neptune** | Fraud Detection Guide | <https://docs.aws.amazon.com/neptune/latest/userguide/> |
| **Apache Spark** | GraphFrames User Guide | <https://graphframes.github.io/graphframes/docs/_site/user-guide.html> |

---

## Cross-References

| Related Concept | Location | Why It's Related |
|---|---|---|
| **Property Graphs** | `05_Graph_Data_Modeling/01_Property_Graphs/` | Fraud detection schemas are built on property graph foundations |
| **Super Nodes** | `05_Graph_Data_Modeling/03_Super_Nodes/` | Super nodes (merchants, hubs) are the #1 performance challenge in fraud graphs |
| **Temporal Modeling** | `04_Temporal_and_Bitemporal_Modeling/` | Fraud patterns have temporal dimensions — ring activity within 7 days, velocity within 1 hour |
| **SCD Extreme Cases** | `02_Dimensional_Modeling_Advanced/02_SCD_Extreme_Cases/` | Account status changes (active → frozen → active) require SCD-like tracking in fraud analysis |
