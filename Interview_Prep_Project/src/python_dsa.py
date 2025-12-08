from collections import defaultdict, Counter

# =========================================================
# PYTHON CODING CHALLENGES (Data Engineering Focus)
# =========================================================

# ---------------------------------------------------------
# QUESTION 1: Log Parsing
# "Given a list of log strings, return the count of errors per user."
# Format: "TIMESTAMP USER_ID LEVEL MESSAGE"
# ---------------------------------------------------------
logs = [
    "2023-01-01 u1 INFO Login success",
    "2023-01-01 u2 ERROR DB connection failed",
    "2023-01-01 u1 ERROR File not found",
    "2023-01-02 u3 INFO Logout",
    "2023-01-02 u2 ERROR Timeout"
]

def count_errors_per_user(logs):
    error_counts = defaultdict(int)
    for log in logs:
        parts = log.split()
        # parts[0]=Time, parts[1]=User, parts[2]=Level, parts[3:]=Msg
        if len(parts) >= 3 and parts[2] == "ERROR":
            user_id = parts[1]
            error_counts[user_id] += 1
    return dict(error_counts)

print("Q1 Output:", count_errors_per_user(logs))
# Expected: {'u2': 2, 'u1': 1}


# ---------------------------------------------------------
# QUESTION 2: Flatten Nested Dictionary
# "Flatten a nested JSON/Dictionary object. Keys should be dot-separated."
# ---------------------------------------------------------
nested_data = {
    "a": 1,
    "b": {
        "c": 2,
        "d": {
            "e": 3
        }
    }
}

def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

print("Q2 Output:", flatten_dict(nested_data))
# Expected: {'a': 1, 'b.c': 2, 'b.d.e': 3}


# ---------------------------------------------------------
# QUESTION 3: Find Duplicate Files (by Content)
# "Given a list of (filename, content), group filenames that have identical content."
# ---------------------------------------------------------
files = [
    ("file1.txt", "hello world"),
    ("file2.txt", "foo bar"),
    ("file3.txt", "hello world"),
    ("file4.txt", "baz"),
    ("file5.txt", "foo bar")
]

def group_duplicates(files):
    content_map = defaultdict(list)
    for fname, content in files:
        content_map[content].append(fname)
    
    # Return only groups with >1 file
    return [group for group in content_map.values() if len(group) > 1]

print("Q3 Output:", group_duplicates(files))
# Expected: [['file1.txt', 'file3.txt'], ['file2.txt', 'file5.txt']]


# ---------------------------------------------------------
# QUESTION 4: ETL Data Transformation (List of Dicts)
# "Join two lists of dictionaries on a key (like a SQL Join)."
# ---------------------------------------------------------
users = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
orders = [{"order_id": 101, "user_id": 1, "amount": 50}, {"order_id": 102, "user_id": 1, "amount": 20}, {"order_id": 103, "user_id": 3, "amount": 100}]

def left_join(users, orders):
    # Convert right side to a lookup map (hash join)
    orders_map = defaultdict(list)
    for o in orders:
        orders_map[o['user_id']].append(o)
        
    result = []
    for u in users:
        user_orders = orders_map.get(u['id'], [])
        if not user_orders:
            # No matching orders
            row = u.copy()
            row['orders'] = []
            result.append(row)
        else:
            # Add orders
            row = u.copy()
            row['orders'] = user_orders
            result.append(row)
    return result

print("Q4 Output:", left_join(users, orders))
