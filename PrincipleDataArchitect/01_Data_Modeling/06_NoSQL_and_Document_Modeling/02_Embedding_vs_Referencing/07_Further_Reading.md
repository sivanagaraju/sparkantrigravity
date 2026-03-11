# Embedding vs Referencing — Further Reading

> Papers, books, engineering blogs, conference talks, repositories, and cross-references.

---

## Papers

| Title | Authors | Year | URL |
|---|---|---|---|
| *Schema Design for Time Series Data in MongoDB* | MongoDB Inc | 2018 | <https://www.mongodb.com/blog/post/time-series-data-and-mongodb-part-2-schema-design-best-practices> |
| *JSON Schema Validation in Document Databases* | Various | 2020 | <https://www.mongodb.com/docs/manual/core/schema-validation/> |
| *On the Denormalization of NoSQL Databases* | Dasgupta et al. | 2019 | <https://dl.acm.org/doi/10.1145/3299869> |

---

## Books

| Title | Author(s) | ISBN | Relevant Chapters |
|---|---|---|---|
| *MongoDB: The Definitive Guide* (3rd Ed) | Bradshaw, Brazil, Chodorow | 978-1491954461 | Ch 8 (schema design patterns) |
| *The DynamoDB Book* | Alex DeBrie | 978-1734617306 | Ch 10 (one-to-many patterns), Ch 11 (many-to-many) |
| *MongoDB in Action* (2nd Ed) | Banker et al. | 978-1617291609 | Ch 5 (schema design) |
| *Designing Data-Intensive Applications* | Martin Kleppmann | 978-1449373320 | Ch 2 (data models — document section) |

---

## Blog Posts — Engineering Blogs

| Title | Source | URL |
|---|---|---|
| *6 Rules of Thumb for MongoDB Schema Design* | MongoDB Blog | <https://www.mongodb.com/blog/post/6-rules-of-thumb-for-mongodb-schema-design> |
| *Building with Patterns (12-Part Series)* | MongoDB Blog | <https://www.mongodb.com/blog/post/building-with-patterns-a-summary> |
| *Schema Design Anti-Patterns* | MongoDB Blog | <https://www.mongodb.com/developer/products/mongodb/schema-design-anti-pattern-massive-arrays/> |
| *Extended Reference Pattern* | MongoDB Developer | <https://www.mongodb.com/developer/products/mongodb/schema-design-anti-pattern-separating-data/> |
| *DynamoDB One-to-Many Relationships* | Alex DeBrie | <https://www.alexdebrie.com/posts/dynamodb-one-to-many/> |

---

## Conference Talks

| Title | Speaker | Event | URL |
|---|---|---|---|
| *Schema Design Best Practices* | Daniel Coupal | MongoDB University | <https://www.youtube.com/results?search_query=mongodb+schema+design+best+practices> |
| *Building with Patterns* | MongoDB | MongoDB Live | <https://www.youtube.com/results?search_query=mongodb+building+with+patterns> |
| *Advanced Schema Design Patterns* | Various | MongoDB World | <https://www.youtube.com/results?search_query=mongo+world+schema+design> |

---

## GitHub Repos

| Repository | Description | URL |
|---|---|---|
| `mongodb/mongo` | MongoDB source | <https://github.com/mongodb/mongo> |
| `mongodb-university/schema-design-patterns` | Schema design pattern examples | <https://github.com/mongodb-university> |
| `jeremydaly/dynamodb-toolbox` | DynamoDB single-table design toolkit | <https://github.com/jeremydaly/dynamodb-toolbox> |
| `alexdebrie/dynamodb-examples` | DynamoDB pattern examples | <https://github.com/alexdebrie> |

---

## Official Documentation

| Product | Doc Title | URL |
|---|---|---|
| **MongoDB** | Schema Design Patterns | <https://www.mongodb.com/docs/manual/core/data-model-design/> |
| **MongoDB** | Embedding vs References | <https://www.mongodb.com/docs/manual/tutorial/model-embedded-one-to-many-relationships-between-documents/> |
| **DynamoDB** | Item Collection Patterns | <https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-sort-keys.html> |
| **Firestore** | Data Model | <https://firebase.google.com/docs/firestore/data-model> |
| **Couchbase** | Document Design | <https://docs.couchbase.com/server/current/learn/data/document-data-model.html> |

---

## Cross-References

| Related Concept | Location | Why It's Related |
|---|---|---|
| **Query-Driven Modeling** | `06_NoSQL_and_Document_Modeling/01_Query_Driven_Modeling/` | Embedding/referencing serves the access patterns defined by query-driven design |
| **Schema Evolution** | `06_NoSQL_and_Document_Modeling/03_Schema_Evolution/` | Schema changes impact embedded data (nested field additions, removals) |
| **Denormalization (Dimensional)** | `02_Dimensional_Modeling_Advanced/` | Embedding is denormalization applied at the document level |
| **Conformed Dimensions** | `02_Dimensional_Modeling_Advanced/04_Conformed_Dimensions/` | Extended reference pattern mirrors conformed dimension concept |
