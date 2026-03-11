# Schema Evolution — Further Reading

> Papers, books, engineering blogs, conference talks, repositories, and cross-references.

---

## Papers

| Title | Authors | Year | URL |
|---|---|---|---|
| *Online Schema Evolution in NoSQL Databases* | Various | 2019 | <https://dl.acm.org/doi/10.1145/3299869> |
| *Schema Evolution in the Wild* | Klettke et al. | 2015 | <https://link.springer.com/chapter/10.1007/978-3-319-22002-4_4> |
| *Avro: A Data Serialization System* | Apache Foundation | 2009 | <https://avro.apache.org/docs/current/spec.html> |

---

## Books

| Title | Author(s) | ISBN | Relevant Chapters |
|---|---|---|---|
| *Designing Data-Intensive Applications* | Martin Kleppmann | 978-1449373320 | Ch 4 (encoding and evolution — Avro, Protobuf, Thrift) |
| *MongoDB: The Definitive Guide* (3rd Ed) | Bradshaw et al. | 978-1491954461 | Ch 8 (schema evolution patterns) |
| *Evolutionary Database Design* | Martin Fowler, Pramod Sadalage | — | <https://martinfowler.com/articles/evodb.html> |
| *The DynamoDB Book* | Alex DeBrie | 978-1734617306 | Ch 15 (schema migration strategies) |
| *Building Event-Driven Microservices* | Adam Bellemare | 978-1492057895 | Ch 6 (schema evolution in event streams) |

---

## Blog Posts — Engineering Blogs

| Title | Source | URL |
|---|---|---|
| *Evolutionary Database Design* | Martin Fowler | <https://martinfowler.com/articles/evodb.html> |
| *MongoDB Schema Versioning Pattern* | MongoDB Blog | <https://www.mongodb.com/blog/post/building-with-patterns-the-schema-versioning-pattern> |
| *How Netflix Handles Schema Evolution* | Netflix Tech Blog | <https://netflixtechblog.com/tagged/schema> |
| *Schema Evolution in Avro and Protobuf* | Confluent | <https://docs.confluent.io/platform/current/schema-registry/avro.html> |
| *Zero-Downtime Schema Migrations* | Stripe Engineering | <https://stripe.com/blog/online-migrations> |
| *Expand and Contract Pattern* | Tim Berglund | <https://www.tim-berglund.com/> |

---

## Conference Talks

| Title | Speaker | Event | URL |
|---|---|---|---|
| *Schema Versioning Pattern* | Daniel Coupal | MongoDB Live | <https://www.youtube.com/results?search_query=mongodb+schema+versioning+pattern> |
| *Zero-Downtime Migrations at Scale* | Various | QCon/StrangeLoop | <https://www.youtube.com/results?search_query=zero+downtime+database+migration> |
| *Avro Schema Evolution* | Various | Kafka Summit | <https://www.youtube.com/results?search_query=avro+schema+evolution+kafka> |

---

## GitHub Repos

| Repository | Description | URL |
|---|---|---|
| `mongodb/mongo` | MongoDB source | <https://github.com/mongodb/mongo> |
| `confluentinc/schema-registry` | Confluent Schema Registry (Avro, Protobuf, JSON Schema) | <https://github.com/confluentinc/schema-registry> |
| `apache/avro` | Apache Avro serialization | <https://github.com/apache/avro> |
| `protocolbuffers/protobuf` | Protocol Buffers (schema evolution via field numbers) | <https://github.com/protocolbuffers/protobuf> |
| `flyway/flyway` | Database migration tool (relational — for comparison) | <https://github.com/flyway/flyway> |

---

## Official Documentation

| Product | Doc Title | URL |
|---|---|---|
| **MongoDB** | Schema Versioning Pattern | <https://www.mongodb.com/docs/manual/tutorial/model-data-for-schema-versioning/> |
| **MongoDB** | JSON Schema Validation | <https://www.mongodb.com/docs/manual/core/schema-validation/> |
| **Avro** | Schema Resolution | <https://avro.apache.org/docs/current/spec.html#Schema+Resolution> |
| **Protobuf** | Language Guide (schema evolution rules) | <https://protobuf.dev/programming-guides/proto3/> |
| **Confluent** | Schema Compatibility Types | <https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html> |

---

## Cross-References

| Related Concept | Location | Why It's Related |
|---|---|---|
| **Query-Driven Modeling** | `06_NoSQL_and_Document_Modeling/01_Query_Driven_Modeling/` | New access patterns drive schema changes |
| **Embedding vs Referencing** | `06_NoSQL_and_Document_Modeling/02_Embedding_vs_Referencing/` | Migrating from embedded to referenced (or vice versa) is a schema evolution |
| **Temporal Modeling** | `04_Temporal_and_Bitemporal_Modeling/` | Schema version tracking is a form of temporal metadata |
| **Data Vault Architecture** | `03_Data_Vault_2_0_Architecture/` | Data Vault's insert-only satellite history handles schema changes naturally |
