---
description: Quality checklist to verify every file meets principal-grade standards before marking it complete
---

# Quality Checklist — Per File Verification

> Run this checklist on EVERY file before marking it complete. A file that fails ANY gate must be rewritten.

---

## Universal Gates (Apply to ALL 8 files)

- [ ] **No filler**: Every sentence earns its place. No "In today's world..." openings
- [ ] **No vague claims**: Search for words "fast", "efficient", "scalable", "good", "bad", "important" — each must be replaced with a specific number or removed
- [ ] **Correct Markdown**: Headers, tables, code blocks all render correctly
- [ ] **No orphan sections**: Every H2/H3 header has substantial content underneath (not just 1 sentence)
- [ ] **Opinionated tone**: The author states trade-offs and opinions, not just lists options

---

## File-Specific Gates

### `01_Concept_Overview.md`

| Gate | Check | Pass? |
|---|---|---|
| Historical origin | Names the creator, year, and original problem | [ ] |
| Value table | ≥ 4 rows, every row has a quantified impact number | [ ] |
| Component diagram | 1 Mermaid diagram with ≥ 3 subgraphs, ≥ 10 nodes | [ ] |
| Decision matrix | ≥ 6 rows, includes ❌ wrong-tool scenarios with named alternatives | [ ] |
| Key terminology | ≥ 12 terms. Each: definition + number + operational significance | [ ] |
| File size | ≥ 100 lines | [ ] |

### `02_How_It_Works.md`

| Gate | Check | Pass? |
|---|---|---|
| Architecture section | Shows internal mechanics at byte/field level | [ ] |
| Mermaid diagrams | ≥ 4 diagrams of ≥ 2 different types (graph, sequenceDiagram, stateDiagram-v2) | [ ] |
| Pseudocode | ≥ 2 algorithm pseudocode blocks with step-by-step logic | [ ] |
| ASCII art | ≥ 1 memory/page/record layout diagram | [ ] |
| Data structure internals | Shows struct fields with byte sizes or bit-level precision | [ ] |
| Storage layout | Shows on-disk or in-memory directory/file structure | [ ] |
| File size | ≥ 200 lines | [ ] |

### `03_Hands_On_Examples.md`

| Gate | Check | Pass? |
|---|---|---|
| Scenarios | ≥ 4 hands-on scenarios with real use case titles | [ ] |
| Before/After | ≥ 2 bad-vs-good comparisons with measurable metric differences | [ ] |
| Production-grade code | Not toy examples — real-world scale, proper error handling | [ ] |
| Integration diagram | ≥ 1 Mermaid diagram showing system integration | [ ] |
| Runnable steps | Numbered steps with expected output | [ ] |
| File size | ≥ 150 lines | [ ] |

### `04_Real_World_Scenarios.md`

| Gate | Check | Pass? |
|---|---|---|
| Case studies | ≥ 2 named FAANG/company cases with specific scale numbers | [ ] |
| Production numbers | Records/sec, TB, latency percentiles (not ranges or vague claims) | [ ] |
| Post-mortem | ≥ 1 incident story: incident → root cause → fix → prevention | [ ] |
| Deployment diagram | 1 Mermaid diagram showing production topology | [ ] |
| File size | ≥ 120 lines | [ ] |

### `05_Pitfalls_And_Anti_Patterns.md`

| Gate | Check | Pass? |
|---|---|---|
| Anti-patterns | ≥ 4 specific mistakes with code/config of the WRONG way | [ ] |
| Detection methods | Each has a diagnostic command, query, or metric to detect it | [ ] |
| Quantified impact | Each states the specific degradation caused | [ ] |
| Remediation | Each shows the corrected code/config | [ ] |
| Decision matrix | States when to NOT use this technology at all | [ ] |
| File size | ≥ 120 lines | [ ] |

### `06_Interview_Angle.md`

| Gate | Check | Pass? |
|---|---|---|
| Interview format | States specific formats (system design, coding, deep dive) | [ ] |
| Questions | ≥ 3 exact questions with dual answer frameworks | [ ] |
| Senior vs Principal | Both levels provided for each question | [ ] |
| Hidden criteria | "What they're really testing" for each question | [ ] |
| Follow-up probes | 2-3 follow-up questions per main question | [ ] |
| Whiteboard exercise | 1 Mermaid diagram you'd draw in an interview | [ ] |
| File size | ≥ 120 lines | [ ] |

### `07_Further_Reading.md`

| Gate | Check | Pass? |
|---|---|---|
| Categories | ≥ 5 different categories (Books, Papers, Blogs, Talks, Docs, Repos, Cross-refs) | [ ] |
| Items per category | ≥ 3 items per category | [ ] |
| Book specificity | Chapter/section references, not just titles | [ ] |
| Blog specificity | Company name + what specifically it covers | [ ] |
| Cross-references | ≥ 2 links to related topics within this curriculum | [ ] |
| File size | ≥ 80 lines | [ ] |

### `08_Mind_Map.md`

| Gate | Check | Pass? |
|---|---|---|
| Sections | All 7 sections present (Theory, Techniques, Hands-On, Scenarios, Mistakes, Interview, Assessment) | [ ] |
| Depth | 3-4 bullet nesting levels per H3 concept | [ ] |
| Format | Bullets only — no prose paragraphs. Every line scannable | [ ] |
| Specificity | Includes names, numbers, and product references | [ ] |
| Failure modes | Stated for every technique in the Techniques section | [ ] |
| Assessment section | Personal audit questions present | [ ] |
| File size | ≥ 250 lines | [ ] |
| No Mermaid | Standard Markdown only (for Markmap compatibility) | [ ] |

---

## Cross-File Consistency Checks

For each subfolder, after all 8 files are written:

- [ ] **Terminology consistent**: Same terms used across all files (no switching between synonyms)
- [ ] **Diagrams complement each other**: No duplicate diagrams, each adds a new perspective
- [ ] **Production numbers consistent**: If file 01 says "100K TPS", file 04 doesn't say "millions of ops"
- [ ] **Mind map covers all files**: Every major topic from files 01-07 appears in file 08
- [ ] **Anti-patterns in file 05 have corresponding "before" examples in file 03**
- [ ] **Interview questions in file 06 test knowledge from files 01-02**

---

## Cross-Subfolder Consistency Checks

When multiple subfolders under the same parent are complete:

- [ ] **No subfolder is significantly smaller** than others (max 30% size variance)
- [ ] **Consistent diagram quality** across subfolders
- [ ] **Cross-references present** between related subfolders
- [ ] **Consistent depth** — if PostgreSQL has byte-level struct details, MySQL must too
