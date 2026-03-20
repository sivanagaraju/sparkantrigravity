---
description: Review workflow to verify and fix content quality after initial generation
---

# Review Workflow — Post-Generation Quality Assurance

> Run this workflow AFTER all files in a subfolder (or set of subfolders) are generated. This is the final gate before marking work as complete.

---

## Phase 1: Automated Size Verification

For each file in the subfolder, check the file size:

| File | Minimum Lines | Minimum KB |
|---|---|---|
| `01_Concept_Overview.md` | 100 | 5 KB |
| `02_How_It_Works.md` | 200 | 10 KB |
| `03_Hands_On_Examples.md` | 150 | 8 KB |
| `04_Real_World_Scenarios.md` | 120 | 6 KB |
| `05_Pitfalls_And_Anti_Patterns.md` | 120 | 6 KB |
| `06_Interview_Angle.md` | 120 | 6 KB |
| `07_Further_Reading.md` | 80 | 4 KB |
| `08_Mind_Map.md` | 250 | 8 KB |

**Action**: If any file is below minimum, it MUST be rewritten with additional depth. NOT by adding filler — by adding new dimensions of content (diagrams, pseudocode, ASCII art, production numbers).

---

## Phase 2: Diagram Count Verification

Count the Mermaid diagrams (` ```mermaid ` blocks) and ASCII art blocks in each file:

| File | Minimum Mermaid | Minimum ASCII Art |
|---|---|---|
| `01_Concept_Overview.md` | 1 | 0 |
| `02_How_It_Works.md` | 4 | 1 |
| `03_Hands_On_Examples.md` | 1 | 0 |
| `04_Real_World_Scenarios.md` | 1 | 0 |
| `06_Interview_Angle.md` | 1 | 0 |

**Action**: If diagram count is below minimum, add the missing diagrams. Choose the type based on what's missing:
- Missing HLD → add a `graph` with subgraphs
- Missing flow → add a `sequenceDiagram`
- Missing lifecycle → add a `stateDiagram-v2`
- Missing internal structure → add ASCII art

---

## Phase 3: Vague Language Scan

Search each file for these forbidden phrases. Each occurrence must be replaced:

| Forbidden Phrase | Replace With |
|---|---|
| "fast" | Specific latency: "P99 < 5ms" |
| "efficient" | Specific metric: "10x compression ratio" or "O(log N) lookup" |
| "scalable" | Specific throughput: "handles 500K events/sec per node" |
| "high performance" | Specific benchmark: "3.2M ops/sec on c5.xlarge" |
| "easily" | Remove, or explain the actual steps |
| "simply" | Remove, or explain why it's actually simple |
| "just" | Remove, or explain what's really involved |
| "important" | Explain WHY — the consequence of not doing it |
| "In today's..." | Delete the entire sentence |
| "As we all know..." | Delete and start with the fact directly |

---

## Phase 4: Depth Spot Check

For each file, read the first 30 lines and the last 30 lines. Check:

1. **Does the opening go deep immediately?** (No throat-clearing, no definitions of basics)
2. **Does the ending provide unique value?** (Not just a summary of what was already said)
3. **Are there byte-level details?** (Struct fields, page layouts, record formats)
4. **Are there production numbers?** (Not just "at scale" — actual numbers)

---

## Phase 5: Cross-Subfolder Comparison

If multiple subfolders were populated in the same session:

1. **Size variance**: No subfolder should be >30% smaller than the largest
2. **Depth variance**: If one subfolder has pseudocode and ASCII art, all should
3. **Cross-references**: Check that `07_Further_Reading.md` in each subfolder links to related subfolders

---

## Phase 6: Missing Content Identification

For each subfolder, check for commonly missed content:

### In `01_Concept_Overview.md`:
- [ ] Creator name and year mentioned?
- [ ] ≥ 12 terminology entries?
- [ ] "When NOT To Use" section with named alternatives?

### In `02_How_It_Works.md`:
- [ ] Pseudocode present (not just prose)?
- [ ] Internal data structures at byte level?
- [ ] ≥ 4 different Mermaid diagram types?
- [ ] Storage/memory layout with ASCII art?

### In `03_Hands_On_Examples.md`:
- [ ] Before/After comparisons with metrics?
- [ ] Code is production-grade (not hello-world)?

### In `04_Real_World_Scenarios.md`:
- [ ] Named company case studies (not generic "a large company")?
- [ ] Specific scale numbers (not "millions")?
- [ ] Post-mortem with root cause analysis?

### In `05_Pitfalls_And_Anti_Patterns.md`:
- [ ] Detection methods (commands/queries) for each anti-pattern?
- [ ] Quantified impact for each mistake?

### In `06_Interview_Angle.md`:
- [ ] Senior vs Principal dual answer frameworks?
- [ ] Follow-up probing questions?
- [ ] Whiteboard Mermaid diagram?

### In `07_Further_Reading.md`:
- [ ] ≥ 5 categories with ≥ 3 items each?
- [ ] Books have chapter references?
- [ ] Cross-references to this curriculum?

### In `08_Mind_Map.md`:
- [ ] Assessment & Reflection section present?
- [ ] ≥ 250 lines?
- [ ] 3-4 bullet nesting levels?

---

## Phase 7: Fix

For every gap identified in Phases 1-6:

1. **Do NOT just add words** — add a new dimension of content
2. **Do NOT rephrase existing content** — add something new
3. **Options for adding depth**:
   - Add a Mermaid diagram (sequenceDiagram, stateDiagram-v2, graph with subgraphs)
   - Add ASCII art for a data structure
   - Add pseudocode for an algorithm
   - Add a production number with source attribution
   - Add a before/after comparison with metrics
   - Add an additional interview question with dual answer framework
   - Add an additional anti-pattern with detection method
   - Add a FAANG case study with scale numbers

---

## Phase 8: Final Sign-Off

After all fixes are applied, verify ONCE MORE:

- [ ] All 8 files exist
- [ ] All files meet minimum size requirements
- [ ] Diagram counts are met
- [ ] No vague language survives
- [ ] Cross-subfolder consistency is maintained
- [ ] The work is DONE — not "good enough"
