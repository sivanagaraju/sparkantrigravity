# Bounded Contexts — Further Reading & References

> Papers, books, blog posts, conference talks, GitHub repos, and cross-references.

---

## 📚 Books

| Book | Author | Why |
|---|---|---|
| *Domain-Driven Design* | Eric Evans (2003) | The origin of Bounded Contexts. Chapters 14-16 |
| *Domain-Driven Design Distilled* | Vaughn Vernon | Practical summary. Chapter 4: Strategic Design with Context Mapping |
| *Building Microservices* 2nd Ed. | Sam Newman (2021) | Chapter 3: Splitting the Monolith — BC-driven decomposition |
| *Data Mesh* | Zhamak Dehghani (2022) | Chapter 5: Data as a Product — BCs become data domains |
| *Designing Data-Intensive Applications* | Martin Kleppmann (2017) | Chapter 4: Encoding and Evolution — schema evolution across BCs |

## 🎤 Talks

| Talk | Speaker | Link |
|---|---|---|
| *Bounded Contexts, Microservices, and Everything In Between* | Vladik Khononov | [YouTube](https://www.youtube.com/watch?v=dlnu5pSsg7k) |
| *Context Mapping in Practice* | Michael Plöd | DDD Europe |
| *Data Mesh in Practice* | Zhamak Dehghani | [YouTube](https://www.youtube.com/watch?v=TO_IQjoB8I0) |

## 🔗 GitHub Repositories

| Repo | Description |
|---|---|
| [ddd-crew/bounded-context-canvas](https://github.com/ddd-crew/bounded-context-canvas) | Structured canvas for documenting BCs — inbound/outbound communication, ubiquitous language |
| [ddd-crew/context-mapping](https://github.com/ddd-crew/context-mapping) | Patterns and templates for mapping relationships between BCs |
| [ddd-crew/aggregate-design-canvas](https://github.com/ddd-crew/aggregate-design-canvas) | Canvas for designing aggregates within a BC |
| [mehdihadeli/awesome-software-architecture](https://github.com/mehdihadeli/awesome-software-architecture) | Comprehensive architecture resources including DDD section |
| [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer) | System design fundamentals with microservices patterns |

## 📝 Engineering Blogs

| Article | Source |
|---|---|
| [How Netflix Scales Data Architecture](https://netflixtechblog.com/) | Netflix Tech Blog |
| [LinkedIn's DataHub](https://engineering.linkedin.com/blog/topic/datahub) | LinkedIn Engineering |
| [Uber's Domain-Oriented Microservice Architecture](https://eng.uber.com/microservice-architecture/) | Uber Engineering |
| [Airbnb's Data Quality](https://medium.com/airbnb-engineering) | Airbnb Engineering |

## 🔗 Cross-References in This Curriculum

| Related Concept | Path | Connection |
|---|---|---|
| Event Storming | [../01_Event_Storming](../01_Event_Storming/) | ES Phase 3 discovers BC boundaries |
| Polymorphism Trap | [../03_Polymorphism_Trap](../03_Polymorphism_Trap/) | Polymorphism often spans BC boundaries — a red flag |
| Conformed Dimensions | [../../02_Dimensional_Modeling_Advanced/04_Conformed_Dimensions](../../02_Dimensional_Modeling_Advanced/04_Conformed_Dimensions/) | How BCs are bridged in the DW |
| Data Mesh Domains | [../../../../09_Data_Governance_Metadata/04_Data_Mesh_Architecture/01_Domain_Ownership](../../../../09_Data_Governance_Metadata/04_Data_Mesh_Architecture/01_Domain_Ownership/) | BC = Data Mesh domain |
| Data Contracts | [../../../../09_Data_Governance_Metadata/05_Data_Contracts/01_Specification](../../../../09_Data_Governance_Metadata/05_Data_Contracts/01_Specification/) | Published Language between BCs = Data Contract |
| CDC / Debezium | [../../../../06_Streaming_And_RealTime/04_CDC_Change_Data_Capture/01_Log_Based_Debezium](../../../../06_Streaming_And_RealTime/04_CDC_Change_Data_Capture/01_Log_Based_Debezium/) | Primary integration mechanism between BCs and DW |
| Saga Pattern | [../../../../06_Streaming_And_RealTime/03_Event_Driven_Architecture_Patterns/04_Saga_Pattern](../../../../06_Streaming_And_RealTime/03_Event_Driven_Architecture_Patterns/04_Saga_Pattern/) | How cross-BC transactions work |
