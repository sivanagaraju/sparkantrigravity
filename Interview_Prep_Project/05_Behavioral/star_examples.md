# Behavioral Interview Questions - STAR Method Examples

This document contains behavioral interview questions and structured answers
using the STAR method (Situation, Task, Action, Result).

---

## 1. Leadership & Mentoring

### Q: "Tell me about a time you mentored a junior developer."

**STAR Answer:**

**Situation:**
In my previous role, a junior developer joined our team and was assigned to
write a PySpark job that loaded data from an API.

**Task:**
I was responsible for reviewing their code and helping them become productive.

**Action:**
1. I noticed they used a UDF to call the API for every row.
2. Instead of just fixing it, I scheduled a 30-minute session.
3. I explained WHY it was slow (1M rows = 1M API calls).
4. I showed them the `mapPartitions` pattern as an alternative.
5. I paired with them to refactor the code.

**Result:**
- The job runtime dropped from 3 hours to 20 minutes.
- The junior developer presented the optimization at our team meeting.
- They now mentor others on the same pattern.

**Key Takeaway:**
"I believe in teaching the 'why', not just the 'what'.
This builds long-term capability in the team."

---

## 2. Problem Solving & Optimization

### Q: "Describe a time you optimized a slow data pipeline."

**STAR Answer:**

**Situation:**
Our daily claims processing job was taking 6 hours and often failed
due to memory issues.

**Task:**
I was asked to investigate and reduce the runtime to under 2 hours.

**Action:**
1. I analyzed the Spark UI and found a massive skew on one join key.
2. 90% of claims had `region = 'Global'`, causing a single executor to OOM.
3. I implemented the "salting" technique:
   - Added a random suffix (0-9) to the skewed key
   - Exploded the small dimension table to match
   - Joined on the salted key
4. I also enabled Adaptive Query Execution (AQE) for future-proofing.

**Result:**
- Runtime dropped from 6 hours to 45 minutes.
- No more OOM failures.
- The pattern was documented and reused in 3 other jobs.

**Key Takeaway:**
"I always investigate the root cause rather than just adding more resources."

---

## 3. Handling Failure & Pressure

### Q: "Tell me about a time a critical job failed in production. How did you handle it?"

**STAR Answer:**

**Situation:**
During quarterly close, our finance data pipeline failed at 2 AM.
The business needed the data by 6 AM for reporting.

**Task:**
I was on-call and had to diagnose and fix the issue within 4 hours.

**Action:**
1. Checked the logs and found the API we depended on was rate-limiting us.
2. I realized our retry logic was too aggressive.
3. Implemented exponential backoff: wait 1s, then 2s, then 4s, etc.
4. Restarted the job with reduced parallelism.
5. Monitored until completion and sent status updates every hour.

**Result:**
- The job finished by 5:30 AM, before the deadline.
- I created a post-mortem document.
- We added monitoring for API rate limits.

**Key Takeaway:**
"Communication during incidents is as important as the fix.
I kept stakeholders informed throughout."

---

## 4. Collaboration & Conflict Resolution

### Q: "Describe a situation where you disagreed with a team member on a technical approach."

**STAR Answer:**

**Situation:**
A colleague wanted to implement real-time streaming for claims data.
I believed batch processing was more appropriate for our use case.

**Task:**
We needed to reach a decision that balanced technical merit with business needs.

**Action:**
1. I created a comparison document:
   - Streaming: Complex, requires Kafka, higher cost, sub-second latency
   - Batch: Simpler, uses existing infrastructure, 15-minute latency
2. I invited the colleague to a whiteboard session to discuss trade-offs.
3. We consulted with the Product Owner about latency requirements.
4. The PO confirmed 15-minute latency was acceptable.

**Result:**
- We went with batch processing.
- Saved ~$50K/year in infrastructure costs.
- The colleague and I remained good collaborators.

**Key Takeaway:**
"I focus on data-driven decisions and involve stakeholders to resolve disagreements."

---

## 5. Innovation & Continuous Learning

### Q: "How do you stay current with technology?"

**STAR Answer:**

**Situation:**
When Delta Lake 2.0 was released, I saw it had features that could
improve our Merge operations significantly.

**Task:**
I wanted to evaluate if we should upgrade.

**Action:**
1. Read the release notes and watched the Databricks Summit talks.
2. Set up a sandbox environment to test the new features.
3. Created a benchmark comparing our current Merge performance vs. Delta 2.0.
4. Presented findings to the team with a migration plan.

**Result:**
- Merge operations became 3x faster.
- We adopted Delta 2.0 across all production jobs.

**Key Takeaway:**
"I proactively test new technologies in sandboxes before recommending them."

---

## 6. DevOps & Ownership

### Q: "How do you ensure the code you write is production-ready?"

**STAR Answer:**

**Situation:**
At my previous company, we had a "you build it, you run it" culture.

**Task:**
I needed to ensure my PySpark jobs were reliable in production.

**Action:**
My checklist before deploying:
1. **Unit Tests**: 80%+ coverage, mocked external dependencies
2. **Integration Tests**: Run against staging data
3. **Logging**: Structured logs with job ID, timestamps, row counts
4. **Monitoring**: Dashboards for duration, error rate, data volume
5. **Runbook**: Documentation for on-call engineers

**Result:**
- My jobs had <1% failure rate.
- When failures did occur, they were fixed within SLA.

**Key Takeaway:**
"Production-readiness starts at design, not after deployment."

---

## 7. Insurance Domain Specific

### Q: "Do you have experience in the insurance or finance domain?"

**STAR Answer (if applicable):**

**Situation:**
I worked on claims processing systems where data accuracy was critical.

**Task:**
Implement an ETL pipeline that generated financial reports for auditors.

**Action:**
1. Implemented reconciliation checks: source row count vs. target row count.
2. Added checksum validation for monetary fields.
3. Created audit trails: who changed what and when.
4. Worked with the finance team to understand IFRS reporting requirements.

**Result:**
- Zero audit findings related to data quality.
- Improved stakeholder confidence in our data.

**Key Takeaway (if no insurance experience):**
"While I haven't worked in insurance specifically, I've worked with
financial data where accuracy and auditability are equally critical.
I'm a quick learner and excited to understand the reinsurance domain."

---

## 8. Questions to Ask the Interviewer

1. "What does a typical day look like for someone in this role?"
2. "How does the team handle production incidents?"
3. "What are the biggest technical challenges the team is facing right now?"
4. "How do you measure success for this role in the first 6 months?"
5. "What's the team's approach to learning and professional development?"

---

## Quick Reference: The STAR Framework

| Component | Description | Example |
|-----------|-------------|---------|
| **S**ituation | Set the context | "During quarterly close..." |
| **T**ask | Your responsibility | "I was asked to investigate..." |
| **A**ction | What YOU did (use "I") | "I analyzed the Spark UI..." |
| **R**esult | Quantifiable outcome | "Runtime dropped from 6h to 45m" |

**Tips:**
- Always use "I" not "we" to show YOUR contribution
- Quantify results when possible
- Keep answers to 2-3 minutes
- Prepare 5-7 stories that can be adapted to different questions
