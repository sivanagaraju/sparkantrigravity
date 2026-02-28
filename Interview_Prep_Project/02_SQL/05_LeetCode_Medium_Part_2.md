# LeetCode SQL Medium - Part 2 (Questions 11-19)

LeetCode Medium SQL questions with T-SQL solutions.

---

## Q11: Exchange Seats

### Tables

```
Seat (id INT PK AUTO_INCREMENT, student VARCHAR)
```

### Problem

Swap adjacent seats. If odd number of students, last one stays.

### Hint

Use CASE WHEN with modulo to check odd/even.

### Understanding the Problem

- ID 1 ↔ ID 2, ID 3 ↔ ID 4, etc.
- If odd count, last ID unchanged
- Output ordered by new ID

### T-SQL Answer

```sql
SELECT 
    CASE 
        WHEN id % 2 = 1 AND id = (SELECT COUNT(*) FROM Seat) THEN id  -- Last odd stays
        WHEN id % 2 = 1 THEN id + 1  -- Odd becomes next
        ELSE id - 1  -- Even becomes previous
    END AS id,
    student
FROM Seat
ORDER BY id;
```

### Why This Approach?

- Check edge case first (last odd student)
- Then swap: odd +1, even -1
- ORDER BY ensures correct output

---

## Q12: Customers Who Bought All Products

### Tables

```
Customer (customer_id INT, product_key INT FK)
Product (product_key INT PK)
```

### Problem

Find customers who bought all products.

### Hint

COUNT DISTINCT products per customer = total products.

### T-SQL Answer

```sql
SELECT customer_id
FROM Customer
GROUP BY customer_id
HAVING COUNT(DISTINCT product_key) = (SELECT COUNT(*) FROM Product);
```

### Why This Approach?

- GROUP BY customer
- COUNT DISTINCT products they bought
- Must equal total product count

---

## Q13: Product Sales Analysis III

### Tables

```
Sales (sale_id INT, product_id INT, year INT, quantity INT, price INT)
Product (product_id INT PK, product_name VARCHAR)
```

### Problem

For each product, return sales from its first year.

### Hint

Find MIN(year) per product, then join back.

### T-SQL Answer

```sql
WITH FirstYear AS (
    SELECT product_id, MIN(year) AS first_year
    FROM Sales
    GROUP BY product_id
)
SELECT s.product_id, f.first_year, s.quantity, s.price
FROM Sales s
INNER JOIN FirstYear f ON s.product_id = f.product_id AND s.year = f.first_year;
```

### Why This Approach?

- CTE finds first year per product
- JOIN back gets all sales from that year

---

## Q14: Market Analysis I

### Tables

```
Users (user_id INT PK, join_date DATE, favorite_brand VARCHAR)
Orders (order_id INT PK, order_date DATE, item_id INT FK, buyer_id INT FK, seller_id INT FK)
Items (item_id INT PK, item_brand VARCHAR)
```

### Problem

For each user: join date and count of orders as buyer in 2019.

### Hint

LEFT JOIN to include users with 0 orders.

### Understanding the Problem

- All users must appear (even with 0 orders)
- Count only orders in 2019
- user is the buyer

### T-SQL Answer

```sql
SELECT u.user_id AS buyer_id,
       u.join_date,
       SUM(CASE WHEN YEAR(o.order_date) = 2019 THEN 1 ELSE 0 END) AS orders_in_2019
FROM Users u
LEFT JOIN Orders o ON u.user_id = o.buyer_id
GROUP BY u.user_id, u.join_date;
```

### Why This Approach?

- LEFT JOIN keeps all users
- CASE WHEN counts only 2019 orders
- SUM gives 0 for no orders (not NULL)

---

## Q15: Product Price at a Given Date

### Tables

```
Products (product_id INT, new_price INT, change_date DATE)
PK: (product_id, change_date)
```

### Problem

Find price of each product on 2019-08-16. Initial price is 10.

### Hint

Find latest change on or before target date. Use LEAD for ranges.

### Understanding the Problem

- Price changes over time
- Need price valid ON that date
- If no change before date, use default 10

### T-SQL Answer

```sql
WITH LatestPrice AS (
    SELECT product_id, new_price,
           ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY change_date DESC) AS rn
    FROM Products
    WHERE change_date <= '2019-08-16'
)
SELECT product_id, new_price AS price
FROM LatestPrice
WHERE rn = 1

UNION

SELECT DISTINCT product_id, 10 AS price
FROM Products
WHERE product_id NOT IN (
    SELECT product_id FROM Products WHERE change_date <= '2019-08-16'
);
```

### Why This Approach?

- First part: products with changes before/on date (get latest)
- Second part: products with only future changes (use default 10)

---

## Q16: Immediate Food Delivery II

### Tables

```
Delivery (delivery_id INT PK, customer_id INT, order_date DATE, customer_pref_delivery_date DATE)
```

### Problem

Find % of first orders that are immediate (order_date = pref_date).

### Hint

Find first order per customer, then calculate immediate %.

### T-SQL Answer

```sql
WITH FirstOrders AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) AS rn
    FROM Delivery
)
SELECT ROUND(
    100.0 * SUM(CASE WHEN order_date = customer_pref_delivery_date THEN 1 ELSE 0 END) / COUNT(*),
    2
) AS immediate_percentage
FROM FirstOrders
WHERE rn = 1;
```

### Why This Approach?

- ROW_NUMBER finds first order per customer
- Filter to first orders only
- Calculate immediate % with conditional sum

---

## Q17: Monthly Transactions I

### Tables

```
Transactions (id INT PK, country VARCHAR, state ENUM('approved','declined'), amount INT, trans_date DATE)
```

### Problem

For each month/country: total count, total amount, approved count, approved amount.

### Hint

FORMAT for year-month. Conditional aggregation.

### T-SQL Answer

```sql
SELECT FORMAT(trans_date, 'yyyy-MM') AS month,
       country,
       COUNT(*) AS trans_count,
       SUM(CASE WHEN state = 'approved' THEN 1 ELSE 0 END) AS approved_count,
       SUM(amount) AS trans_total_amount,
       SUM(CASE WHEN state = 'approved' THEN amount ELSE 0 END) AS approved_total_amount
FROM Transactions
GROUP BY FORMAT(trans_date, 'yyyy-MM'), country;
```

### Why This Approach?

- FORMAT extracts year-month
- Conditional SUM for approved-only metrics

---

## Q18: Last Person to Fit in the Bus

### Tables

```
Queue (person_id INT PK, person_name VARCHAR, weight INT, turn INT)
```

### Problem

Bus has 1000kg limit. Find last person who can board (by turn order).

### Hint

Running SUM of weight. Filter <= 1000. Get last one.

### T-SQL Answer

```sql
WITH RunningWeight AS (
    SELECT person_name, turn,
           SUM(weight) OVER (ORDER BY turn) AS total_weight
    FROM Queue
)
SELECT TOP 1 person_name
FROM RunningWeight
WHERE total_weight <= 1000
ORDER BY turn DESC;
```

### Why This Approach?

- Running SUM by turn order
- Filter within limit
- TOP 1 with DESC gets last valid person

---

## Q19: Restaurant Growth

### Tables

```
Customer (customer_id INT, name VARCHAR, visited_on DATE, amount INT)
```

### Problem

Compute 7-day moving average (current day + 6 previous). Skip first 6 days.

### Hint

ROWS BETWEEN 6 PRECEDING AND CURRENT ROW.

### Understanding the Problem

- 7-day window = current + 6 before
- First 6 days don't have full window
- Need total amount AND average per day

### T-SQL Answer

```sql
WITH DailyTotals AS (
    SELECT visited_on, SUM(amount) AS amount
    FROM Customer
    GROUP BY visited_on
),
MovingAvg AS (
    SELECT visited_on,
           SUM(amount) OVER (ORDER BY visited_on ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS amount,
           AVG(1.0 * amount) OVER (ORDER BY visited_on ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS average_amount,
           ROW_NUMBER() OVER (ORDER BY visited_on) AS rn
    FROM DailyTotals
)
SELECT visited_on, amount, ROUND(average_amount, 2) AS average_amount
FROM MovingAvg
WHERE rn >= 7;
```

### Why This Approach?

- First aggregate by date (multiple customers per day)
- ROWS BETWEEN for 7-day window
- Skip first 6 days (incomplete window)

---

## Summary: Key Patterns

| Pattern | Questions |
|---------|-----------|
| **DENSE_RANK** | Q1, Q2, Q3, Q5 |
| **LAG/LEAD** | Q4, Q15 |
| **Running SUM** | Q18, Q19 |
| **CASE WHEN aggregation** | Q6, Q14, Q16, Q17 |
| **LEFT JOIN for all rows** | Q14 |
| **ROWS BETWEEN** | Q19 |
