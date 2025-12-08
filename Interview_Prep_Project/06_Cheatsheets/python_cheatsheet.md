# PYTHON CHEATSHEET - Interview Quick Reference

## 🔥 MEMORY TRICKS

### `is` vs `==`
**"IS for Identity, EQUALS for Equality"**
```python
==   →  Same VALUE?
is   →  Same OBJECT in memory?

# Rule: Use 'is' ONLY for None, True, False
if x is None:    # ✅ Correct
if x == None:    # ❌ Works but bad style
```

### Mutable Default Arguments
**"Never use [] or {} as default!"**
```python
# ❌ BUG: Same list shared across calls
def bad(items=[]):
    items.append(1)
    return items

# ✅ FIX: Use None
def good(items=None):
    if items is None:
        items = []
    items.append(1)
    return items
```

### LEGB Scope
**"Local → Enclosing → Global → Built-in"**
```python
x = "global"
def outer():
    x = "enclosing"
    def inner():
        x = "local"
        print(x)  # "local"
```

---

## 📝 DATA STRUCTURES

### List Operations
```python
# Create
lst = [1, 2, 3]
lst = list(range(10))

# Access
lst[0]      # First
lst[-1]     # Last
lst[1:3]    # Slice [1, 2]

# Modify
lst.append(4)      # Add to end
lst.insert(0, 0)   # Insert at index
lst.extend([5,6])  # Add multiple
lst.pop()          # Remove last
lst.remove(2)      # Remove first occurrence

# Search
2 in lst           # O(n)
lst.index(2)       # Index of first 2
lst.count(2)       # Count occurrences

# Sort
lst.sort()              # In-place
sorted(lst)             # Returns new list
lst.sort(key=len)       # Custom key
lst.sort(reverse=True)  # Descending
```

### Dictionary Operations
```python
# Create
d = {"a": 1, "b": 2}
d = dict(a=1, b=2)

# Access (safe)
d.get("a")         # Returns None if missing
d.get("x", 0)      # Returns 0 if missing

# Modify
d["c"] = 3                  # Add/update
d.update({"d": 4, "e": 5})  # Update multiple
d.pop("a")                  # Remove and return
del d["b"]                  # Remove

# Iterate
for k in d:              # Keys
for v in d.values():     # Values
for k, v in d.items():   # Both

# Useful
d.keys()    # dict_keys
d.values()  # dict_values
d.items()   # dict_items
```

### Set Operations
```python
s = {1, 2, 3}

s.add(4)                # Add element
s.remove(1)             # Remove (error if missing)
s.discard(1)            # Remove (no error)

# Set math
a | b   # Union
a & b   # Intersection
a - b   # Difference (in a but not b)
a ^ b   # Symmetric difference (in a or b, not both)
```

---

## 🔄 COMPREHENSIONS

### List Comprehension
```python
[x**2 for x in range(10)]                    # [0, 1, 4, 9, ...]
[x for x in range(10) if x % 2 == 0]         # Even numbers
[x if x > 5 else 0 for x in range(10)]       # Conditional value
```

### Dict Comprehension
```python
{k: v for k, v in items}
{k: v**2 for k, v in d.items()}
{x: x**2 for x in range(5)}
```

### Generator Expression
```python
(x**2 for x in range(10))  # Memory efficient
sum(x**2 for x in range(10))  # Works with functions
```

---

## ⚠️ TRICKY GOTCHAS

### 1. Integer Caching (-5 to 256)
```python
a = 256; b = 256
a is b  # True (cached)

a = 257; b = 257
a is b  # False (not cached!)
```

### 2. String Interning
```python
a = "hello"; b = "hello"
a is b  # True (interned)

a = "hello world"; b = "hello world"
a is b  # May be False!
```

### 3. List Copy vs Reference
```python
a = [1, 2, 3]
b = a           # REFERENCE (same object)
b = a.copy()    # COPY (different object)
b = a[:]        # COPY (slicing)
b = list(a)     # COPY

# Deep copy for nested
import copy
b = copy.deepcopy(a)
```

### 4. Closure Late Binding
```python
# ❌ BUG: All functions return 2
funcs = [lambda: i for i in range(3)]
[f() for f in funcs]  # [2, 2, 2]

# ✅ FIX: Capture value
funcs = [lambda i=i: i for i in range(3)]
[f() for f in funcs]  # [0, 1, 2]
```

### 5. Tuple Mutability Gotcha
```python
t = ([1, 2], [3, 4])
t[0].append(5)  # Works! List inside tuple is mutable
# t = ([1, 2, 5], [3, 4])
```

### 6. Chained Comparison
```python
1 < 2 < 3      # True (not (1 < 2) < 3)
1 < 2 > 0      # True (1 < 2 and 2 > 0)
```

---

## 🎯 COMMON PATTERNS

### Flatten Nested Dict
```python
def flatten(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
```

### Two Sum
```python
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return (seen[target - n], i)
        seen[n] = i
```

### Group By
```python
from collections import defaultdict
grouped = defaultdict(list)
for item in items:
    grouped[item['key']].append(item)
```

### Counter
```python
from collections import Counter
counts = Counter(['a', 'b', 'a', 'c', 'a'])
counts.most_common(2)  # [('a', 3), ('b', 1)]
```

---

## 🐍 BUILT-IN FUNCTIONS

### Iteration
```python
enumerate(lst)            # [(0, 'a'), (1, 'b'), ...]
zip(lst1, lst2)           # Pair up
reversed(lst)             # Reverse iterator
sorted(lst, key=lambda x: x[1])  # Sort by key
```

### Filtering
```python
filter(lambda x: x > 0, lst)      # Keep positives
map(lambda x: x * 2, lst)         # Transform
any([False, True, False])         # True (any true?)
all([True, True, False])          # False (all true?)
```

### Aggregation
```python
sum(lst)
min(lst)
max(lst)
len(lst)
```

---

## 💡 INTERVIEW TIPS

1. **"is vs ==" always clarify which you need**
2. **Never mutate while iterating**
3. **Use `get()` for safe dict access**
4. **Generators for large data**
5. **defaultdict for grouping**
6. **Counter for counting**
