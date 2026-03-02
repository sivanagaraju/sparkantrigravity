# Event Storming — Further Reading & References

> Papers, books, blog posts, conference talks, official documentation, and cross-references.

---

## 📚 Books

| Book | Author | Why |
|---|---|---|
| *Introducing EventStorming* | Alberto Brandolini | The definitive guide by the inventor |
| *Domain-Driven Design* | Eric Evans (2003) | The theoretical foundation — bounded contexts, ubiquitous language |
| *Domain-Driven Design Distilled* | Vaughn Vernon | Shorter, practical DDD introduction (if you can't do Evans' 560 pages) |
| *Implementing Domain-Driven Design* | Vaughn Vernon | Implementation companion — DDD concepts to code and schema |

## 🎤 Talks

| Talk | Speaker | Where |
|---|---|---|
| *50,000 Orange Stickies Later* | Alberto Brandolini | DDD Europe — [YouTube](https://www.youtube.com/watch?v=1i6QYvYhlYQ) |
| *Event Storming for Fun and Profit* | Alberto Brandolini | Explore DDD |
| *From EventStorming to CoDDDing* | Sara Pellegrini & Milan Savic | KanDDDinsky |
| *Modelling Time* | Eric Evans | DDD Europe |

## 🔗 GitHub Repositories

| Repo | Description |
|---|---|
| [ddd-crew/eventstorming-glossary-cheat-sheet](https://github.com/ddd-crew/eventstorming-glossary-cheat-sheet) | Official DDD Crew cheat sheet — printable sticky note color reference |
| [mariuszgil/awesome-eventstorming](https://github.com/mariuszgil/awesome-eventstorming) | Curated list of articles, videos, and tools |
| [ddd-crew/bounded-context-canvas](https://github.com/ddd-crew/bounded-context-canvas) | Canvas template for documenting bounded contexts discovered via Event Storming |
| [ddd-crew/context-mapping](https://github.com/ddd-crew/context-mapping) | Patterns for relationships between bounded contexts |
| [mehdihadeli/awesome-software-architecture](https://github.com/mehdihadeli/awesome-software-architecture) | Comprehensive architecture resources including Event Storming section |

## 📝 Blog Posts & Articles

| Article | Source |
|---|---|
| [A Facilitator's Recipe for Event Storming](https://www.eventstorming.com/) | eventstorming.com (official site) |
| [Event Storming — Remote Edition](https://miro.com/templates/event-storming/) | Miro — official remote template |
| [Event-Driven Architecture at LinkedIn](https://engineering.linkedin.com/blog) | LinkedIn Engineering Blog |
| [How Netflix Uses Domain Events](https://netflixtechblog.com/) | Netflix Tech Blog |

## 🛠 Tools

| Tool | Use Case |
|---|---|
| [Miro](https://miro.com) | Best digital whiteboard for remote Event Storming |
| [FigJam](https://www.figma.com/figjam/) | Good alternative, especially for design-heavy teams |
| [Event Catalog](https://www.eventcatalog.dev/) | Open-source tool to document discovered events as a searchable catalog |
| Physical sticky notes + wall | Still the gold standard for in-person workshops |

## 🔗 Cross-References in This Curriculum

| Related Concept | Path | Connection |
|---|---|---|
| Bounded Contexts | [../02_Bounded_Contexts](../02_Bounded_Contexts/) | Event Storming Phase 3 output defines BC boundaries |
| Polymorphism Trap | [../03_Polymorphism_Trap](../03_Polymorphism_Trap/) | Events reveal entity hierarchies that cause polymorphism issues |
| Event Sourcing | [../../../../06_Streaming_And_RealTime/03_Event_Driven_Architecture_Patterns/01_Event_Sourcing](../../../../06_Streaming_And_RealTime/03_Event_Driven_Architecture_Patterns/01_Event_Sourcing/) | Domain events discovered here become event sourcing events |
| CQRS | [../../../../06_Streaming_And_RealTime/03_Event_Driven_Architecture_Patterns/02_CQRS](../../../../06_Streaming_And_RealTime/03_Event_Driven_Architecture_Patterns/02_CQRS/) | Read models from Event Storming become CQRS projections |
| Data Mesh Domain Ownership | [../../../../09_Data_Governance_Metadata/04_Data_Mesh_Architecture/01_Domain_Ownership](../../../../09_Data_Governance_Metadata/04_Data_Mesh_Architecture/01_Domain_Ownership/) | Bounded contexts map 1:1 to Data Mesh domains |
| Data Contracts | [../../../../09_Data_Governance_Metadata/05_Data_Contracts/01_Specification](../../../../09_Data_Governance_Metadata/05_Data_Contracts/01_Specification/) | Event schemas become formalized data contracts |
| ADRs | [../../../../20_Leadership_Communication/01_Writing_Technical_Vision/04_ADRs](../../../../20_Leadership_Communication/01_Writing_Technical_Vision/04_ADRs/) | Hot spots from Event Storming become ADRs |
