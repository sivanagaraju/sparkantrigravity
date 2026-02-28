# 20 — Leadership & Communication

> "At the Principal level, the architecture IS the communication. If you can't explain it, you can't build it. If you can't convince people, it doesn't matter how right you are."

Technical brilliance without communication skills caps you at Staff level. Principals influence organizational strategy, mentor the next generation, and shape multi-year technology roadmaps. This domain is the difference between a great engineer and a great leader.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Writing_Technical_Vision_Documents/`

- **The 1-Year, 3-Year, 5-Year Roadmap**: How to write a data platform vision document that the CTO signs off on. Separating the "Now" (tactical), "Next" (strategic), and "Later" (aspirational) horizons.
- **The Amazon 6-Pager**: Narrative, not bullet points. Start with the customer problem, not the technology. Write the press release for your project *before* you build it (Working Backwards).
- **RFC (Request for Comments) Process**: Writing design proposals that invite structured feedback. Sections: Context, Problem Statement, Proposed Solution, Alternatives Considered, Risks, Open Questions.
- **Architecture Decision Records (ADRs)**: Short, dated documents that capture *what* was decided, *why*, and *what alternatives were rejected*. Building an organizational decision log that prevents re-litigating past decisions.

### `02_Stakeholder_Management/`

- **Speaking to the C-Suite**: The CEO cares about revenue impact and risk. The CFO cares about cost. The CTO cares about scalability and tech debt. The CDO cares about compliance. Tailoring the same architecture proposal to four different audiences.
- **The Art of "No"**: Saying no to a VP's pet project without getting fired. Using data (latency, cost, risk) to justify architectural decisions. The "Yes, and..." negotiation technique.
- **Managing Technical Debt Conversations**: Quantifying tech debt in dollars. "Our current ETL architecture costs $500K/month in operational overhead and engineering time. Migrating to X will reduce that to $100K/month within 12 months."

### `03_Building_And_Running_Architecture_Reviews/`

- **The Architecture Review Board (ARB)**: Design reviews for all significant technical decisions. Moving from "gatekeeper" (blocking) to "enabler" (advisory).
- **Lightweight Architecture Decision Flow**: Not every decision needs a formal review. Establishing thresholds: "Changes impacting 3+ teams or costing >$50K require ARB review."
- **Running Effective Design Reviews**: Requiring a written design doc *before* the review meeting. Structured feedback: "I disagree and commit" vs. "This is a blocking concern."

### `04_Mentoring_And_Growing_Engineers/`

- **The Multiplier Effect**: A Principal's greatest impact is turning 5 Senior Engineers into Staff Engineers. Your individual contribution ceiling is 1x; your mentoring ceiling is 10x.
- **Architecture Office Hours**: Weekly open sessions where any engineer can bring an architecture question. Building a culture of architectural thinking across the organization.
- **Giving Hard Feedback**: Telling a senior engineer their design is fundamentally flawed without crushing their motivation. The SBI (Situation, Behavior, Impact) model.

### `05_Vendor_And_Technology_Evaluation/`

- **The POC Framework**: Defining success criteria *before* the proof of concept starts. Measuring on performance, cost, operational burden, and team velocity — not on "how cool is the demo."
- **Build vs. Buy Decision Matrix**: Total Cost of Ownership over 3 years. Including engineering time, hiring difficulty, operational burden, and vendor lock-in risk.
- **Navigating Vendor Sales Cycles**: Understanding that the vendor's Solutions Architect is an expert at making their product look perfect. Designing POCs that expose the product's weaknesses, not just its strengths.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
