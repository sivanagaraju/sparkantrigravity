# SQL Practice - All Questions (Quick Reference)

This file contains all 37 SQL questions with table metadata, hints, and T-SQL solutions in one place.

---

## Database Schema

| Table | Columns |
|-------|---------|
| `patients` | patient_id, first_name, last_name, gender, birth_date, city, province_id, allergies, height, weight |
| `admissions` | patient_id, admission_date, discharge_date, diagnosis, attending_doctor_id |
| `doctors` | doctor_id, first_name, last_name, speciality |
| `province_names` | province_id, province_name |

### Relationships

- `patients.province_id` → `province_names.province_id`
- `admissions.patient_id` → `patients.patient_id`
- `admissions.attending_doctor_id` → `doctors.doctor_id`

---

## Part 1: Medium Questions (1-15)

### Q1: Unique birth years, sorted ascending

**Tables**: patients | **Hint**: YEAR(), DISTINCT, ORDER BY

```sql
SELECT DISTINCT YEAR(birth_date) AS birth_year
FROM patients
ORDER BY birth_year ASC;
```

---

### Q2: First names that appear only once

**Tables**: patients | **Hint**: GROUP BY, HAVING COUNT = 1

```sql
SELECT first_name
FROM patients
GROUP BY first_name
HAVING COUNT(*) = 1;
```

---

### Q3: Names starting and ending with 's', length >= 6

**Tables**: patients | **Hint**: LIKE 's%s', LEN()

```sql
SELECT patient_id, first_name
FROM patients
WHERE first_name LIKE 's%s'
  AND LEN(first_name) >= 6;
```

---

### Q4: Patients with 'Dementia' diagnosis

**Tables**: patients, admissions | **Hint**: JOIN, filter diagnosis

```sql
SELECT p.patient_id, p.first_name, p.last_name
FROM patients p
INNER JOIN admissions a ON p.patient_id = a.patient_id
WHERE a.diagnosis = 'Dementia';
```

---

### Q5: Order by name length, then alphabetically

**Tables**: patients | **Hint**: ORDER BY LEN(), then name

```sql
SELECT first_name
FROM patients
ORDER BY LEN(first_name), first_name;
```

---

### Q6: Male and female counts in same row

**Tables**: patients | **Hint**: SUM(CASE WHEN...)

```sql
SELECT 
    SUM(CASE WHEN gender = 'M' THEN 1 ELSE 0 END) AS male_count,
    SUM(CASE WHEN gender = 'F' THEN 1 ELSE 0 END) AS female_count
FROM patients;
```

---

### Q7: Patients allergic to Penicillin or Morphine

**Tables**: patients | **Hint**: IN, multi-column ORDER BY

```sql
SELECT first_name, last_name, allergies
FROM patients
WHERE allergies IN ('Penicillin', 'Morphine')
ORDER BY allergies, first_name, last_name;
```

---

### Q8: Multiple admissions for same diagnosis

**Tables**: admissions | **Hint**: GROUP BY patient + diagnosis, HAVING > 1

```sql
SELECT patient_id, diagnosis
FROM admissions
GROUP BY patient_id, diagnosis
HAVING COUNT(*) > 1;
```

---

### Q9: Patient count per city, sorted

**Tables**: patients | **Hint**: GROUP BY, ORDER BY count DESC, city ASC

```sql
SELECT city, COUNT(*) AS num_patients
FROM patients
GROUP BY city
ORDER BY num_patients DESC, city ASC;
```

---

### Q10: All people with role labels (UNION)

**Tables**: patients, doctors | **Hint**: UNION ALL with literal column

```sql
SELECT first_name, last_name, 'Patient' AS role FROM patients
UNION ALL
SELECT first_name, last_name, 'Doctor' AS role FROM doctors;
```

---

### Q11: Allergies by popularity (excluding NULL)

**Tables**: patients | **Hint**: IS NOT NULL, GROUP BY, ORDER BY DESC

```sql
SELECT allergies, COUNT(*) AS allergy_count
FROM patients
WHERE allergies IS NOT NULL
GROUP BY allergies
ORDER BY allergy_count DESC;
```

---

### Q12: Patients born in the 1970s

**Tables**: patients | **Hint**: YEAR(birth_date) BETWEEN 1970 AND 1979

```sql
SELECT first_name, last_name, birth_date
FROM patients
WHERE YEAR(birth_date) BETWEEN 1970 AND 1979
ORDER BY birth_date ASC;
```

---

### Q13: Full name as LASTNAME,firstname

**Tables**: patients | **Hint**: UPPER, LOWER, concatenation (+)

```sql
SELECT UPPER(last_name) + ',' + LOWER(first_name) AS full_name
FROM patients
ORDER BY first_name DESC;
```

---

### Q14: Provinces with total height >= 7000

**Tables**: patients | **Hint**: SUM(height), HAVING

```sql
SELECT province_id, SUM(height) AS total_height
FROM patients
GROUP BY province_id
HAVING SUM(height) >= 7000;
```

---

### Q15: Weight difference for 'Maroni' patients

**Tables**: patients | **Hint**: MAX - MIN

```sql
SELECT MAX(weight) - MIN(weight) AS weight_difference
FROM patients
WHERE last_name = 'Maroni';
```

---

## Part 2: Medium/Hard Questions (16-30)

### Q16: Admissions per day of month

**Tables**: admissions | **Hint**: DAY(), GROUP BY, ORDER BY DESC

```sql
SELECT DAY(admission_date) AS day_number, COUNT(*) AS admission_count
FROM admissions
GROUP BY DAY(admission_date)
ORDER BY admission_count DESC;
```

---

### Q17: Most recent admission for patient 542

**Tables**: admissions | **Hint**: TOP 1, ORDER BY DESC

```sql
SELECT TOP 1 *
FROM admissions
WHERE patient_id = 542
ORDER BY admission_date DESC;
```

---

### Q18: Complex filter (odd ID + doctors OR digit checks)

**Tables**: admissions | **Hint**: Modulo, LIKE, combine with OR

```sql
SELECT patient_id, attending_doctor_id, diagnosis
FROM admissions
WHERE (patient_id % 2 = 1 AND attending_doctor_id IN (1, 5, 19))
   OR (CAST(attending_doctor_id AS VARCHAR) LIKE '%2%' 
       AND LEN(CAST(patient_id AS VARCHAR)) = 3);
```

---

### Q19: Admission count per doctor

**Tables**: doctors, admissions | **Hint**: JOIN, GROUP BY, COUNT

```sql
SELECT d.first_name, d.last_name, COUNT(*) AS total_admissions
FROM doctors d
INNER JOIN admissions a ON d.doctor_id = a.attending_doctor_id
GROUP BY d.first_name, d.last_name;
```

---

### Q20: First and last admission dates per doctor

**Tables**: doctors, admissions | **Hint**: MIN, MAX

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

---

### Q21: Patient count per province

**Tables**: patients, province_names | **Hint**: JOIN, GROUP BY, ORDER BY DESC

```sql
SELECT pn.province_name, COUNT(*) AS patient_count
FROM patients p
INNER JOIN province_names pn ON p.province_id = pn.province_id
GROUP BY pn.province_name
ORDER BY patient_count DESC;
```

---

### Q22: Three-way join (patient, diagnosis, doctor)

**Tables**: patients, admissions, doctors | **Hint**: Two JOINs

```sql
SELECT 
    p.first_name + ' ' + p.last_name AS patient_name,
    a.diagnosis,
    d.first_name + ' ' + d.last_name AS doctor_name
FROM admissions a
INNER JOIN patients p ON a.patient_id = p.patient_id
INNER JOIN doctors d ON a.attending_doctor_id = d.doctor_id;
```

---

### Q23: Duplicate patients by name

**Tables**: patients | **Hint**: GROUP BY names, HAVING > 1

```sql
SELECT first_name, last_name, COUNT(*) AS duplicate_count
FROM patients
GROUP BY first_name, last_name
HAVING COUNT(*) > 1;
```

---

### Q24: Unit conversions and gender expansion

**Tables**: patients | **Hint**: ROUND, CASE for gender

```sql
SELECT 
    first_name + ' ' + last_name AS full_name,
    ROUND(height / 30.48, 1) AS height_feet,
    ROUND(weight * 2.205, 0) AS weight_pounds,
    birth_date,
    CASE WHEN gender = 'M' THEN 'Male'
         WHEN gender = 'F' THEN 'Female'
         ELSE 'Unknown' END AS gender_full
FROM patients;
```

---

### Q25: Patients with no admissions

**Tables**: patients, admissions | **Hint**: LEFT JOIN, WHERE IS NULL

```sql
SELECT p.patient_id, p.first_name, p.last_name
FROM patients p
LEFT JOIN admissions a ON p.patient_id = a.patient_id
WHERE a.patient_id IS NULL;
```

---

### Q26: Min/Max/Avg daily admissions

**Tables**: admissions | **Hint**: CTE for daily counts, then aggregate

```sql
WITH daily_counts AS (
    SELECT admission_date, COUNT(*) AS daily_count
    FROM admissions
    GROUP BY admission_date
)
SELECT 
    MAX(daily_count) AS max_visits,
    MIN(daily_count) AS min_visits,
    ROUND(AVG(CAST(daily_count AS FLOAT)), 2) AS avg_visits
FROM daily_counts;
```

---

### Q27: Weight group buckets (100-109 → 100)

**Tables**: patients | **Hint**: Integer division × 10

```sql
SELECT 
    (weight / 10) * 10 AS weight_group,
    COUNT(*) AS patient_count
FROM patients
GROUP BY (weight / 10) * 10
ORDER BY weight_group DESC;
```

---

### Q28: BMI calculation and obesity flag

**Tables**: patients | **Hint**: POWER, CASE/IIF

```sql
SELECT 
    patient_id, weight, height,
    CASE WHEN weight / POWER(height / 100.0, 2) >= 30 THEN 1 ELSE 0 END AS isObese
FROM patients;
```

---

### Q29: Epilepsy patients of Dr. Lisa

**Tables**: patients, admissions, doctors | **Hint**: 3-way join, WHERE conditions

```sql
SELECT p.patient_id, p.first_name, p.last_name, d.speciality
FROM patients p
INNER JOIN admissions a ON p.patient_id = a.patient_id
INNER JOIN doctors d ON a.attending_doctor_id = d.doctor_id
WHERE a.diagnosis = 'Epilepsy' AND d.first_name = 'Lisa';
```

---

### Q30: Generate temp password (id + len(name) + year)

**Tables**: patients, admissions | **Hint**: CONCAT, DISTINCT on join

```sql
SELECT DISTINCT
    p.patient_id,
    CONCAT(p.patient_id, LEN(p.last_name), YEAR(p.birth_date)) AS temp_password
FROM patients p
INNER JOIN admissions a ON p.patient_id = a.patient_id;
```

---

## Part 3: Hard Questions (31-37)

### Q31: Admission costs by insurance status

**Tables**: patients, admissions | **Hint**: Even ID = insured, CASE for cost

```sql
SELECT 
    CASE WHEN p.patient_id % 2 = 0 THEN 'Yes' ELSE 'No' END AS has_insurance,
    SUM(CASE WHEN p.patient_id % 2 = 0 THEN 10 ELSE 50 END) AS total_cost
FROM patients p
INNER JOIN admissions a ON p.patient_id = a.patient_id
GROUP BY CASE WHEN p.patient_id % 2 = 0 THEN 'Yes' ELSE 'No' END;
```

---

### Q32: Provinces with more males than females

**Tables**: patients, province_names | **Hint**: Conditional aggregation, HAVING

```sql
SELECT pn.province_name
FROM patients p
INNER JOIN province_names pn ON p.province_id = pn.province_id
GROUP BY pn.province_name
HAVING SUM(CASE WHEN p.gender = 'M' THEN 1 ELSE 0 END) > 
       SUM(CASE WHEN p.gender = 'F' THEN 1 ELSE 0 END);
```

---

### Q33: Complex multi-condition patient filter

**Tables**: patients | **Hint**: LIKE '__r%', MONTH(), BETWEEN, modulo

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

---

### Q34: Percentage of male patients

**Tables**: patients | **Hint**: CAST for float division, CONCAT %

```sql
SELECT CONCAT(
    ROUND(CAST(SUM(IIF(gender = 'M', 1, 0)) AS FLOAT) / COUNT(*) * 100, 2),
    '%') AS male_percentage
FROM patients;
```

---

### Q35: Daily admission change (LAG window function)

**Tables**: admissions | **Hint**: CTE + LAG OVER (ORDER BY)

```sql
WITH daily_counts AS (
    SELECT admission_date, COUNT(*) AS admission_count
    FROM admissions
    GROUP BY admission_date
)
SELECT 
    admission_date,
    admission_count,
    admission_count - LAG(admission_count) OVER (ORDER BY admission_date) AS day_change
FROM daily_counts;
```

---

### Q36: Custom sort (Ontario first)

**Tables**: province_names | **Hint**: CASE in ORDER BY

```sql
SELECT province_name
FROM province_names
ORDER BY 
    CASE WHEN province_name = 'Ontario' THEN 0 ELSE 1 END,
    province_name;
```

---

### Q37: Doctor admissions breakdown by year

**Tables**: doctors, admissions | **Hint**: GROUP BY doctor + YEAR()

```sql
SELECT 
    d.doctor_id,
    d.first_name + ' ' + d.last_name AS doctor_name,
    d.speciality,
    YEAR(a.admission_date) AS admission_year,
    COUNT(*) AS total_admissions
FROM doctors d
INNER JOIN admissions a ON d.doctor_id = a.attending_doctor_id
GROUP BY d.doctor_id, d.first_name, d.last_name, d.speciality, YEAR(a.admission_date)
ORDER BY d.doctor_id, admission_year;
```
