---
description: Workflow for populating content in topic subfolders using parallel sub-agents with deep research
---

# Populate Content — Parallel Sub-Agent Workflow

> Use this workflow when a parent folder with multiple subfolders needs content populated. Each subfolder gets its own sub-agent working independently.

---

## Step 1: Reconnaissance

Read the parent folder and list ALL subfolders:

```
list all subfolders in [parent_folder]
```

For each subfolder, check what files already exist vs what's needed (8 files per subfolder).

---

## Step 2: Read Standards

Before writing ANY content, read these files:
1. `.agents/AGENTS.md` — master instructions
2. `.agents/workflows/content-template.md` — 8-file specification
3. `.agents/workflows/quality-checklist.md` — per-file quality gates

---

## Step 3: Deep Research Phase (Per Subfolder)

For EACH subfolder topic, do deep research BEFORE writing. This is NOT optional.

### Research Checklist:
- [ ] Search for the official documentation (latest version) of this technology/concept
- [ ] Find 3+ engineering blog posts from FAANG companies on this topic
- [ ] Identify the key academic papers or books that define this concept
- [ ] Find real production numbers (latency, throughput, memory) from benchmarks or blog posts
- [ ] Look for production incident reports or post-mortems related to this topic
- [ ] Find notable GitHub repositories or tools
- [ ] Identify the inventor/creator, the year, and the original problem that was solved
- [ ] Find the actual source code struct definitions or config parameter names
- [ ] Identify 4-6 common anti-patterns practitioners encounter

### Research Sources to Always Check:
- Official project documentation (PostgreSQL docs, Redis docs, Kafka docs, etc.)
- Netflix Tech Blog, Uber Engineering, LinkedIn Engineering, Meta Engineering
- AWS Architecture Blog, Google Cloud Blog
- Jepsen test results (for distributed systems)
- StackOverflow canonical answers (highest-voted answers for common questions)

---

## Step 4: Parallel Dispatch

Dispatch ONE sub-agent per subfolder. Each sub-agent:

### Sub-Agent Instructions:
```
You are a sub-agent responsible for creating deep practitioner-level content for the topic: [SUBFOLDER_NAME]

MANDATORY PRE-WORK:
1. Read .agents/AGENTS.md for master instructions
2. Read .agents/workflows/content-template.md for the 8-file specification  
3. Do deep research on [TOPIC] before writing anything

THINKING PROCESS (do this BEFORE writing each file):
1. What are the 3-5 most important internal mechanisms of [TOPIC]?
2. What production numbers can I cite?
3. Which Mermaid diagram types fit best for this topic?
4. What would a principal architect say is the most common mistake?
5. What would distinguish a senior vs principal in an interview about this?

WRITING ORDER:
1. Write 01_Concept_Overview.md (historical context, value table, component diagram, decision matrix, 12+ terms)
2. Write 02_How_It_Works.md (architecture, 4+ diagrams, 2+ pseudocode blocks, ASCII art, byte-level structs)
3. Write 03_Hands_On_Examples.md (4+ scenarios, before/after with metrics, integration diagram)
4. Write 04_Real_World_Scenarios.md (2+ FAANG cases, post-mortem, deployment diagram)
5. Write 05_Pitfalls_And_Anti_Patterns.md (4+ anti-patterns with detection + fix + impact)
6. Write 06_Interview_Angle.md (3+ questions with Senior/Principal answers, whiteboard)
7. Write 07_Further_Reading.md (5+ categories, 3+ items each)
8. Write 08_Mind_Map.md (250+ lines, 7 sections, 3-4 bullet levels)

SELF-REVIEW:
After writing all 8 files, run .agents/workflows/quality-checklist.md against each file.
Fix any failures BEFORE reporting completion.
```

---

## Step 5: Cross-Subfolder Review

After ALL sub-agents complete, do a final cross-cutting review:

### Size Comparison
Compare file sizes across subfolders. If any subfolder's `02_How_It_Works.md` is < 70% the size of the largest, it needs to be enhanced.

### Depth Comparison
Pick the deepest subfolder (usually the first one done). Verify that ALL other subfolders match its:
- Diagram count
- Pseudocode presence
- ASCII art presence
- Terminology count
- Before/after example count

### Cross-References
Verify that `07_Further_Reading.md` in each subfolder references related subfolders.

---

## Step 6: Fix Gaps

For any gaps found in Step 5:
- **Do NOT add words for the same concept** — add NEW dimensions
- **Options**: More diagrams, more pseudocode, more ASCII art, more production numbers, more case studies
- Re-run the quality checklist on fixed files

---

## Step 7: Final Verification

- [ ] All subfolders have exactly 8 files each
- [ ] No file is below minimum size threshold
- [ ] Cross-subfolder consistency is maintained
- [ ] All quality gates pass
- [ ] The work is DONE

---

## Example Dispatch for 4 Subfolders

```
Parent: 02_Database_Systems/06_RDBMS_Deep_Internals/
├── 01_PostgreSQL_Internals/  → Sub-Agent 1
├── 02_MySQL_InnoDB/          → Sub-Agent 2
├── 03_Oracle_Architecture/   → Sub-Agent 3
└── 04_SQL_Server_Internals/  → Sub-Agent 4

Each sub-agent:
  1. Deep research on its specific RDBMS
  2. Write all 8 files following content-template.md
  3. Self-review using quality-checklist.md
  4. Fix gaps

Then: Cross-subfolder comparison → Fix inconsistencies → Final sign-off
```
