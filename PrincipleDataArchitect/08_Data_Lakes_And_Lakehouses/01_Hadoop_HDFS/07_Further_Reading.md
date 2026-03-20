# Hadoop & HDFS — Further Reading

## Fundamental Engineering Reading

The entire Hadoop ecosystem is an open-source clone of two landmark academic papers published by Google. You cannot claim mastery of modern distributed data without reading the original source texts.

| Title | Authors | Key Topic |
|---|---|---|
| *The Google File System (2003)* | Sanjay Ghemawat, Howard Gobioff, Shun-Tak Leung | The blueprint for HDFS. Explicitly details the decision to abandon expensive SANs for commodity hardware, the 64MB/128MB chunk allocation size logic, the single Master metadata server memory limits, and the fault-tolerance replication architecture. |
| *MapReduce: Simplified Data Processing on Large Clusters (2004)* | Jeffrey Dean, Sanjay Ghemawat | The blueprint for MapReduce. Explains the paradigm of moving computation to where the data lives, and mechanically details the Map phase, the network-heavy Shuffle/Sort phase, and the Reduce aggregation. |

## Ecosystem Evolution

| Title | Publisher | Description |
|---|---|---|
| *Hadoop: The Definitive Guide (4th Edition)* | Tom White (O'Reilly) | The absolute bible of the Hadoop era. While the ecosystem is fading, the mechanical chapters explaining how YARN allocates containers and how HDFS processes heartbeats remain relevant to understanding modern Kubernetes and distributed object stores. |
| *Why Hadoop Failed* | Industry Blogs/Retrospectives | Various. A critical subject to research. Focus on architectural essays discussing the "tight coupling of compute and storage" and the administrative nightmare of JVM tuning that drove the industry toward AWS S3 and serverless databricks. |

## Official References

- **Apache Hadoop Official Docs**: https://hadoop.apache.org/
- **HDFS Architecture Guide**: https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html (Crucial for understanding how NameNode metadata operates and how heartbeats dictate cluster health).
