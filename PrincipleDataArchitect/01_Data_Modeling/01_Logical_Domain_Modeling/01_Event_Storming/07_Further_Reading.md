# Event Storming — Further Reading & References

> Papers, books, blog posts, conference talks, official documentation, and cross-references to related concepts in this curriculum.

---

## 📚 Essential Books

| Book | Author | Why You Should Read It |
|---|---|---|
| **Introducing EventStorming** | Alberto Brandolini | The definitive guide by the inventor. Covers Big Picture, Process Modeling, and Design Level in depth |
| **Domain-Driven Design** | Eric Evans | The theoretical foundation. Bounded Contexts, Ubiquitous Language, and Aggregates — the concepts that Event Storming operationalizes |
| **Domain-Driven Design Distilled** | Vaughn Vernon | A shorter, more practical introduction to DDD concepts. Good if you don't have time for Evans' 560 pages |
| **Implementing Domain-Driven Design** | Vaughn Vernon | The implementation companion to Evans. Shows how DDD concepts translate to code and data models |

---

## 🎤 Conference Talks

| Talk | Speaker | Event | Key Takeaway |
|---|---|---|---|
| "50,000 Orange Stickies Later" | Alberto Brandolini | DDD Europe | The origin story and evolution of Event Storming after running 100+ workshops |
| "Event Storming for Fun and Profit" | Alberto Brandolini | Explore DDD | Practical tips for facilitating sessions |
| "From EventStorming to CoDDDing" | Sara Pellegrini & Milan Savic | KanDDDinsky | How to go from Event Storming output to actual code/schema implementation |
| "Modelling Time" | Eric Evans | DDD Europe | How temporal concepts (key in data architecture) connect to domain modeling |

---

## 📝 Blog Posts & Articles

- **eventstorming.com** — Official site with free introductory resources and examples
- **"A Facilitator's Recipe for Event Storming"** by Kenny Baas-Schwegler — Step-by-step facilitation guide with real photos
- **"EventStorming Cheat Sheet"** by DDD Crew (GitHub) — Printable color reference for sticky note types
- **"Remote EventStorming"** by Virtual DDD Community — Detailed guide for running sessions in Miro

---

## 🛠 Tools

| Tool | Use Case |
|---|---|
| **Miro** | Best digital whiteboard for remote Event Storming. Has official templates |
| **FigJam** | Figma's whiteboard tool. Good for design-heavy teams |
| **Physical sticky notes + wall** | Still the gold standard. Nothing beats the energy of a room full of people and a 20-foot wall |
| **Event Catalog** | Open-source tool to document discovered events as a searchable catalog |

---

## 🔗 Cross-References in This Curriculum

These are the concepts in this learning path that directly connect to Event Storming:

### Concepts Event Storming Feeds Into

| Related Concept | Path | How It Connects |
|---|---|---|
| **Bounded Contexts** | [02_Bounded_Contexts](../02_Bounded_Contexts/) | Event Storming's Phase 3 output defines bounded context boundaries |
| **Conformed Dimensions** | [../../02_Dimensional_Modeling_Advanced/04_Conformed_Dimensions](../../02_Dimensional_Modeling_Advanced/04_Conformed_Dimensions/) | Shared entities across bounded contexts become conformed dimensions |
| **Data Vault Hubs** | [../../03_Data_Vault_2_0_Architecture/02_Hubs_Links_Satellites](../../03_Data_Vault_2_0_Architecture/02_Hubs_Links_Satellites/) | Aggregates from Event Storming map to Data Vault Hubs |

### Streaming & Event Architecture

| Related Concept | Path | How It Connects |
|---|---|---|
| **Event Sourcing** | [../../../../06_Streaming_And_RealTime/03_Event_Driven_Architecture_Patterns/01_Event_Sourcing](../../../../06_Streaming_And_RealTime/03_Event_Driven_Architecture_Patterns/01_Event_Sourcing/) | Domain events discovered here ARE the events stored in event sourcing |
| **CQRS** | [../../../../06_Streaming_And_RealTime/03_Event_Driven_Architecture_Patterns/02_CQRS](../../../../06_Streaming_And_RealTime/03_Event_Driven_Architecture_Patterns/02_CQRS/) | Read models from Event Storming become CQRS projections |
| **Schema Registry** | [../../../../06_Streaming_And_RealTime/01_Apache_Kafka_Internals/05_Schema_Registry_Compatibility](../../../../06_Streaming_And_RealTime/01_Apache_Kafka_Internals/05_Schema_Registry_Compatibility/) | Each event type becomes an Avro/Protobuf schema in the registry |

### Governance & Architecture

| Related Concept | Path | How It Connects |
|---|---|---|
| **Domain Ownership (Data Mesh)** | [../../../../09_Data_Governance_Metadata/04_Data_Mesh_Architecture/01_Domain_Ownership](../../../../09_Data_Governance_Metadata/04_Data_Mesh_Architecture/01_Domain_Ownership/) | Bounded contexts map to Data Mesh domains |
| **Data Contracts** | [../../../../09_Data_Governance_Metadata/05_Data_Contracts/01_Specification](../../../../09_Data_Governance_Metadata/05_Data_Contracts/01_Specification/) | Event schemas become formalized data contracts |
| **Architecture Decision Records** | [../../../../20_Leadership_Communication/01_Writing_Technical_Vision/04_ADRs](../../../../20_Leadership_Communication/01_Writing_Technical_Vision/04_ADRs/) | Hot spots from Event Storming become ADRs |

---

## 📋 Quick Reference Card

```
EVENT STORMING IN 60 SECONDS:

1. Invite engineers + domain experts + PM (minimum 4 people)
2. Everyone writes Domain Events (past tense) on ORANGE stickies (5 min)
3. Arrange events on a timeline, left to right (10 min)
4. Cluster related events → name the Aggregates (YELLOW) (10 min)
5. Draw boundaries around clusters → Bounded Contexts (10 min)
6. Add Policies (PURPLE), External Systems (RED), Read Models (GREEN)
7. Mark disagreements with ⚡ Hot Spots

OUTPUT: Bounded contexts → data domains → schemas → Kafka topics → Data Mesh
```
