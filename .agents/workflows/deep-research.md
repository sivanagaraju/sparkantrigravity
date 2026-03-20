---
description: Deep research methodology for every topic before content generation
---

# Deep Research Workflow — How To Research Like a Principal Architect

> This workflow ensures every topic benefits from thorough research BEFORE writing. Do NOT skip this — it's the difference between shallow tutorial content and principal-grade knowledge.

---

## The Problem This Solves

LLMs commonly fail by:
- Relying solely on training data (which may be outdated or shallow)
- Generating plausible-sounding but imprecise content
- Missing internal implementation details that only source code or docs reveal
- Using vague phrases ("fast", "efficient") instead of production numbers
- Missing newer features, versions, or changes since training cutoff

## Research Mandate

For EVERY topic subfolder, the agent MUST:

### Phase 1: Official Sources (Do First)
1. **Official Documentation**: Search for the latest docs of this technology
   - Find specific config parameter names and defaults
   - Find internal architecture pages
   - Find version history / changelog for recent changes
2. **Source Code** (where accessible): Look for struct definitions, algorithm implementations
   - Redis: antirez's GitHub repo — find the actual `redisObject` struct
   - PostgreSQL: src/include/access/ for page layout headers
   - Kafka: look at the actual log segment format

### Phase 2: Industry Sources
3. **FAANG Engineering Blogs**: Search for posts from these blogs specifically:
   - Netflix Tech Blog
   - Uber Engineering Blog
   - LinkedIn Engineering Blog
   - Meta (Facebook) Engineering Blog  
   - Airbnb Engineering & Data Science
   - Twitter (X) Engineering
   - Pinterest Engineering
   - Shopify Engineering
   - Stripe Engineering
4. **AWS/GCP/Azure Architecture Blogs**: Cloud provider best practices
5. **Conference Talks**: Search YouTube for talks at:
   - Strange Loop, QCon, VLDB, SIGMOD
   - PGConf, RedisConf, Kafka Summit
   - re:Invent, Google Cloud Next, KubeCon

### Phase 3: Academic & Foundational
6. **Academic Papers**: Find the original papers that define the concept
   - Use Google Scholar or arXiv
   - Get title, authors, year, key contribution
7. **Books**: Identify the definitive books on this topic
   - Find specific chapter numbers relevant to this concept
8. **Jepsen Tests**: For any distributed system, check jepsen.io results

### Phase 4: Community Intelligence
9. **Stack Overflow**: Find the highest-voted canonical answers
   - These reveal common mistakes and real practitioner concerns
10. **GitHub**: Find repos related to this topic
    - awesome-* lists, benchmark repos, migration tools
11. **Post-Mortems**: Search for public post-mortems involving this technology
    - Focus on root cause and fix, not just "it went down"

---

## Research Output Template

After research, document findings as mental notes before writing:

```
TOPIC: [Name]
CREATOR: [Person/Company], [Year]
ORIGINAL PROBLEM: [What triggered its creation]

KEY MECHANISMS:
1. [Internal mechanism 1] — [how it works at byte level]
2. [Internal mechanism 2] — [algorithm name + complexity]
3. [Internal mechanism 3] — [data structure + trade-off]

PRODUCTION NUMBERS:
- Latency: [P50, P99]
- Throughput: [ops/sec, records/sec]
- Memory: [per-connection, per-item overhead]
- Storage: [compression ratio, page size]

FAANG USAGE:
- [Company 1]: [what they use it for, at what scale]
- [Company 2]: [architecture decision, why they chose this]

COMMON MISTAKES:
1. [Mistake] → [Impact] → [Fix]
2. [Mistake] → [Impact] → [Fix]

STRUCT DEFINITIONS:
- [key struct 1]: fields + byte sizes
- [key struct 2]: fields + byte sizes

ALGORITHM PSEUDOCODE CANDIDATES:
1. [Algorithm 1]: [what it does, worth showing as pseudocode]
2. [Algorithm 2]: [what it does, worth showing as pseudocode]
```

---

## Thinking Process Per File

Before writing EACH of the 8 files, think through:

### For `01_Concept_Overview.md`:
- "What year and who created this? What problem were they solving?"
- "What are the top 5 measurable benefits I can quantify?"
- "What architecture diagram best shows where this fits?"
- "What are the explicit WRONG scenarios for this technology?"
- "What 12-15 terms would a principal architect use daily?"

### For `02_How_It_Works.md`:
- "What are the 3-5 most important internal data structures?"
- "What does the struct/class look like at byte level?"
- "Which algorithms deserve pseudocode (not just prose)?"
- "What Mermaid diagram types best explain the flow? (sequence? state? DFD?)"
- "What does the page/record/message format look like as ASCII art?"

### For `03_Hands_On_Examples.md`:
- "What's the most common mistake that a before/after can show?"
- "What production-grade code would a principal write?"
- "How does this integrate with surrounding systems?"
- "What would a reproducible lab exercise look like?"

### For `04_Real_World_Scenarios.md`:
- "Which FAANG companies use this and what specific scale?"
- "What post-mortem or incident involved this technology?"
- "What does the production deployment topology look like?"

### For `05_Pitfalls_And_Anti_Patterns.md`:
- "What mistake have I seen most in production code?"
- "How would a DBA or SRE detect this mistake?"
- "What's the specific performance impact?"
- "When is this technology the WRONG choice entirely?"

### For `06_Interview_Angle.md`:
- "What would a FAANG interviewer ask about this?"
- "What separates a senior from a principal answer?"
- "What diagram would I draw on a whiteboard?"
- "What follow-up would probe for real depth?"

### For `07_Further_Reading.md`:
- "What's THE definitive book? Which chapter specifically?"
- "What FAANG blog posts cover this best?"
- "What related topics in this curriculum should cross-reference?"

### For `08_Mind_Map.md`:
- "What's the most important thing to remember from each file?"
- "Can I compress a concept into 3-4 nested bullets?"
- "What audit questions would test my real understanding?"

---

## Time Investment Per Topic

Research should take meaningful effort. A rough guide:

| Phase | Expected Effort |
|---|---|
| Official docs research | Deep — find struct definitions, param names |
| FAANG blog search | Find 3+ relevant posts |
| Production numbers | Find 5+ specific numbers |
| Academic papers | Identify 2+ foundational papers |
| Anti-patterns | Identify 4+ from community sources |
| **Total before writing** | Substantial — research is 40% of the work |
