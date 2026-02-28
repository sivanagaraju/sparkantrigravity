# SQL Practice Questions - Part 2 (Questions 16-30)

This document contains medium-to-hard difficulty SQL questions with T-SQL solutions.

---

## Database Schema Reference

| Table | Columns |
|-------|---------|
| `patients` | patient_id, first_name, last_name, gender, birth_date, city, province_id, allergies, height, weight |
| `admissions` | patient_id, admission_date, discharge_date, diagnosis, attending_doctor_id |
| `doctors` | doctor_id, first_name, last_name, speciality |
| `province_names` | province_id, province_name |

---

## Q16: Count admissions per day of month, sorted by count DESC

### Tables Used

- `admissions`

### Hint

Extract day from date. GROUP BY and COUNT.

### Understanding the Problem

- Extract the **day number** (1-31) from admission_date
- Count how many admissions happened on each day number across all months/years
- Sort by most admissions first

### Solution Approach

1. Use `DAY()` to extract day of month
2. GROUP BY the day number
3. COUNT and ORDER BY DESC

### T-SQL Answer

```sql
SELECT DAY(admission_date) AS day_number, COUNT(*) AS admission_count
FROM admissions
GROUP BY DAY(admission_date)
ORDER BY admission_count DESC;
```

### Why This Approach?

- `DAY()` is the standard T-SQL function for extracting day of month
- Simple aggregation pattern
- Single pass through data

### Alternative Approaches

**Using DATEPART:**

```sql
SELECT DATEPART(DAY, admission_date) AS day_number, COUNT(*) AS admission_count
FROM admissions
GROUP BY DATEPART(DAY, admission_date)
ORDER BY admission_count DESC;
```

- Equivalent, `DAY()` is shorthand for `DATEPART(DAY, ...)`

### Common Mistakes

- Using `STRFTIME('%d')` - that's SQLite, not T-SQL
- Confusing day of month with day of week (`DATEPART(WEEKDAY, ...)`)

---

## Q17: Find most recent admission for patient 542

### Tables Used

- `admissions`

### Hint

Filter, sort, and limit to 1 row.

### Understanding the Problem

- Find all admissions for patient_id = 542
- Return only the most recent one

### Solution Approach

1. Filter WHERE patient_id = 542
2. ORDER BY admission_date DESC (newest first)
3. Use TOP 1 to get only the first row

### T-SQL Answer

```sql
SELECT TOP 1 *
FROM admissions
WHERE patient_id = 542
ORDER BY admission_date DESC;
```

### Why This Approach?

- `TOP 1` is T-SQL's way to limit results (not LIMIT)
- ORDER BY DESC ensures newest is first
- Clean and efficient

### Alternative Approaches

**Using subquery with MAX:**

```sql
SELECT *
FROM admissions
WHERE patient_id = 542
  AND admission_date = (
      SELECT MAX(admission_date) 
      FROM admissions 
      WHERE patient_id = 542
  );
```

- Returns all rows if there are ties on date
- Two scans of filtered data

**Using ROW_NUMBER:**

```sql
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (ORDER BY admission_date DESC) AS rn
    FROM admissions
    WHERE patient_id = 542
) t
WHERE rn = 1;
```

- Overkill here, but useful in more complex scenarios

### Common Mistakes

- Using `LIMIT 1` instead of `TOP 1` - LIMIT is MySQL/PostgreSQL
- Forgetting ORDER BY (would return arbitrary row)

---

## Q18: Complex filter with odd patient_id and doctor conditions

### Tables Used

- `admissions`

### Hint

Combine multiple conditions with AND/OR. Use modulo for odd numbers.

### Understanding the Problem

Two separate criteria (either can match):

1. patient_id is odd AND attending_doctor_id IN (1, 5, 19)
2. attending_doctor_id contains '2' AND patient_id has 3 digits

### Solution Approach

1. Use modulo `% 2 = 1` for odd check
2. Use `IN` for doctor list
3. Use `LIKE` on cast to find '2' in doctor_id
4. Use `LEN` on cast for 3-digit check
5. Combine with proper parentheses

### T-SQL Answer

```sql
SELECT patient_id, attending_doctor_id, diagnosis
FROM admissions
WHERE (patient_id % 2 = 1 AND attending_doctor_id IN (1, 5, 19))
   OR (CAST(attending_doctor_id AS VARCHAR) LIKE '%2%' 
       AND LEN(CAST(patient_id AS VARCHAR)) = 3);
```

### Why This Approach?

- Modulo is the standard way to check odd/even
- CAST to VARCHAR allows string operations on numbers
- Parentheses are crucial for correct OR/AND logic

### Alternative Approaches

**Using string conversion function:**

```sql
SELECT patient_id, attending_doctor_id, diagnosis
FROM admissions
WHERE (patient_id % 2 = 1 AND attending_doctor_id IN (1, 5, 19))
   OR (CONVERT(VARCHAR, attending_doctor_id) LIKE '%2%' 
       AND patient_id BETWEEN 100 AND 999);
```

- BETWEEN is cleaner for 3-digit check

### Common Mistakes

- Missing parentheses around OR conditions
- Using `patient_id % 2 != 0` instead of `= 1` (same result but less clear)

---

## Q19: Count admissions per doctor

### Tables Used

- `doctors`, `admissions`

### Hint

JOIN and GROUP BY.

### Understanding the Problem

- Each admission has attending_doctor_id
- Count how many admissions each doctor has handled
- Show doctor names

### Solution Approach

1. JOIN doctors and admissions on doctor_id
2. GROUP BY doctor's name
3. COUNT admissions

### T-SQL Answer

```sql
SELECT d.first_name, d.last_name, COUNT(*) AS total_admissions
FROM doctors d
INNER JOIN admissions a ON d.doctor_id = a.attending_doctor_id
GROUP BY d.first_name, d.last_name;
```

### Why This Approach?

- INNER JOIN excludes doctors with no admissions
- GROUP BY both name parts for uniqueness
- Clean aggregation

### Alternative Approaches

**Include doctors with zero admissions:**

```sql
SELECT d.first_name, d.last_name, COUNT(a.patient_id) AS total_admissions
FROM doctors d
LEFT JOIN admissions a ON d.doctor_id = a.attending_doctor_id
GROUP BY d.first_name, d.last_name;
```

- LEFT JOIN keeps all doctors
- COUNT(a.patient_id) returns 0 for unmatched rows (not NULL)

### Common Mistakes

- Using COUNT(*) with LEFT JOIN would count 1 for doctors with no admissions
- Forgetting to group by all non-aggregated columns

---

## Q20: First and last admission date per doctor

### Tables Used

- `doctors`, `admissions`

### Hint

MIN and MAX aggregations.

### Understanding the Problem

- For each doctor, find their earliest and latest admission dates
- Show doctor's full name

### Solution Approach

1. JOIN doctors and admissions
2. GROUP BY doctor
3. Use MIN and MAX for first/last dates

### T-SQL Answer

```sql
SELECT 
    d.doctor_id,
    d.first_name + ' ' + d.last_name AS full_name,
    MIN(a.admission_date) AS first_admission,
    MAX(a.admission_date) AS last_admission
FROM doctors d
INNER JOIN admissions a ON d.doctor_id = a.attending_doctor_id
GROUP BY d.doctor_id, d.first_name, d.last_name;
```

### Why This Approach?

- MIN/MAX are the natural choice for earliest/latest
- Group by doctor_id ensures uniqueness even if names duplicate
- String concatenation with `+` for full name

### Alternative Approaches

**Using CONCAT for NULL-safety:**

```sql
SELECT 
    d.doctor_id,
    CONCAT(d.first_name, ' ', d.last_name) AS full_name,
    MIN(a.admission_date) AS first_admission,
    MAX(a.admission_date) AS last_admission
FROM doctors d
INNER JOIN admissions a ON d.doctor_id = a.attending_doctor_id
GROUP BY d.doctor_id, d.first_name, d.last_name;
```

- CONCAT handles NULLs better

### Common Mistakes

- Not including all non-aggregated columns in GROUP BY
- Using FIRST/LAST - those aren't standard aggregate functions

---

## Q21: Count patients per province

### Tables Used

- `patients`, `province_names`

### Hint

JOIN to get province name. GROUP BY and COUNT.

### Understanding the Problem

- Count patients in each province
- Show province name (not just ID)
- Order by count descending

### Solution Approach

1. JOIN patients with province_names
2. GROUP BY province_name
3. COUNT and ORDER

### T-SQL Answer

```sql
SELECT pn.province_name, COUNT(*) AS patient_count
FROM patients p
INNER JOIN province_names pn ON p.province_id = pn.province_id
GROUP BY pn.province_name
ORDER BY patient_count DESC;
```

### Why This Approach?

- Join brings in the readable province name
- Standard aggregation pattern
- Descending order shows largest provinces first

### Common Mistakes

- Grouping by province_id only - would work but less informative
- LEFT JOIN when INNER is appropriate (unless you want provinces with 0 patients)

---

## Q22: Three-way join - patient, diagnosis, doctor

### Tables Used

- `patients`, `admissions`, `doctors`

### Hint

Two JOINs in sequence.

### Understanding the Problem

- For each admission, show:
  - Patient's full name
  - The diagnosis
  - Doctor's full name

### Solution Approach

1. Start from admissions (center table)
2. JOIN to patients for patient name
3. JOIN to doctors for doctor name

### T-SQL Answer

```sql
SELECT 
    p.first_name + ' ' + p.last_name AS patient_name,
    a.diagnosis,
    d.first_name + ' ' + d.last_name AS doctor_name
FROM admissions a
INNER JOIN patients p ON a.patient_id = p.patient_id
INNER JOIN doctors d ON a.attending_doctor_id = d.doctor_id;
```

### Why This Approach?

- Admissions is the natural center (has FKs to both tables)
- INNER JOINs ensure only complete records
- Clear column aliases

### Alternative Approaches

**Using CONCAT:**

```sql
SELECT 
    CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
    a.diagnosis,
    CONCAT(d.first_name, ' ', d.last_name) AS doctor_name
FROM admissions a
INNER JOIN patients p ON a.patient_id = p.patient_id
INNER JOIN doctors d ON a.attending_doctor_id = d.doctor_id;
```

- NULL-safe string concatenation

### Common Mistakes

- Wrong join order (doesn't affect result but affects readability)
- Mixing up which ID joins to which table

---

## Q23: Find duplicate patients by name

### Tables Used

- `patients`

### Hint

GROUP BY name. HAVING COUNT > 1.

### Understanding the Problem

- Find patients who share the same first AND last name
- Show how many times each name combination appears

### Solution Approach

1. GROUP BY first_name AND last_name
2. HAVING COUNT(*) > 1 to filter for duplicates

### T-SQL Answer

```sql
SELECT first_name, last_name, COUNT(*) AS duplicate_count
FROM patients
GROUP BY first_name, last_name
HAVING COUNT(*) > 1;
```

### Why This Approach?

- Standard duplicate detection pattern
- HAVING filters after aggregation
- Shows the actual count for context

### Common Mistakes

- Grouping by only first_name or only last_name
- Using WHERE instead of HAVING

---

## Q24: Convert height and weight with unit labels

### Tables Used

- `patients`

### Hint

Math operations. ROUND. CASE for gender.

### Understanding the Problem

- Convert height from cm to feet (divide by 30.48)
- Convert weight from kg to pounds (multiply by 2.205)
- Expand gender M/F to Male/Female

### Solution Approach

1. ROUND for decimal precision
2. CASE WHEN for gender expansion
3. Math operations for conversions

### T-SQL Answer

```sql
SELECT 
    first_name + ' ' + last_name AS full_name,
    ROUND(height / 30.48, 1) AS height_feet,
    ROUND(weight * 2.205, 0) AS weight_pounds,
    birth_date,
    CASE 
        WHEN gender = 'M' THEN 'Male'
        WHEN gender = 'F' THEN 'Female'
        ELSE 'Unknown'
    END AS gender_full
FROM patients;
```

### Why This Approach?

- ROUND controls decimal places (1 for feet, 0 for pounds)
- CASE handles the lookup/expansion cleanly
- All transformations in a single SELECT

### Common Mistakes

- Integer division (height/30 instead of height/30.48)
- Forgetting ELSE in CASE (returns NULL if no match)

---

## Q25: Find patients with no admissions

### Tables Used

- `patients`, `admissions`

### Hint

LEFT JOIN and check for NULL.

### Understanding the Problem

- Find patients who have never been admitted
- They exist in patients but not in admissions

### Solution Approach

1. LEFT JOIN patients to admissions
2. Filter where admission side is NULL

### T-SQL Answer

```sql
SELECT p.patient_id, p.first_name, p.last_name
FROM patients p
LEFT JOIN admissions a ON p.patient_id = a.patient_id
WHERE a.patient_id IS NULL;
```

### Why This Approach?

- LEFT JOIN keeps all patients
- NULL in admission columns means no match = no admissions
- Standard "anti-join" pattern

### Alternative Approaches

**Using NOT EXISTS:**

```sql
SELECT patient_id, first_name, last_name
FROM patients p
WHERE NOT EXISTS (
    SELECT 1 FROM admissions a WHERE a.patient_id = p.patient_id
);
```

- Often more efficient, clearly expresses intent

**Using NOT IN:**

```sql
SELECT patient_id, first_name, last_name
FROM patients
WHERE patient_id NOT IN (SELECT patient_id FROM admissions);
```

- Simple but beware of NULLs in subquery

### Common Mistakes

- Using INNER JOIN (would return nothing for this query)
- Checking wrong column for NULL

---

## Q26: Aggregate of aggregates (min/max/avg daily admissions)

### Tables Used

- `admissions`

### Hint

CTE or subquery. Two-level aggregation.

### Understanding the Problem

- First, count admissions per day
- Then, find min/max/avg of those daily counts

### Solution Approach

1. CTE to calculate daily counts
2. Outer query aggregates the counts

### T-SQL Answer

```sql
WITH daily_counts AS (
    SELECT admission_date, COUNT(*) AS daily_admission_count
    FROM admissions
    GROUP BY admission_date
)
SELECT 
    MAX(daily_admission_count) AS max_visits,
    MIN(daily_admission_count) AS min_visits,
    ROUND(AVG(CAST(daily_admission_count AS FLOAT)), 2) AS avg_visits
FROM daily_counts;
```

### Why This Approach?

- CTE makes the logic clear and readable
- Two-level aggregation is a common pattern
- CAST to FLOAT for proper average calculation

### Alternative Approaches

**Using subquery:**

```sql
SELECT 
    MAX(daily_count) AS max_visits,
    MIN(daily_count) AS min_visits,
    ROUND(AVG(CAST(daily_count AS FLOAT)), 2) AS avg_visits
FROM (
    SELECT COUNT(*) AS daily_count
    FROM admissions
    GROUP BY admission_date
) t;
```

- Equivalent, just inline the calculation

### Common Mistakes

- Integer division in AVG (use CAST to get decimals)
- Trying to nest aggregates directly without subquery/CTE

---

## Q27: Group patients into weight brackets

### Tables Used

- `patients`

### Hint

Integer division to create buckets.

### Understanding the Problem

- Create weight groups: 100-109 → 100, 110-119 → 110, etc.
- Count patients in each group

### Solution Approach

1. Integer division by 10, then multiply by 10
2. GROUP BY the bucket
3. COUNT and ORDER

### T-SQL Answer

```sql
SELECT 
    (weight / 10) * 10 AS weight_group,
    COUNT(*) AS patient_count
FROM patients
GROUP BY (weight / 10) * 10
ORDER BY weight_group DESC;
```

### Why This Approach?

- Integer division truncates (104/10 = 10, 10*10 = 100)
- Simple bucketing formula
- Descending order shows heaviest groups first

### Alternative Approaches

**Using FLOOR (for non-integer weights):**

```sql
SELECT 
    FLOOR(weight / 10.0) * 10 AS weight_group,
    COUNT(*) AS patient_count
FROM patients
GROUP BY FLOOR(weight / 10.0) * 10
ORDER BY weight_group DESC;
```

- More explicit, handles decimal weights

### Common Mistakes

- Using modulo instead of division
- Adding instead of multiplying back

---

## Q28: Calculate BMI and flag obesity

### Tables Used

- `patients`

### Hint

BMI formula. CASE for boolean flag.

### Understanding the Problem

- BMI = weight (kg) / height (m)²
- Height is in cm, must convert to meters
- Obese = BMI >= 30

### Solution Approach

1. Convert height cm to meters (divide by 100)
2. Calculate BMI
3. Use CASE to return 1 or 0

### T-SQL Answer

```sql
SELECT 
    patient_id,
    weight,
    height,
    CASE 
        WHEN weight / POWER(height / 100.0, 2) >= 30 THEN 1
        ELSE 0
    END AS isObese
FROM patients;
```

### Why This Approach?

- POWER for squaring
- 100.0 forces float division
- CASE creates the boolean flag

### Alternative Approaches

**Using IIF:**

```sql
SELECT 
    patient_id,
    weight,
    height,
    IIF(weight / POWER(height / 100.0, 2) >= 30, 1, 0) AS isObese
FROM patients;
```

- IIF is T-SQL shorthand for simple CASE

### Common Mistakes

- Integer division (height/100 = 1 for any height < 200)
- Wrong formula (forgetting to square denominator)

---

## Q29: Find epilepsy patients of Dr. Lisa

### Tables Used

- `patients`, `admissions`, `doctors`

### Hint

Three-way join with multiple filters.

### Understanding the Problem

- Patient has diagnosis = 'Epilepsy'
- AND their doctor's first name is 'Lisa'
- Show patient info and doctor's specialty

### Solution Approach

1. Three-way join
2. Filter on both diagnosis and doctor name

### T-SQL Answer

```sql
SELECT 
    p.patient_id,
    p.first_name,
    p.last_name,
    d.speciality
FROM patients p
INNER JOIN admissions a ON p.patient_id = a.patient_id
INNER JOIN doctors d ON a.attending_doctor_id = d.doctor_id
WHERE a.diagnosis = 'Epilepsy'
  AND d.first_name = 'Lisa';
```

### Why This Approach?

- Joins connect all three tables
- WHERE clause filters on both conditions
- Returns only matching records

### Common Mistakes

- Filtering before joining (would need subqueries)
- Using OR instead of AND

---

## Q30: Generate temporary password

### Tables Used

- `patients`, `admissions`

### Hint

CONCAT patient_id + length of last_name + birth year.

### Understanding the Problem

- Only for patients who have had admissions
- Password = patient_id + length(last_name) + year(birth_date)
- One password per patient (use DISTINCT)

### Solution Approach

1. JOIN to filter for admitted patients
2. CONCAT the three parts
3. DISTINCT to avoid duplicates from multiple admissions

### T-SQL Answer

```sql
SELECT DISTINCT
    p.patient_id,
    CONCAT(p.patient_id, LEN(p.last_name), YEAR(p.birth_date)) AS temp_password
FROM patients p
INNER JOIN admissions a ON p.patient_id = a.patient_id;
```

### Why This Approach?

- INNER JOIN ensures only patients with admissions
- CONCAT handles the string building
- DISTINCT removes duplicates from multiple admissions

### Alternative Approaches

**Using string concatenation with +:**

```sql
SELECT DISTINCT
    p.patient_id,
    CAST(p.patient_id AS VARCHAR) + CAST(LEN(p.last_name) AS VARCHAR) + CAST(YEAR(p.birth_date) AS VARCHAR) AS temp_password
FROM patients p
INNER JOIN admissions a ON p.patient_id = a.patient_id;
```

- More verbose, explicit type conversion

### Common Mistakes

- Returning one row per admission instead of per patient
- Type mismatches when concatenating mixed types

---

## Summary of Key T-SQL Functions Used

| Function | Purpose | Example |
|----------|---------|---------|
| `DAY()` | Extract day from date | `DAY(admission_date)` |
| `TOP n` | Limit results | `SELECT TOP 1 * FROM ...` |
| `POWER()` | Exponentiation | `POWER(x, 2)` |
| `FLOOR()` | Round down | `FLOOR(weight / 10.0)` |
| `IIF()` | Simple conditional | `IIF(condition, true_val, false_val)` |
| `CONVERT()` | Type conversion | `CONVERT(VARCHAR, number)` |
