# Query-Driven Modeling — Further Reading

> Papers, books, engineering blogs, conference talks, repositories, and cross-references.

---

## Papers

| Title | Authors | Year | URL |
|---|---|---|---|
| *Dynamo: Amazon's Highly Available Key-Value Store* | DeCandia et al. | 2007 | <https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf> |
| *Bigtable: A Distributed Storage System for Structured Data* | Chang et al. (Google) | 2006 | <https://research.google/pubs/pub27898/> |
| *Cassandra — A Decentralized Structured Storage System* | Lakshman, Malik (Facebook) | 2010 | <https://www.cs.cornell.edu/projects/ladis2009/papers/lakshman-ladis2009.pdf> |

---

## Books

| Title | Author(s) | ISBN | Relevant Chapters |
|---|---|---|---|
| *The DynamoDB Book* | Alex DeBrie | 978-1-7345181-0-7 | All — the definitive guide to single-table design |
| *Cassandra: The Definitive Guide* (3rd Ed) | Jeff Carpenter, Eben Hewitt | 978-1492097143 | Ch 5 (data modeling), Ch 6 (query-driven design) |
| *MongoDB: The Definitive Guide* (3rd Ed) | Shannon Bradshaw et al. | 978-1491954461 | Ch 8 (schema design), Ch 9 (indexing) |
| *Designing Data-Intensive Applications* | Martin Kleppmann | 978-1449373320 | Ch 2 (data models), Ch 6 (partitioning) |
| *NoSQL Distilled* | Pramod Sadalage, Martin Fowler | 978-0321826626 | Ch 4 (distribution models), Ch 5 (consistency) |

---

## Blog Posts — Engineering Blogs

| Title | Source | URL |
|---|---|---|
| *Best Practices for DynamoDB* | AWS Documentation | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html> |
| *Single-Table Design with DynamoDB* | Alex DeBrie | <https://www.alexdebrie.com/posts/dynamodb-single-table/> |
| *How Discord Stores Billions of Messages* | Discord Engineering | <https://discord.com/blog/how-discord-stores-billions-of-messages> |
| *How Discord Stores Trillions of Messages* | Discord Engineering | <https://discord.com/blog/how-discord-stores-trillions-of-messages> |
| *Netflix Data Engineering: Cassandra* | Netflix Tech Blog | <https://netflixtechblog.com/tagged/cassandra> |
| *DynamoDB at Prime Day Scale* | AWS Blog | <https://aws.amazon.com/blogs/database/amazon-dynamodb-update-new-features-for-prime-day/> |

---

## Conference Talks

| Title | Speaker | Event | URL |
|---|---|---|---|
| *Advanced DynamoDB Design Patterns* | Rick Houlihan | re:Invent | <https://www.youtube.com/results?search_query=rick+houlihan+dynamodb+reinvent> |
| *DynamoDB Deep Dive* | AWS | re:Invent | <https://www.youtube.com/results?search_query=dynamodb+deep+dive+reinvent> |
| *Data Modeling for Cassandra* | Patrick McFadin | DataStax | <https://www.youtube.com/results?search_query=patrick+mcfadin+cassandra+data+modeling> |

---

## GitHub Repos

| Repository | Description | URL |
|---|---|---|
| `alexdebrie/dynamodb-toolbox` | DynamoDB single-table design toolkit | <https://github.com/jeremydaly/dynamodb-toolbox> |
| `aws-samples/amazon-dynamodb-design-patterns` | AWS DynamoDB design pattern examples | <https://github.com/aws-samples> |
| `scylladb/scylladb` | ScyllaDB — Cassandra-compatible, query-driven | <https://github.com/scylladb/scylladb> |
| `apache/cassandra` | Apache Cassandra | <https://github.com/apache/cassandra> |
| `mongodb/mongo` | MongoDB | <https://github.com/mongodb/mongo> |

---

## Official Documentation

| Product | Doc Title | URL |
|---|---|---|
| **DynamoDB** | Best Practices | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html> |
| **DynamoDB** | Single-Table Design | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-modeling-nosql.html> |
| **Cassandra** | Data Modeling | <https://cassandra.apache.org/doc/latest/cassandra/data_modeling/index.html> |
| **MongoDB** | Schema Design | <https://www.mongodb.com/docs/manual/core/data-model-design/> |
| **ScyllaDB** | Data Modeling | <https://docs.scylladb.com/stable/data-modeling/> |

---

## Cross-References

| Related Concept | Location | Why It's Related |
|---|---|---|
| **Embedding vs Referencing** | `06_NoSQL_and_Document_Modeling/02_Embedding_vs_Referencing/` | Core design decision in query-driven document modeling |
| **Schema Evolution** | `06_NoSQL_and_Document_Modeling/03_Schema_Evolution/` | How to handle access pattern changes after deployment |
| **Denormalization** | `02_Dimensional_Modeling_Advanced/` | Query-driven modeling uses denormalization principles from dimensional modeling |
| **Data Vault Architecture** | `03_Data_Vault_2_0_Architecture/` | Data Vault is insert-only, hub-link-satellite — conceptually similar to event-driven NoSQL patterns |
