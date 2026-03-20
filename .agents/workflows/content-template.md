---
description: The 8-file content template specification for every topic subfolder
---

# Content Template — 8 Files Per Topic

> Every topic subfolder MUST contain exactly these 8 files. This document specifies the required sections, diagrams, and minimum depth for each file.

---

## File 1: `01_Concept_Overview.md`

### Required Sections

| Section | What To Write | Depth Requirement |
|---|---|---|
| **Why This Exists** | Historical origin story. Name the inventor/creator. State the exact year. What specific problem triggered its creation. What existed before | 1-2 substantial paragraphs with dates and names |
| **What Value It Provides** | Table format. Each row: benefit name + quantified impact. Use real numbers ($, %, latency, throughput) | Table with 4-6 rows, every row has a number |
| **Where It Fits** | Position in the architecture stack. Show relationships to adjacent systems | 1 Mermaid component diagram with ≥3 subgraphs and ≥10 nodes |
| **When To Use / When NOT To Use** | Decision table. Columns: Scenario, Verdict (✅/⚠️/❌), Why/Alternative | Table with 6-8 rows covering both YES and NO scenarios |
| **Key Terminology** | Table of precise definitions | **12-18 terms minimum**. Each: definition + key number + operational significance |

### Required Diagrams
- 1 Component/Context Mermaid diagram showing this concept within the broader system
- Diagram MUST have ≥3 subgraphs, ≥10 nodes, styled nodes where helpful

### Minimum Size: 100 lines

### Quality Gates
- [ ] No vague benefit claims — every row in the value table has a number
- [ ] Decision matrix has explicit "wrong tool" scenarios with named alternatives
- [ ] Key Terminology has 12-18 terms, each with operational significance
- [ ] Component diagram has subgraphs, not just flat nodes

---

## File 2: `02_How_It_Works.md`

### Required Sections

| Section | What To Write | Depth Requirement |
|---|---|---|
| **Architecture** | Internal mechanics: process model, threading, memory layout. Name the actual OS primitives used (epoll, mmap, fork, futex) | Byte-level detail for key structures |
| **Data Structures (Internal)** | The actual structs, fields, and their sizes. Show the C struct or equivalent with byte annotations | ASCII art for layouts + field table |
| **Core Algorithms** | Pseudocode for 2-3 critical algorithms. Not prose — actual step-by-step logic | Pseudocode blocks with comments |
| **HLD** | Mermaid diagram showing major internal components and data flow | 1 HLD diagram (always required) |
| **Sequence Diagrams** | Step-by-step message flow for key operations (write path, read path, recovery) | 1-2 sequence diagrams |
| **State Machine** | State transitions for any lifecycle (compaction, checkpointing, replication) | 1 stateDiagram-v2 (when applicable) |
| **Data Flow** | How data moves through the system stage by stage | 1 DFD or flowchart |
| **Storage Layout** | On-disk or in-memory layout with actual directory/file structure | ASCII tree + page/record layout |

### Required Diagrams (4-6 minimum)
- `graph` — HLD with subgraphs (ALWAYS required)
- `sequenceDiagram` — write path, read path, or replication flow
- `stateDiagram-v2` — lifecycle states (when applicable)
- `graph` — data flow or algorithm flow
- ASCII art — page layout, record format, memory regions

### Required Pseudocode
At least 2-3 core algorithm outlines:
```
function eviction_algorithm(buffer_pool):
    sweep_hand = global_hand_position
    while true:
        slot = buffer_pool[sweep_hand]
        if slot.usage_count > 0:
            slot.usage_count -= 1  // decrement, not evict
            sweep_hand = (sweep_hand + 1) % pool_size
        else if not slot.is_pinned:
            if slot.is_dirty:
                schedule_background_write(slot)
            return slot  // victim found
```

### Required ASCII Art
```
+------------------+-------------------+------------------+
| Header (N bytes) | Payload (variable)| Footer (M bytes) |
+------------------+-------------------+------------------+
| field_1 (4B)     | actual data       | checksum (4B)    |
| field_2 (2B)     |                   | padding (2B)     |
+------------------+-------------------+------------------+
```

### Minimum Size: 200 lines (this is the deepest file)

### Quality Gates
- [ ] ≥ 4 Mermaid diagrams of different types
- [ ] ≥ 2 pseudocode blocks for core algorithms
- [ ] ≥ 1 ASCII art diagram for internal structure
- [ ] Internal data structures shown at byte/field level
- [ ] Actual OS primitives named (epoll, mmap, fork, etc.)
- [ ] No section is just a prose paragraph — all have structured content

---

## File 3: `03_Hands_On_Examples.md`

### Required Sections

| Section | What To Write | Depth Requirement |
|---|---|---|
| **Scenario-Based Examples** | 4-6 hands-on scenarios, each with a real use case title | Full code with comments |
| **Before vs After** | Show the bad approach, then the correct approach | Measurable metric comparison |
| **Code** | Production-grade SQL, Python, PySpark, CLI commands, config files | Not toy examples — real-world scale |
| **Table Structures** | DDL with partitioning, indexing, constraints (for DB topics) | Complete CREATE TABLE with comments |
| **Integration Diagram** | How this concept integrates with surrounding systems | 1-2 Mermaid diagrams |
| **Runnable Steps** | Step-by-step instructions to reproduce on laptop or cloud sandbox | Numbered steps with expected output |

### Before vs After Template (Mandatory)
```markdown
### ❌ Before (Anti-Pattern)
```sql
-- What most people do wrong
SELECT * FROM orders WHERE status = 'pending'; -- full table scan
```
**Result**: Full table scan on 500M rows → 34 seconds, 99% CPU

### ✅ After (Correct Approach)
```sql
-- Correct approach with covering index
CREATE INDEX idx_orders_status_inc ON orders(status) INCLUDE (id, amount);
SELECT id, amount FROM orders WHERE status = 'pending'; -- index-only scan
```
**Result**: Index-only scan → 12ms, <1% CPU
**Why**: Covering index eliminates heap fetches; all required columns are in the index leaf pages
```

### Required Diagrams
- 1-2 integration diagrams showing how this connects to adjacent systems

### Minimum Size: 150 lines

### Quality Gates
- [ ] ≥ 4 hands-on scenarios with real use case titles
- [ ] ≥ 2 before/after comparisons with measurable metrics
- [ ] Code is production-grade, not toy examples
- [ ] Runnable steps with expected output
- [ ] Integration diagram present

---

## File 4: `04_Real_World_Scenarios.md`

### Required Sections

| Section | What To Write | Depth Requirement |
|---|---|---|
| **FAANG Case Studies** | 2-4 real company implementations with architecture decisions | Named companies, specific numbers |
| **Production Numbers** | Records/sec, TB processed, latency percentiles, cost, team size | Exact numbers, not ranges |
| **What Went Wrong** | Post-mortem style: incident → root cause → fix → prevention | 1-2 incident stories |
| **Deployment Topology** | How this is deployed at scale | 1 Mermaid deployment diagram |

### Case Study Template
```markdown
### 01: [Company Name] — [What They Built]
- **Scale**: [specific numbers — records/sec, TB, users]
- **Architecture Decision**: [what they chose and WHY]
- **Trade-Off**: [what they gave up and why it was acceptable]
- **Key Configuration**: [specific settings, versions, hardware]
- **Lesson**: [the non-obvious takeaway]
```

### Required Diagrams
- 1 deployment diagram showing production topology at scale

### Minimum Size: 120 lines

### Quality Gates
- [ ] ≥ 2 named company case studies with scale numbers
- [ ] ≥ 1 post-mortem incident with root cause analysis
- [ ] Deployment diagram with specific infrastructure details
- [ ] Production numbers are exact, not "handles millions of requests"

---

## File 5: `05_Pitfalls_And_Anti_Patterns.md`

### Required Sections

| Section | What To Write | Depth Requirement |
|---|---|---|
| **Anti-Patterns** | 4-6 specific mistakes with code/config examples of the WRONG way | Show the bad code or config |
| **Detection** | How to detect each anti-pattern: queries, metrics, symptoms, monitoring | Diagnostic commands |
| **Fix** | Concrete remediation: code, config changes, migration steps | Show the corrected version |
| **Decision Matrix** | When this concept is the WRONG choice entirely | Table with alternatives |

### Anti-Pattern Template
```markdown
## Anti-Pattern N: [Descriptive Name]

### The Mistake
[1-2 sentences: what people do wrong and WHY they think it's right]

### The Code (Wrong Way)
```[language]
// This looks correct but causes [specific problem]
[bad code or config]
```

### Impact
- **Measured**: [specific degradation — "latency increases from 5ms to 2.3 seconds"]
- **Symptom**: [what you observe in monitoring — "CPU spikes to 100% every 5 minutes"]
- **Detection**: [command or query to detect this — "SELECT ... FROM pg_stat..."]

### The Fix
```[language]
// Correct approach: [why this works]
[good code or config]
```
**Result**: [quantified improvement]
```

### Minimum Size: 120 lines

### Quality Gates
- [ ] ≥ 4 anti-patterns with code examples
- [ ] Each has detection method (command, query, or metric)
- [ ] Each has quantified impact
- [ ] Decision matrix stating when NOT to use this technology at all

---

## File 6: `06_Interview_Angle.md`

### Required Sections

| Section | What To Write | Depth Requirement |
|---|---|---|
| **How This Appears** | System design? Coding? Deep dive? Behavioral? Which companies? | Specific interview formats |
| **Sample Questions** | 3-5 exact questions | Full answer frameworks |
| **Senior vs Principal Answers** | For each question: surface-level vs deep answer | Side-by-side contrast |
| **What They're Really Testing** | Hidden evaluation criteria per question | The actual signal |
| **Follow-Up Questions** | Probing questions interviewers use to test depth | 2-3 per main question |
| **Whiteboard Exercise** | A diagram you draw from memory in 5 minutes | Mermaid diagram as example |

### Question Template
```markdown
### Question N: "[Exact interview question]"

**What they're really testing**: [hidden criteria]

**Senior Answer (Surface)**:
> [2-3 sentence answer hitting key points but missing depth]

**Principal Answer (Deep)**:
> [4-6 sentence answer showing internal mechanics, trade-offs, production experience.
> Includes specific numbers, names design alternatives considered and rejected,
> references a real production incident or design decision]

**Follow-Up Probes**:
1. "What happens when [edge case]?"
2. "How would you monitor [specific metric]?"
3. "What's the trade-off between [option A] and [option B]?"
```

### Required Diagrams
- 1 whiteboard-style Mermaid diagram (what you'd draw in an interview)

### Minimum Size: 120 lines

### Quality Gates
- [ ] ≥ 3 questions with dual Senior/Principal answer frameworks
- [ ] Each question has "what they're really testing" + follow-up probes
- [ ] Whiteboard exercise with Mermaid diagram
- [ ] Numbers and specifics in every principal-level answer

---

## File 7: `07_Further_Reading.md`

### Required Categories (5+ categories, 3+ items each)

| Category | Minimum | What Each Entry Needs |
|---|---|---|
| **Books** | 3 | Title, Author, Key Contribution (which chapter/section is most relevant) |
| **Papers** | 2 | Title, Authors, Year, Key Contribution in 1 sentence |
| **Engineering Blog Posts** | 3 | Company, Title, what it covers, URL if available |
| **Conference Talks** | 2 | Title, Speaker, Event, Year |
| **Official Documentation** | 3 | Specific page/section links (not just the docs homepage) |
| **GitHub Repos** | 2 | Repo name, description, why it's useful |
| **Cross-References** | 2 | Related topics in THIS curriculum with relative paths |

### Minimum Size: 80 lines

### Quality Gates
- [ ] ≥ 5 categories present
- [ ] ≥ 3 items per category
- [ ] Books have chapter references, not just titles
- [ ] Blog posts include company names and what specifically they cover
- [ ] Cross-references link to related topics within this repository

---

## File 8: `08_Mind_Map.md`

### Purpose
A single-page hierarchical compression of Files 01-07. The "60-second recall" file — scannable, dense, Markmap-compatible.

### Format
- Hierarchical Markdown only (H1/H2/H3 + nested bullets)
- NO Mermaid code blocks. Standard Markdown only
- Every line must be scannable — no prose paragraphs

### Required Sections

| Section | Content | Depth |
|---|---|---|
| **How to Use** | 3-4 bullets: revision, application, interview-prep usage | 1 level |
| **🗺️ Theory & Concepts** | From 01 + 02. H3 per concept → definition, mechanism, why, key numbers | 3-4 bullet levels deep |
| **🗺️ Techniques & Patterns** | From 02 + 03. H3 per technique → when, how, failure modes | Include worked examples |
| **🗺️ Hands-On & Code** | From 03. Key code patterns, DDL, config snippets | Referenced not copied |
| **🗺️ Real-World Scenarios** | From 04. H3 per case → trap, scale numbers, fix | 3-part structure |
| **🗺️ Mistakes & Anti-Patterns** | From 05. H3 per mistake → root cause, diagnostic, correction | 3-part structure |
| **🗺️ Interview Angle** | From 06. Key questions, what's really tested | Per question type |
| **🗺️ Assessment & Reflection** | Knowledge check, personal audit questions | Bullet list |

### Content Rules
- **Depth over breadth**: Each H3 must have 3-4 levels of nested bullets
- **Mechanisms, not labels**: Don't just name it — explain HOW in 1-2 bullets
- **Specificity**: Names (Kimball, antirez), numbers (16MB, <10ms P99), products (DynamoDB)
- **Failure modes**: For every technique, state how it goes wrong
- **No prose**: Bullets only. Every line scannable

### Minimum Size: 250 lines

### Quality Gates
- [ ] ≥ 250 lines
- [ ] All 7 sections present (including Assessment & Reflection)
- [ ] 3-4 bullet nesting levels per concept
- [ ] Failure modes stated for techniques
- [ ] Scale numbers present in scenarios
- [ ] Assessment section has personal audit questions
