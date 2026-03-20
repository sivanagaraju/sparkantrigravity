# Principal Data Architect — Agent Instructions

> **This file is the master instruction set for ANY LLM agent** (Claude, Gemini, GPT, etc.) working on this repository. Read this file FIRST before touching any content.

---

## 1. Repository Purpose

This repository is a **Principal Data Architect knowledge base** — 23 domains, each containing multiple topics, each topic containing exactly **8 Markdown files** following a strict template. The content must be at the level of a **Principal Data Architect with 20+ years at Meta/Amazon/Netflix/Google/Microsoft**.

## 2. Mandatory Pre-Work Before Writing ANY Content

Before generating content for any subfolder, the agent MUST:

1. **Read this file** (`AGENTS.md`) completely
2. **Read the content template** at `.agents/workflows/content-template.md`
3. **Read the quality checklist** at `.agents/workflows/quality-checklist.md`
4. **Read the review workflow** at `.agents/workflows/review-workflow.md`
5. **Do deep internet research** on the specific topic — do NOT rely solely on training data. Search for:
   - Official documentation (latest version)
   - FAANG engineering blog posts (Netflix, Uber, LinkedIn, Airbnb, Meta, Google)
   - Academic papers and conference talks
   - GitHub repositories with high star counts
   - Stack Overflow canonical answers
   - Production incident reports and post-mortems

## 3. Parallelization Strategy

When working on a parent folder with multiple subfolders:

### Step 1: Identify All Subfolders
List all subfolders in the parent directory. Each subfolder = one independent task.

### Step 2: Dispatch Parallel Sub-Agents
- **Each sub-agent works on ONE subfolder** independently
- Sub-agents do NOT share context — each must do its own deep research
- Each sub-agent follows the FULL workflow: Research → Write → Self-Review → Fix

### Step 3: Final Review Pass
After ALL sub-agents complete, do a **cross-cutting review**:
- Verify consistent quality across all subfolders
- Check no subfolder is significantly weaker than others
- Verify cross-references between related topics are present
- Fix any gaps found

### Important Rules for Parallel Work
- **Never rush to finish** — depth matters more than speed
- **Think step-by-step** before writing each file — plan the content structure first
- **Do deep research for EACH topic** — don't assume training data is sufficient
- **Apply lot of thinking** — reason about what a principal architect would actually want to know

## 4. Persona & Tone

**Author**: Principal Data Architect, 20+ years FAANG experience, PhD-level depth

**Audience**: Lead data engineers, platform owners, senior architects

**Tone Rules** (STRICTLY ENFORCED):
- ❌ No motivational fluff. No "In today's fast-paced world..." openings
- ❌ No filler words. Every sentence must earn its place
- ❌ No vague claims ("fast", "efficient", "scalable") without specific numbers
- ✅ Direct, opinionated, technical
- ✅ State trade-offs explicitly. State disagreements with conventional wisdom
- ✅ Assume the reader can read code — don't explain basic syntax
- ✅ Use production numbers everywhere (latency, throughput, cost, memory)

## 5. The 8-File Template

Every topic subfolder MUST contain exactly these 8 files. See `.agents/workflows/content-template.md` for the full specification of each file.

| File | Purpose | Minimum Size |
|---|---|---|
| `01_Concept_Overview.md` | Why it exists, value, positioning, decision matrix, terminology | ≥ 100 lines |
| `02_How_It_Works.md` | Internal architecture, algorithms, data structures, protocols | ≥ 200 lines |
| `03_Hands_On_Examples.md` | Production-grade code, before/after, runnable exercises | ≥ 150 lines |
| `04_Real_World_Scenarios.md` | FAANG case studies, post-mortems, deployment topology | ≥ 120 lines |
| `05_Pitfalls_And_Anti_Patterns.md` | Specific mistakes, detection, remediation, decision matrix | ≥ 120 lines |
| `06_Interview_Angle.md` | Questions, Senior vs Principal answers, whiteboard exercise | ≥ 120 lines |
| `07_Further_Reading.md` | Books, papers, blogs, talks, repos, docs, cross-refs | ≥ 80 lines |
| `08_Mind_Map.md` | Hierarchical compression of files 01-07, Markmap-compatible | ≥ 250 lines |

## 6. Critical Quality Gates (From Gap Analysis)

These are the TOP 10 quality requirements that LLMs commonly fail on. **EVERY file must pass ALL applicable gates**:

### Gate 1: Mermaid Diagrams
- `01_Concept_Overview`: 1 component/context diagram (with subgraphs, styled nodes)
- `02_How_It_Works`: **4-6 diagrams** (HLD, sequenceDiagram, stateDiagram-v2, DFD, activity)
- `03_Hands_On_Examples`: 1-2 integration diagrams
- `04_Real_World_Scenarios`: 1 deployment diagram
- `06_Interview_Angle`: 1 whiteboard-style diagram

### Gate 2: Internal Data Structures (Byte-Level)
- Show header layouts with field names and byte sizes
- Include ASCII art for memory/page/record layouts
- Show struct definitions with bit-level precision where relevant

### Gate 3: Production Numbers
- Every claim must have a specific number (latency, throughput, memory, cost)
- No "fast" or "efficient" without quantification
- Include percentiles (P50, P99, P99.9) where applicable

### Gate 4: Algorithm Pseudocode
- `02_How_It_Works` must have 2-3 core algorithm pseudocode blocks
- Not just prose descriptions — actual step-by-step logic

### Gate 5: Key Terminology (12-18 terms)
- Each definition: what it IS + a key number + why it matters operationally
- Not just dictionary definitions — include operational significance

### Gate 6: ASCII Art for Layouts
- Page structures, memory regions, file formats, protocol frames
- Required for ANY system that has internal binary structures

### Gate 7: Before vs After in Examples
- `03_Hands_On_Examples` must contrast bad approach vs correct approach
- Include measurable metric differences (latency, memory, CPU)

### Gate 8: Comprehensive Further Reading
- 5+ categories, 3+ items per category
- Books with chapter references, papers with key contributions
- FAANG blog posts with specific URLs, conference talks with speaker names

### Gate 9: Interview Depth
- Senior vs Principal answer frameworks for each question
- Follow-up probing questions that interviewers use
- A whiteboard exercise you can draw in 5 minutes

### Gate 10: Mind Map Depth
- 250-400 lines, 7 sections, 3-4 bullet levels per concept
- Must include Assessment & Reflection section
- Failure modes for every technique, scale numbers for scenarios

## 7. Workflow Per Subfolder

```
For each subfolder:
  1. RESEARCH (Deep)
     - Search official docs for latest version details
     - Find 3+ FAANG engineering blog posts
     - Identify key academic papers
     - Look for production incident reports
     - Find GitHub repos and tools
  
  2. THINK (Plan the content)
     - Outline each file's structure BEFORE writing
     - Identify the 3-5 most important internal mechanisms
     - List specific production numbers to include
     - Plan which Mermaid diagram types fit this topic
  
  3. WRITE (Create all 8 files)
     - Follow the content-template.md specification exactly
     - Apply all 10 quality gates from this document
     - Include deep research findings, not just training data
  
  4. SELF-REVIEW (Quality check)
     - Run through quality-checklist.md for every file
     - Verify minimum line counts and diagram counts
     - Check that production numbers are present, not vague claims
     - Ensure before/after examples exist in file 03
  
  5. FIX (Address gaps)
     - If any quality gate fails, rewrite that section
     - Do NOT just add words — add actual depth and detail
     - Adding more words for the same concept is NOT adding depth
```

## 8. What "Deep Research" Means

"Deep research" is NOT:
- ❌ Rephrasing training data in more words
- ❌ Adding adjectives to make prose sound impressive
- ❌ Copying Wikipedia-level summaries

"Deep research" IS:
- ✅ Finding the actual source code or config parameter names
- ✅ Getting the real struct field names and byte sizes from documentation
- ✅ Finding production numbers from FAANG engineering blog posts
- ✅ Understanding the algorithm well enough to write pseudocode
- ✅ Knowing the exact version where a feature was introduced
- ✅ Being able to state WHY a design decision was made (not just WHAT it is)

## 9. What "Adding More Detail" Means

"Adding more detail" is NOT:
- ❌ Adding more words to describe the same concept
- ❌ Rephrasing the same idea 3 different ways
- ❌ Adding introductory context before every section

"Adding more detail" IS:
- ✅ Adding a NEW dimension (e.g., adding byte-level struct layout to a concept)
- ✅ Adding a Mermaid diagram that visualizes the internal flow
- ✅ Adding pseudocode for an algorithm that was only described in prose
- ✅ Adding a production number to a vague claim
- ✅ Adding a before/after comparison with metrics
- ✅ Adding a follow-up interview question with a principal-level answer
