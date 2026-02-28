# 22 — Interview Preparation

> "A Principal Data Architect interview is not a coding test. It is a 5-hour evaluation of your judgment, communication, and the depth of your technical intuition under pressure."

At the Principal level, interviewers aren't checking if you know Spark. They're checking: Can you design a multi-region data platform in 45 minutes? Can you explain trade-offs to a room of skeptical Staff Engineers? Do you have the leadership stories that demonstrate you've *actually* operated at this scale?

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Behavioral_Deep_Dives/`

- **The STAR Method at L7**: Situation, Task, Action, Result. But at Principal level, interviewers also want: **Alternatives considered**, **People influenced**, **Long-term impact**, and **What you'd do differently**.
- **Leadership Scenarios**: "Tell me about a time you changed the technical direction of an organization." "Tell me about a project that failed and how you handled it." "How did you resolve a disagreement with another Principal?"
- **Influence Stories**: "Describe a time you convinced a VP to cancel a project." "How did you drive adoption of a new architectural standard across 10 teams?"
- **Failure Stories**: Interviewers don't trust candidates who've never failed. Prepare 3-4 genuine failure stories with authentic reflections: What you learned, what changed, what you'd do differently.

### `02_System_Design_Questions/`

- **25 Data Architecture Prompts**: Design a real-time analytics platform. Design a data lakehouse for a 500-person company. Design a CDC pipeline from 50 microservices to a central data warehouse. Design a feature store for ML. Design a multi-region data platform with sub-second failover.
- **The 45-Minute Framework**: Requirements (5 min) → High-Level Architecture (10 min) → Deep Dive on 2 Components (20 min) → Trade-offs & Bottlenecks (10 min). Never start drawing boxes before asking clarifying questions.
- **How to Handle "What About..."**: Interviewers probe your design with challenges. "What if the data volume increases 100x?" "What if the network between regions goes down?" "What if you have a $0 budget?" Practice pivoting gracefully.

### `03_Technical_Deep_Dive_Questions/`

- **Database Internals**: "Explain how MVCC works in PostgreSQL." "What happens inside Snowflake when you run a query — from SQL to result?" "Why is Cassandra eventually consistent and how do you achieve strong consistency when needed?"
- **Distributed Systems**: "Explain the CAP theorem with a concrete example from your experience." "How does Kafka achieve exactly-once semantics?" "What is the difference between Raft and Paxos?"
- **Data Modeling**: "We have a SaaS product with 50 customers who each want custom fields. Design the schema." "Design a bi-temporal data model for a financial trading platform."
- **Performance**: "A query that used to take 5 seconds now takes 5 minutes after we added 10x more data. Walk me through your debugging process." "How would you design the partitioning strategy for a 100TB fact table?"

### `04_Case_Study_Exercises/`

- **The "Current State to Target State" Exercise**: "Here is Company X's current architecture (whiteboard diagram). It has these problems (latency, cost, reliability). Design the target state and the migration plan."
- **The Cost Optimization Exercise**: "Your data platform costs $2M/year. The CFO wants it under $800K. What do you cut and what are the risks?"
- **The Organizational Exercise**: "Three teams own overlapping data pipelines. They disagree on data definitions. How do you resolve this?"

### `05_Compensation_And_Negotiation/`

- **FAANG Compensation Bands (2026)**: Principal/L7 total compensation ranges. Base salary ($250-350K), stock ($300-800K/year vesting), signing bonus, performance multipliers.
- **Leveling Negotiations**: Sometimes you're offered L6 (Staff) instead of L7 (Principal). How to present evidence for the higher level. The "down-level" negotiation technique.
- **Counter-Offer Strategy**: When to negotiate base vs. stock vs. signing bonus. The "exploding offer" tactic and how to manage multiple simultaneous offers.

### `06_Resume_And_Portfolio/`

- **The 2-Page Resume for 20 Years of Experience**: Curate ruthlessly. Only the last 10 years get detail. Earlier roles get one line each. Lead with impact metrics ($, %, scale).
- **Architecture Portfolio**: A personal website or PDF showcasing 5-8 architecture diagrams you designed, the business problem they solved, and the outcomes.
- **GitHub / Open Source Signal**: Contributing to Apache Spark, Iceberg, or Flink. Writing technical blog posts. Speaking at conferences (Data Council, Strata, dbt Coalesce).

---
*Part of [Principal Data Architect Learning Path](../README.md)*
