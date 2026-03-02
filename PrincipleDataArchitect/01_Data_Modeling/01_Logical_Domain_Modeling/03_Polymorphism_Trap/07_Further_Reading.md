# Polymorphism Trap — Further Reading & References

> Papers, books, blog posts, GitHub repos, and cross-references.

---

## 📚 Books

| Book | Author | Relevant Chapter |
|---|---|---|
| *SQL Antipatterns* | Bill Karwin | Ch. 7: Polymorphic Associations — the definitive anti-pattern reference |
| *Patterns of Enterprise Application Architecture* | Martin Fowler | Ch. 12: STI, CTI, CCI — the original pattern names |
| *Designing Data-Intensive Applications* | Martin Kleppmann | Ch. 2: Data Models and Query Languages — relational vs document models |
| *Database Design for Mere Mortals* | Michael Hernandez | Ch. 9: Table relationships and inheritance patterns |
| *Refactoring Databases* | Scott Ambler | Strategies for migrating from STI to CTI/CCI |

## 🎤 Talks

| Talk | Speaker | Where |
|---|---|---|
| *SQL Antipatterns Strike Back* | Bill Karwin | PGConf — [YouTube](https://www.youtube.com/results?search_query=bill+karwin+sql+antipatterns) |
| *The Trouble with Polymorphic Associations* | Brad Urani | RailsConf |
| *Data Modeling Mistakes* | Kimball Group | Various TDWI conferences |

## 🔗 GitHub Repositories

| Repo | Description |
|---|---|
| [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer) | System design fundamentals including database schema patterns |
| [bregman-arie/devops-exercises](https://github.com/bregman-arie/devops-exercises) | Includes database design exercises with polymorphism scenarios |
| [rxin/db-readings](https://github.com/rxin/db-readings) | Curated database readings including storage engine internals relevant to STI performance |
| [DataEngineer-io/data-engineer-handbook](https://github.com/DataEngineer-io/data-engineer-handbook) | Comprehensive data engineering resource collection |

## 📝 Blog Posts

| Article | Source |
|---|---|
| [Polymorphic Associations Considered Harmful](https://hasura.io/blog/modeling-approaches-for-polymorphic-associations) | Hasura Blog |
| [Why You Should Avoid Polymorphic Associations](https://blog.appsignal.com/2024/01/24/single-table-inheritance-in-rails.html) | AppSignal Blog |
| [Schema Design Anti-Patterns](https://www.uber.com/en-US/blog/schemaless-sql-database/) | Uber Engineering |
| [Snowflake Schema Design Best Practices](https://docs.snowflake.com/en/user-guide/table-considerations) | Snowflake Docs |

## 🔗 Cross-References in This Curriculum

| Related Concept | Path | Connection |
|---|---|---|
| Event Storming | [../01_Event_Storming](../01_Event_Storming/) | Events reveal entity hierarchies that may fall into the polymorphism trap |
| Bounded Contexts | [../02_Bounded_Contexts](../02_Bounded_Contexts/) | Different types often belong to different BCs — splitting by BC naturally eliminates the trap |
| Query-Driven Modeling (NoSQL) | [../../06_NoSQL_and_Document_Modeling/01_Query_Driven_Modeling](../../06_NoSQL_and_Document_Modeling/01_Query_Driven_Modeling/) | Document models handle polymorphism naturally (schema-per-document) |
| Schema Evolution | [../../06_NoSQL_and_Document_Modeling/03_Schema_Evolution](../../06_NoSQL_and_Document_Modeling/03_Schema_Evolution/) | How to evolve schemas when refactoring from STI |
| Star Schema Fundamentals | [../../10_Data_Modeling_For_Analytics/01_Star_Schema_Fundamentals](../../10_Data_Modeling_For_Analytics/01_Star_Schema_Fundamentals/) | Star schema avoids polymorphism by design (one fact table per business process) |
| EAV Pattern | [../../09_Schema_Design_Patterns/03_EAV_Pattern_And_Alternatives](../../09_Schema_Design_Patterns/03_EAV_Pattern_And_Alternatives/) | EAV is an extreme form of polymorphism — and usually an anti-pattern |
| B-Trees vs LSM | [../../../../02_Database_Systems/01_Storage_Engines_and_Disk_Layout/01_B_Trees_vs_LSM_Trees](../../../../02_Database_Systems/01_Storage_Engines_and_Disk_Layout/01_B_Trees_vs_LSM_Trees/) | Storage engine behavior with wide, sparse STI tables |
