# Event Storming — Interview Angle

> How this topic appears in Principal-level interviews. Sample questions, strong answer frameworks, what interviewers are really testing.

---

## How Event Storming Appears in Principal Interviews

Event Storming itself is rarely asked about directly. Instead, it appears as a **technique you volunteer** when answering system design and situational questions. Using it correctly signals that you think about business domains before jumping to technical solutions — the hallmark of a Principal-level architect.

---

## Question 1: The Greenfield Design

> **"You're joining a new company as Principal Data Architect. The existing data warehouse is a mess — 500 tables, no documentation, conflicting definitions across teams. How do you start?"**

### Weak Answer (Senior-level)

"I would audit the existing tables, run profiling queries, interview the DBA, and create an ER diagram."

### Strong Answer (Principal-level)

"I would **not** start by looking at the existing schema. I'd start by running Event Storming workshops with each business domain team — Product, Finance, Operations, Customer Support.

First, I'd run a 2-hour Big Picture session to understand what *actually happens* in the business, expressed as domain events. This reveals the real bounded contexts — which may not match the current table structure at all.

The Event Storming output gives me:

- **Domain events** → Fact table candidates
- **Aggregates** → Dimension candidates
- **Bounded contexts** → Data Mesh domain boundaries
- **Hot spots** → Schema design decisions I need to resolve via ADRs

Only *after* understanding the domain would I map the existing 500 tables against the discovered model. I'd expect to find that 200 of those tables are redundant, 100 have conflicting definitions, and 50 are missing. That gap analysis becomes my migration roadmap."

### What the Interviewer Is Testing

- ✅ You start from **business understanding**, not technical spelunking
- ✅ You know how to **facilitate cross-functional collaboration**
- ✅ You have a structured methodology, not "I'll figure it out"
- ✅ You can derive technical architecture from business processes

---

## Question 2: The Domain Disagreement

> **"Two teams — Marketing and Finance — use the same term 'customer' but define it differently. Marketing counts anyone who signed up; Finance counts anyone who completed a purchase. How do you resolve this?"**

### Strong Answer Using Event Storming

"This is a classic bounded context problem. In Event Storming terms, Marketing's 'customer' is a user who triggered `Customer Registered`, while Finance's 'customer' is one who triggered `Order Confirmed` + `Payment Captured`.

I'd resolve this by:

1. Running a focused Event Storming session with both teams to map the full customer lifecycle
2. Identifying that there are actually three bounded contexts: Acquisition (Marketing), Transaction (Finance), and Engagement (Product)
3. Creating a shared data contract with explicit definitions:
   - `prospect` = registered but no purchase
   - `customer` = at least one completed purchase  
   - `active_customer` = purchase within last 12 months
4. Publishing these as conformed dimensions in the data catalog with clear SLAs"

### What This Tests

- ✅ You resolve semantic conflicts through structured discovery, not authority
- ✅ You know bounded contexts and ubiquitous language (DDD concepts)
- ✅ You produce data contracts, not just verbal agreements

---

## Question 3: The Microservices Data Challenge

> **"We have 50 microservices, each with its own database. We need a unified analytics platform. Where do you start?"**

### Strong Answer

"50 microservices means 50 potential bounded contexts. Before I design any CDC pipeline or data warehouse schema, I need to understand which bounded contexts are truly distinct and which overlap.

I'd facilitate an Event Storming workshop covering the key user journeys end-to-end. The event timeline will show me:

- Which services emit events that logically belong together
- Where the same entity (e.g., 'user', 'order') is defined differently across services
- Which events are the critical ones for analytics vs. operational noise

From this, I'd design:

- CDC pipelines (Debezium) for the 10-15 services that own core business events
- A Kafka topic namespace per bounded context
- Conformed dimensions that bridge the semantic gaps between services
- A Data Mesh structure where each domain team owns their data products"

---

## Question 4: Handling Pushback

> **"Your VP says Event Storming sounds like a waste of time. 'Just look at the database schema.' How do you respond?"**

### Strong Answer

"I'd say: 'The database schema tells us how data is *stored*, not what the business *does*. Let me share a concrete example: At Amazon, the single `orders` table had 300 columns because five different teams kept adding their fields. An Event Storming session revealed that "Order" was actually five bounded contexts — Cart, Payment, Fulfillment, Returns, and Customer Service — each with different lifecycles and requirements. Splitting them improved query performance 10-50x and reduced cross-team conflicts.'

Then I'd offer a compromise: 'Give me 2 hours with the team. If the session doesn't surface at least 3 insights we didn't know about the domain, I'll buy everyone lunch.'"

---

## Follow-Up Questions to Prepare For

| Question | Key Points for Your Answer |
|---|---|
| "How long does Event Storming take?" | Big Picture: 2-4 hours. Design Level: 4-8 hours. Start Big Picture always |
| "What if domain experts disagree?" | That's a hot spot — the most valuable output. Document both views. Create an ADR |
| "Can you do Event Storming remotely?" | Yes, Miro or FigJam. Less effective than in-person but workable. Use breakout rooms |
| "How does this differ from requirements gathering?" | Requirements gathering asks "what do you want?" — Event Storming discovers "what actually happens?" (including things people forget to mention) |
| "What's the output?" | A photographed/exported event timeline, list of bounded contexts, aggregates, policies, hot spots — the raw material for every data model decision |
