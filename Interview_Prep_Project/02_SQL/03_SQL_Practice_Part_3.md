# SQL Practice Questions - Part 3 (Questions 31-37)

This document contains hard difficulty SQL questions with T-SQL solutions.

---

## Database Schema Reference

| Table | Columns |
|-------|---------|
| `patients` | patient_id, first_name, last_name, gender, birth_date, city, province_id, allergies, height, weight |
| `admissions` | patient_id, admission_date, discharge_date, diagnosis, attending_doctor_id |
| `doctors` | doctor_id, first_name, last_name, speciality |
| `province_names` | province_id, province_name |

---

## Q31: Calculate admission costs based on insurance status

### Tables Used

- `patients`, `admissions`

### Hint

Even patient_id = has insurance. Conditional logic for cost.

### Understanding the Problem

- Patients with EVEN patient_id have insurance ($10 per admission)
- Patients with ODD patient_id have no insurance ($50 per admission)
- Group by insurance status and sum costs

### Solution Approach

1. JOIN patients and admissions (cost is per admission)
2. Use modulo to determine even/odd
3. CASE for insurance flag
4. CASE for cost calculation
5. GROUP BY and SUM

### T-SQL Answer

```sql
SELECT 
    CASE 
        WHEN p.patient_id % 2 = 0 THEN 'Yes'
        ELSE 'No'
    END AS has_insurance,
    SUM(
        CASE 
            WHEN p.patient_id % 2 = 0 THEN 10
            ELSE 50
        END
    ) AS total_cost
FROM patients p
INNER JOIN admissions a ON p.patient_id = a.patient_id
GROUP BY CASE WHEN p.patient_id % 2 = 0 THEN 'Yes' ELSE 'No' END;
```

### Why This Approach?

- Two CASE expressions: one for display, one for calculation
- GROUP BY the full CASE expression (required in T-SQL)
- Single pass through joined data

### Alternative Approaches

**Using CTE for clarity:**

```sql
WITH admission_costs AS (
    SELECT 
        p.patient_id,
        IIF(p.patient_id % 2 = 0, 'Yes', 'No') AS has_insurance,
        IIF(p.patient_id % 2 = 0, 10, 50) AS cost
    FROM patients p
    INNER JOIN admissions a ON p.patient_id = a.patient_id
)
SELECT has_insurance, SUM(cost) AS total_cost
FROM admission_costs
GROUP BY has_insurance;
```

- More readable with IIF shorthand

### Common Mistakes

- Counting patients instead of admissions
- Using GROUP BY alias (T-SQL requires the full expression)

---

## Q32: Find provinces with more males than females

### Tables Used

- `patients`, `province_names`

### Hint

Conditional aggregation per gender. Compare counts.

### Understanding the Problem

- Count males and females per province
- Return only provinces where male count > female count

### Solution Approach

1. JOIN patients with province_names
2. Use conditional aggregation to count each gender
3. Filter using HAVING

### T-SQL Answer

```sql
SELECT pn.province_name
FROM patients p
INNER JOIN province_names pn ON p.province_id = pn.province_id
GROUP BY pn.province_name
HAVING SUM(CASE WHEN p.gender = 'M' THEN 1 ELSE 0 END) > 
       SUM(CASE WHEN p.gender = 'F' THEN 1 ELSE 0 END);
```

### Why This Approach?

- Conditional aggregation counts each gender in one pass
- HAVING compares the two sums directly
- No subquery needed

### Alternative Approaches

**Using CTE:**

```sql
WITH gender_counts AS (
    SELECT 
        pn.province_name,
        SUM(IIF(p.gender = 'M', 1, 0)) AS male_count,
        SUM(IIF(p.gender = 'F', 1, 0)) AS female_count
    FROM patients p
    INNER JOIN province_names pn ON p.province_id = pn.province_id
    GROUP BY pn.province_name
)
SELECT province_name
FROM gender_counts
WHERE male_count > female_count;
```

- More readable, easier to debug

### Common Mistakes

- Using WHERE instead of HAVING for aggregate comparison
- Counting all patients instead of by gender

---

## Q33: Complex multi-condition patient filter

### Tables Used

- `patients`

### Hint

Combine LIKE, IN, BETWEEN, and modulo.

### Understanding the Problem

Find patients matching ALL conditions:

- First name has 'r' as 3rd character (`__r%`)
- Gender = 'F'
- Born in Feb, May, or Dec
- Weight 60-80 kg
- Odd patient_id
- City = 'Kingston'

### Solution Approach

1. LIKE with underscores for position
2. MONTH() with IN for birth months
3. BETWEEN for weight range
4. Modulo for odd check
5. Combine with AND

### T-SQL Answer

```sql
SELECT *
FROM patients
WHERE first_name LIKE '__r%'
  AND gender = 'F'
  AND MONTH(birth_date) IN (2, 5, 12)
  AND weight BETWEEN 60 AND 80
  AND patient_id % 2 = 1
  AND city = 'Kingston';
```

### Why This Approach?

- Each condition is clear and testable
- `__r%` means: any char, any char, 'r', then anything
- MONTH() returns integer (2, 5, 12 not '02', '05', '12')

### Alternative Approaches

**Using CHARINDEX:**

```sql
WHERE CHARINDEX('r', first_name) = 3
  -- rest of conditions...
```

- Alternative to LIKE for position check

### Common Mistakes

- `_r%` would check 2nd position, not 3rd
- Using string months ('02') instead of integers

---

## Q34: Calculate percentage of male patients

### Tables Used

- `patients`

### Hint

Division with CAST to avoid integer truncation. Format as percentage.

### Understanding the Problem

- Count males / total patients × 100
- Round to 2 decimal places
- Display with % symbol

### Solution Approach

1. CAST to prevent integer division
2. Calculate percentage
3. ROUND to 2 decimals
4. CONCAT the % symbol

### T-SQL Answer

```sql
SELECT 
    CONCAT(
        ROUND(
            CAST(SUM(IIF(gender = 'M', 1, 0)) AS FLOAT) / 
            CAST(COUNT(*) AS FLOAT) * 100
        , 2),
        '%'
    ) AS male_percentage
FROM patients;
```

### Why This Approach?

- CAST to FLOAT prevents integer division (which would give 0 or 1)
- ROUND for precision
- CONCAT adds the % symbol

### Alternative Approaches

**Using FORMAT:**

```sql
SELECT 
    FORMAT(
        CAST(SUM(IIF(gender = 'M', 1, 0)) AS FLOAT) / COUNT(*),
        'P2'
    ) AS male_percentage
FROM patients;
```

- FORMAT with 'P2' gives percentage with 2 decimal places

### Common Mistakes

- Integer division: `SUM/COUNT` without CAST returns 0 or 1
- Multiplying by 100 twice (once in formula, once in formatting)

---

## Q35: Daily admission change using LAG

### Tables Used

- `admissions`

### Hint

Window function LAG to get previous day's count.

### Understanding the Problem

- Count admissions per day
- Show change from previous day (today - yesterday)
- First day has NULL change

### Solution Approach

1. CTE to get daily counts
2. LAG to get previous day's count
3. Subtract for change

### T-SQL Answer

```sql
WITH daily_counts AS (
    SELECT 
        admission_date,
        COUNT(*) AS admission_count
    FROM admissions
    GROUP BY admission_date
)
SELECT 
    admission_date,
    admission_count,
    admission_count - LAG(admission_count) OVER (ORDER BY admission_date) AS day_change
FROM daily_counts;
```

### Why This Approach?

- LAG gets the previous row's value in order
- OVER (ORDER BY date) ensures chronological order
- NULL for first row (no previous) is correct behavior

### Alternative Approaches

**Using self-join:**

```sql
WITH daily_counts AS (
    SELECT admission_date, COUNT(*) AS cnt
    FROM admissions
    GROUP BY admission_date
)
SELECT 
    d1.admission_date,
    d1.cnt,
    d1.cnt - d2.cnt AS day_change
FROM daily_counts d1
LEFT JOIN daily_counts d2 ON d2.admission_date = DATEADD(DAY, -1, d1.admission_date);
```

- More complex, only works for consecutive dates

### Common Mistakes

- Forgetting ORDER BY in LAG (undefined behavior)
- Using LEAD instead of LAG (gives next, not previous)

---

## Q36: Custom sort with Ontario first

### Tables Used

- `province_names`

### Hint

CASE expression in ORDER BY to create priority.

### Understanding the Problem

- Ontario should always appear first
- All other provinces alphabetically after Ontario

### Solution Approach

1. Create sort priority with CASE
2. Ontario gets 0, others get 1
3. Secondary sort by name

### T-SQL Answer

```sql
SELECT province_name
FROM province_names
ORDER BY 
    CASE WHEN province_name = 'Ontario' THEN 0 ELSE 1 END,
    province_name;
```

### Why This Approach?

- CASE creates a sort key: Ontario = 0, others = 1
- Primary sort by this key puts Ontario first
- Secondary alphabetical sort for the rest

### Alternative Approaches

**Using IIF:**

```sql
SELECT province_name
FROM province_names
ORDER BY 
    IIF(province_name = 'Ontario', 0, 1),
    province_name;
```

- Shorter syntax, same result

### Common Mistakes

- Only using the CASE sort (would have random order for non-Ontario)
- Case sensitivity if data isn't consistent

---

## Q37: Doctor admission breakdown by year

### Tables Used

- `doctors`, `admissions`

### Hint

GROUP BY doctor AND year. YEAR() for extraction.

### Understanding the Problem

- For each doctor, for each year
- Count total admissions
- Show doctor info with yearly breakdown

### Solution Approach

1. JOIN doctors and admissions
2. GROUP BY doctor_id and YEAR(admission_date)
3. COUNT admissions

### T-SQL Answer

```sql
SELECT 
    d.doctor_id,
    d.first_name + ' ' + d.last_name AS doctor_name,
    d.speciality,
    YEAR(a.admission_date) AS admission_year,
    COUNT(*) AS total_admissions
FROM doctors d
INNER JOIN admissions a ON d.doctor_id = a.attending_doctor_id
GROUP BY 
    d.doctor_id, 
    d.first_name, 
    d.last_name, 
    d.speciality, 
    YEAR(a.admission_date)
ORDER BY d.doctor_id, admission_year;
```

### Why This Approach?

- Multi-dimensional grouping (doctor × year)
- All non-aggregated columns must be in GROUP BY
- ORDER BY makes output readable

### Alternative Approaches

**Using DATEPART:**

```sql
SELECT 
    d.doctor_id,
    CONCAT(d.first_name, ' ', d.last_name) AS doctor_name,
    d.speciality,
    DATEPART(YEAR, a.admission_date) AS admission_year,
    COUNT(*) AS total_admissions
FROM doctors d
INNER JOIN admissions a ON d.doctor_id = a.attending_doctor_id
GROUP BY 
    d.doctor_id, d.first_name, d.last_name, d.speciality, 
    DATEPART(YEAR, a.admission_date)
ORDER BY d.doctor_id, admission_year;
```

- YEAR() is just shorthand for DATEPART(YEAR, ...)

### Common Mistakes

- Missing columns in GROUP BY
- Not including the year in grouping (would show totals across all years)

---

## Summary of Advanced T-SQL Concepts

| Concept | Description | Example |
|---------|-------------|---------|
| **LAG/LEAD** | Access previous/next row | `LAG(col) OVER (ORDER BY ...)` |
| **Conditional Aggregation** | Count/sum with conditions | `SUM(IIF(cond, 1, 0))` |
| **HAVING with expressions** | Filter aggregated groups | `HAVING SUM(x) > SUM(y)` |
| **Custom sorting** | CASE in ORDER BY | `ORDER BY CASE WHEN ... END` |
| **FORMAT** | Display formatting | `FORMAT(0.75, 'P2')` → 75.00% |

---

## Key Takeaways for Hard Questions

1. **Break down the problem** - Multiple conditions often need multiple steps
2. **Use CTEs** - Complex queries become readable with intermediate results
3. **Window functions** - Essential for row comparisons (previous, next, running totals)
4. **Watch for type issues** - Integer division, NULL handling, string/number mixing
5. **Test edge cases** - What if no data matches? First/last row in window?
