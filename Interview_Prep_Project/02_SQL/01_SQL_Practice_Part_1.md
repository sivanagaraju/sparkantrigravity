# SQL Practice Questions - Part 1 (Questions 1-15)

This document contains medium difficulty SQL questions with T-SQL solutions. Focus on understanding the problem-solving approach.

---

## Database Schema Reference

| Table | Columns |
|-------|---------|
| `patients` | patient_id, first_name, last_name, gender, birth_date, city, province_id, allergies, height, weight |
| `admissions` | patient_id, admission_date, discharge_date, diagnosis, attending_doctor_id |
| `doctors` | doctor_id, first_name, last_name, speciality |
| `province_names` | province_id, province_name |

---

## Q1: Show unique birth years from patients, ordered ascending

### Tables Used

- `patients`

### Hint

Extract the year from a date column. How do you get unique values?

### Understanding the Problem

- We need the **year portion** of `birth_date`
- We want **unique** years only (no duplicates)
- Results must be **sorted** from earliest to latest

### Solution Approach

1. Use `YEAR()` function to extract year from date
2. Use `DISTINCT` to remove duplicate years
3. Use `ORDER BY` to sort ascending

### T-SQL Answer

```sql
SELECT DISTINCT YEAR(birth_date) AS birth_year
FROM patients
ORDER BY birth_year ASC;
```

### Why This Approach?

- `YEAR()` is the standard T-SQL function for extracting year - clear and readable
- `DISTINCT` is more intuitive than `GROUP BY` for simple deduplication
- Alias `birth_year` makes output self-documenting

### Alternative Approaches

**Using GROUP BY:**

```sql
SELECT YEAR(birth_date) AS birth_year
FROM patients
GROUP BY YEAR(birth_date)
ORDER BY birth_year;
```

- Functionally equivalent, but `DISTINCT` better communicates intent for this use case

**Using DATEPART:**

```sql
SELECT DISTINCT DATEPART(YEAR, birth_date) AS birth_year
FROM patients
ORDER BY birth_year;
```

- `YEAR()` is simply shorthand for `DATEPART(YEAR, ...)`

### Common Mistakes

- Using `STRFTIME('%Y', ...)` - that's SQLite/MySQL, not T-SQL
- Forgetting `DISTINCT` and getting one row per patient instead of per year
- Using `ORDER BY 1` instead of alias - works but less readable

---

## Q2: Show unique first names that appear only once

### Tables Used

- `patients`

### Hint

Count how many times each name appears. Filter for counts of exactly 1.

### Understanding the Problem

- Find first names that are **truly unique** (no other patient shares that name)
- This is NOT the same as `DISTINCT` - we need names that occur exactly once in the entire table

### Solution Approach

1. Group by first_name
2. Count occurrences in each group
3. Filter where count equals 1 using HAVING

### T-SQL Answer

```sql
SELECT first_name
FROM patients
GROUP BY first_name
HAVING COUNT(*) = 1;
```

### Why This Approach?

- `GROUP BY` + `HAVING` is the standard pattern for filtering aggregated data
- `HAVING` filters after grouping (unlike `WHERE` which filters before)
- Clean, readable, and efficient

### Alternative Approaches

**Using Subquery:**

```sql
SELECT first_name
FROM patients
WHERE first_name IN (
    SELECT first_name
    FROM patients
    GROUP BY first_name
    HAVING COUNT(*) = 1
);
```

- More verbose, no benefit here

**Using Window Function:**

```sql
SELECT DISTINCT first_name
FROM (
    SELECT first_name, COUNT(*) OVER (PARTITION BY first_name) AS cnt
    FROM patients
) t
WHERE cnt = 1;
```

- Overkill for this problem, but shows window function skill

### Common Mistakes

- Confusing `DISTINCT` with "appears once" - DISTINCT just removes duplicates from output
- Using `WHERE COUNT(*) = 1` instead of `HAVING` - WHERE can't reference aggregates

---

## Q3: Find patients whose first_name starts and ends with 's' and is at least 6 characters

### Tables Used

- `patients`

### Hint

Pattern matching with LIKE. String length with LEN.

### Understanding the Problem

- First name must **start with 's'**
- First name must **end with 's'**
- Length must be **6 or more characters**
- Case sensitivity depends on collation (assume case-insensitive)

### Solution Approach

1. Use `LIKE 's%s'` for start/end pattern
2. Use `LEN()` for length check
3. Combine with AND

### T-SQL Answer

```sql
SELECT patient_id, first_name
FROM patients
WHERE first_name LIKE 's%s'
  AND LEN(first_name) >= 6;
```

### Why This Approach?

- `LIKE 's%s'` elegantly captures both conditions in one pattern
- `%` matches zero or more characters in the middle
- `LEN()` is the T-SQL function for string length (not LENGTH)

### Alternative Approaches

**Using LEFT and RIGHT:**

```sql
SELECT patient_id, first_name
FROM patients
WHERE LEFT(first_name, 1) = 's'
  AND RIGHT(first_name, 1) = 's'
  AND LEN(first_name) >= 6;
```

- More verbose but explicit about what we're checking

### Common Mistakes

- Using `LENGTH()` instead of `LEN()` - LENGTH is MySQL/PostgreSQL, T-SQL uses LEN
- Forgetting that `LIKE 's%s'` allows 2-character strings like 'ss' - need the length check
- Case sensitivity issues - check your database collation

---

## Q4: Find patients with diagnosis 'Dementia'

### Tables Used

- `patients`, `admissions`

### Hint

Join the two tables. Filter on diagnosis.

### Understanding the Problem

- Patient info is in `patients` table
- Diagnosis info is in `admissions` table
- Need to join them to find patients admitted with 'Dementia'

### Solution Approach

1. Join patients and admissions on patient_id
2. Filter where diagnosis = 'Dementia'
3. Select patient details

### T-SQL Answer

```sql
SELECT p.patient_id, p.first_name, p.last_name
FROM patients p
INNER JOIN admissions a ON p.patient_id = a.patient_id
WHERE a.diagnosis = 'Dementia';
```

### Why This Approach?

- `INNER JOIN` is correct because we only want patients who HAVE admissions with this diagnosis
- Table aliases (`p`, `a`) improve readability
- Explicit join syntax is clearer than implicit comma joins

### Alternative Approaches

**Using EXISTS:**

```sql
SELECT patient_id, first_name, last_name
FROM patients p
WHERE EXISTS (
    SELECT 1 FROM admissions a
    WHERE a.patient_id = p.patient_id
    AND a.diagnosis = 'Dementia'
);
```

- Better if you want each patient listed once even with multiple Dementia admissions

**Using IN:**

```sql
SELECT patient_id, first_name, last_name
FROM patients
WHERE patient_id IN (
    SELECT patient_id FROM admissions WHERE diagnosis = 'Dementia'
);
```

- Similar to EXISTS, returns distinct patients

### Common Mistakes

- Using `LEFT JOIN` when you need `INNER JOIN` - LEFT would include patients without Dementia
- Not handling duplicate patients (if admitted multiple times for Dementia)

---

## Q5: Order patients by name length, then alphabetically

### Tables Used

- `patients`

### Hint

ORDER BY can have multiple expressions. LEN for length.

### Understanding the Problem

- Primary sort: length of first_name (shortest first)
- Secondary sort: alphabetical order (for names of same length)

### Solution Approach

1. Use `LEN(first_name)` as first sort key
2. Use `first_name` as second sort key
3. Both ascending by default

### T-SQL Answer

```sql
SELECT first_name
FROM patients
ORDER BY LEN(first_name), first_name;
```

### Why This Approach?

- Multi-column ORDER BY is the standard approach
- First expression takes priority, second breaks ties
- Concise and efficient

### Alternative Approaches

**Explicit ASC:**

```sql
SELECT first_name
FROM patients
ORDER BY LEN(first_name) ASC, first_name ASC;
```

- Same result, more explicit about sort direction

### Common Mistakes

- Reversing the order of sort keys - length must come first
- Using `LENGTH()` instead of `LEN()`

---

## Q6: Count male and female patients in same row

### Tables Used

- `patients`

### Hint

Conditional aggregation with CASE inside SUM/COUNT.

### Understanding the Problem

- We want **one row** with **two columns**: male count and female count
- This is called "pivoting" or "conditional aggregation"

### Solution Approach

1. Use `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` pattern
2. One CASE for males, one for females
3. Single query, single row output

### T-SQL Answer

```sql
SELECT 
    SUM(CASE WHEN gender = 'M' THEN 1 ELSE 0 END) AS male_count,
    SUM(CASE WHEN gender = 'F' THEN 1 ELSE 0 END) AS female_count
FROM patients;
```

### Why This Approach?

- Conditional aggregation is the standard pattern for pivoting in SQL
- Single table scan - efficient
- Extensible to more categories (e.g., add 'Other')

### Alternative Approaches

**Using COUNT with CASE (returns NULL for false):**

```sql
SELECT 
    COUNT(CASE WHEN gender = 'M' THEN 1 END) AS male_count,
    COUNT(CASE WHEN gender = 'F' THEN 1 END) AS female_count
FROM patients;
```

- COUNT ignores NULLs, so no ELSE needed

**Using IIF (T-SQL specific):**

```sql
SELECT 
    SUM(IIF(gender = 'M', 1, 0)) AS male_count,
    SUM(IIF(gender = 'F', 1, 0)) AS female_count
FROM patients;
```

- IIF is T-SQL shorthand for simple CASE

### Common Mistakes

- Using GROUP BY and getting two rows instead of one row with two columns
- Forgetting ELSE 0 with SUM (ELSE NULL would give correct result but less clear)

---

## Q7: Find patients allergic to Penicillin or Morphine, sorted

### Tables Used

- `patients`

### Hint

Use IN for multiple values. Multi-column ORDER BY.

### Understanding the Problem

- Filter for specific allergy values
- Sort by allergies first, then by name

### Solution Approach

1. Use `IN ('Penicillin', 'Morphine')` for filtering
2. ORDER BY allergies, then first_name, then last_name

### T-SQL Answer

```sql
SELECT first_name, last_name, allergies
FROM patients
WHERE allergies IN ('Penicillin', 'Morphine')
ORDER BY allergies, first_name, last_name;
```

### Why This Approach?

- `IN` is cleaner than multiple OR conditions
- Easy to add more allergies to the list
- Multi-column ORDER BY handles the sorting requirements

### Alternative Approaches

**Using OR:**

```sql
SELECT first_name, last_name, allergies
FROM patients
WHERE allergies = 'Penicillin' OR allergies = 'Morphine'
ORDER BY allergies, first_name, last_name;
```

- Equivalent but more verbose

### Common Mistakes

- Forgetting that allergies could be NULL (not a problem here, but consider it)
- Case sensitivity if allergies are stored differently

---

## Q8: Find patients admitted multiple times for same diagnosis

### Tables Used

- `admissions`

### Hint

Group by patient AND diagnosis. Count > 1.

### Understanding the Problem

- Same patient, same diagnosis, multiple admissions
- Need to group by both columns

### Solution Approach

1. GROUP BY patient_id AND diagnosis
2. HAVING COUNT(*) > 1 to filter for multiples

### T-SQL Answer

```sql
SELECT patient_id, diagnosis
FROM admissions
GROUP BY patient_id, diagnosis
HAVING COUNT(*) > 1;
```

### Why This Approach?

- Composite grouping finds exact duplicates on the combination
- HAVING filters groups after aggregation
- Clean and efficient

### Alternative Approaches

**With admission count:**

```sql
SELECT patient_id, diagnosis, COUNT(*) AS admission_count
FROM admissions
GROUP BY patient_id, diagnosis
HAVING COUNT(*) > 1;
```

- Shows how many times they were admitted

### Common Mistakes

- Grouping by only one column
- Using WHERE instead of HAVING

---

## Q9: Count patients per city, sorted by count DESC then city ASC

### Tables Used

- `patients`

### Hint

GROUP BY with ORDER BY on both aggregated and regular columns.

### Understanding the Problem

- Count patients in each city
- Primary sort: most patients first (DESC)
- Secondary sort: city name alphabetically (ASC)

### Solution Approach

1. GROUP BY city
2. COUNT(*) for patient count
3. ORDER BY count DESC, city ASC

### T-SQL Answer

```sql
SELECT city, COUNT(*) AS num_patients
FROM patients
GROUP BY city
ORDER BY num_patients DESC, city ASC;
```

### Why This Approach?

- Standard aggregation pattern
- Alias in ORDER BY improves readability
- Dual sort handles ties properly

### Alternative Approaches

**ORDER BY expression instead of alias:**

```sql
SELECT city, COUNT(*) AS num_patients
FROM patients
GROUP BY city
ORDER BY COUNT(*) DESC, city ASC;
```

- Works but repeating the expression is less clean

### Common Mistakes

- Forgetting ASC/DESC on specific columns
- Getting sort order backwards

---

## Q10: Show all people (patients and doctors) with role label

### Tables Used

- `patients`, `doctors`

### Hint

UNION ALL to combine rows from different tables.

### Understanding the Problem

- Need to combine data from two different tables
- Add a literal column to identify the source (role)

### Solution Approach

1. SELECT from patients with 'Patient' role
2. UNION ALL with doctors with 'Doctor' role
3. Matching columns in both SELECTs

### T-SQL Answer

```sql
SELECT first_name, last_name, 'Patient' AS role 
FROM patients
UNION ALL
SELECT first_name, last_name, 'Doctor' AS role 
FROM doctors;
```

### Why This Approach?

- `UNION ALL` combines all rows from both queries
- Literal string creates the role column
- UNION ALL is faster than UNION (no duplicate check)

### Alternative Approaches

**Using UNION (removes duplicates):**

```sql
SELECT first_name, last_name, 'Patient' AS role FROM patients
UNION
SELECT first_name, last_name, 'Doctor' AS role FROM doctors;
```

- Only matters if a doctor is also a patient with same name

### Common Mistakes

- Mismatched columns between the two SELECTs
- Using UNION when you want all rows (UNION removes duplicates if role was same)

---

## Q11: Show allergies ordered by popularity

### Tables Used

- `patients`

### Hint

COUNT and GROUP BY. Filter out NULL values.

### Understanding the Problem

- Count occurrences of each allergy
- Exclude NULL (no allergy)
- Order by most common first

### Solution Approach

1. Filter out NULL allergies
2. GROUP BY allergies
3. COUNT and ORDER BY DESC

### T-SQL Answer

```sql
SELECT allergies, COUNT(*) AS allergy_count
FROM patients
WHERE allergies IS NOT NULL
GROUP BY allergies
ORDER BY allergy_count DESC;
```

### Why This Approach?

- `IS NOT NULL` filters before grouping (efficient)
- COUNT(*) counts patients per allergy
- DESC order shows most common first

### Alternative Approaches

**Filter in HAVING:**

```sql
SELECT allergies, COUNT(*) AS allergy_count
FROM patients
GROUP BY allergies
HAVING allergies IS NOT NULL
ORDER BY allergy_count DESC;
```

- Works but WHERE is more efficient for non-aggregate conditions

### Common Mistakes

- Using `allergies != NULL` instead of `IS NOT NULL` - equality comparison with NULL is always NULL
- Including NULL as a category

---

## Q12: Find patients born in the 1970s

### Tables Used

- `patients`

### Hint

Date range filtering. Years 1970-1979.

### Understanding the Problem

- Birth year between 1970 and 1979 (inclusive)
- Could filter on YEAR() or date range

### Solution Approach

1. Extract YEAR from birth_date
2. Filter BETWEEN 1970 AND 1979
3. Order by birth_date

### T-SQL Answer

```sql
SELECT first_name, last_name, birth_date
FROM patients
WHERE YEAR(birth_date) BETWEEN 1970 AND 1979
ORDER BY birth_date ASC;
```

### Why This Approach?

- `YEAR()` extracts just the year for comparison
- `BETWEEN` is inclusive and readable
- Clear intent

### Alternative Approaches

**Using date range (potentially more index-friendly):**

```sql
SELECT first_name, last_name, birth_date
FROM patients
WHERE birth_date >= '1970-01-01' AND birth_date < '1980-01-01'
ORDER BY birth_date ASC;
```

- Can use indexes on birth_date column
- More efficient for large tables

### Common Mistakes

- `BETWEEN 1970 AND 1980` would include anyone born on Jan 1, 1980
- Not considering index usage with function on column

---

## Q13: Format full name as LASTNAME,firstname

### Tables Used

- `patients`

### Hint

String functions: UPPER, LOWER, concatenation (+).

### Understanding the Problem

- Last name in UPPERCASE
- First name in lowercase
- Separated by comma
- Order by first_name DESC (original case)

### Solution Approach

1. Use UPPER() and LOWER() for case conversion
2. Concatenate with + operator
3. ORDER BY the original first_name column

### T-SQL Answer

```sql
SELECT UPPER(last_name) + ',' + LOWER(first_name) AS full_name
FROM patients
ORDER BY first_name DESC;
```

### Why This Approach?

- String concatenation with `+` is T-SQL standard
- Case functions are straightforward
- ORDER BY uses original column, not the transformed expression

### Alternative Approaches

**Using CONCAT:**

```sql
SELECT CONCAT(UPPER(last_name), ',', LOWER(first_name)) AS full_name
FROM patients
ORDER BY first_name DESC;
```

- CONCAT handles NULL better (returns other parts instead of NULL)

### Common Mistakes

- Using `||` for concatenation - that's PostgreSQL/Oracle, not T-SQL
- If any name is NULL, `+` returns NULL for entire expression

---

## Q14: Find provinces with total patient height >= 7000

### Tables Used

- `patients`

### Hint

GROUP BY and SUM. HAVING for aggregate filtering.

### Understanding the Problem

- Sum heights of all patients per province
- Filter for provinces where sum >= 7000

### Solution Approach

1. GROUP BY province_id
2. SUM(height) for total
3. HAVING to filter aggregated result

### T-SQL Answer

```sql
SELECT province_id, SUM(height) AS total_height
FROM patients
GROUP BY province_id
HAVING SUM(height) >= 7000;
```

### Why This Approach?

- Standard aggregation with filter pattern
- HAVING is required for filtering aggregate results
- Clean and efficient

### Alternative Approaches

**Using subquery:**

```sql
SELECT * FROM (
    SELECT province_id, SUM(height) AS total_height
    FROM patients
    GROUP BY province_id
) t
WHERE total_height >= 7000;
```

- More verbose, same result

### Common Mistakes

- Using WHERE instead of HAVING - WHERE can't filter aggregates
- Using alias in HAVING - T-SQL requires repeating the expression: `HAVING SUM(height) >= 7000`

---

## Q15: Find weight difference for patients named 'Maroni'

### Tables Used

- `patients`

### Hint

MAX, MIN, and subtraction.

### Understanding the Problem

- Filter for last_name = 'Maroni'
- Find the difference between heaviest and lightest

### Solution Approach

1. Filter WHERE last_name = 'Maroni'
2. Calculate MAX(weight) - MIN(weight)

### T-SQL Answer

```sql
SELECT MAX(weight) - MIN(weight) AS weight_difference
FROM patients
WHERE last_name = 'Maroni';
```

### Why This Approach?

- Simple aggregate math
- Single scan of filtered data
- Returns NULL if no Maroni patients (which is mathematically correct)

### Alternative Approaches

**Using subqueries (overkill but valid):**

```sql
SELECT 
    (SELECT MAX(weight) FROM patients WHERE last_name = 'Maroni') -
    (SELECT MIN(weight) FROM patients WHERE last_name = 'Maroni') AS weight_difference;
```

- Two table scans, less efficient

### Common Mistakes

- Forgetting the filter - would calculate for all patients
- Expecting a result if no patients match (returns NULL)

---

## Summary of Key T-SQL Functions Used

| Function | Purpose | Example |
|----------|---------|---------|
| `YEAR()` | Extract year from date | `YEAR(birth_date)` |
| `LEN()` | String length | `LEN(first_name)` |
| `UPPER()` / `LOWER()` | Case conversion | `UPPER(last_name)` |
| `+` | String concatenation | `first_name + ' ' + last_name` |
| `CONCAT()` | NULL-safe concatenation | `CONCAT(a, b, c)` |
| `IIF()` | Simple conditional | `IIF(gender='M', 1, 0)` |
