# Python OOP & Internals Cheat Sheet

> **Lead Data Engineer / Staff Engineer Interview Prep**
> 
> 📓 Interactive Notebook: [05_python_oop_deep_dive.ipynb](file:///c:/Users/sivan/Learning/Code/sparkantrigravity/Interview_Prep_Project/03_Python/05_python_oop_deep_dive.ipynb)

---

## 🔧 Magic Methods Quick Reference

### Object Representation
```python
__repr__(self)  # Developer-facing: repr(obj), debugging, logs
__str__(self)   # User-facing: str(obj), print(obj)
```
> 💡 **Rule**: Always implement `__repr__`. If `__str__` is missing, Python uses `__repr__`.

### Container Emulation (Make Objects Behave Like Lists/Dicts)
```python
__len__(self)           # len(obj)
__getitem__(self, key)  # obj[key]
__setitem__(self, k, v) # obj[key] = value
__contains__(self, x)   # x in obj
__iter__(self)          # for item in obj
```

### Operators
```python
__add__(self, other)  # obj + other
__sub__(self, other)  # obj - other
__eq__(self, other)   # obj == other
__lt__(self, other)   # obj < other
__hash__(self)        # hash(obj) - required for dict keys/sets
```

### Callable & Context Manager
```python
__call__(self, ...)         # obj() - makes instance callable
__enter__(self)             # with obj as x:
__exit__(self, exc, val, tb)
```

---

## 🏗️ Object Creation: `__new__` vs `__init__`

```
Class()  →  __new__(cls)  →  __init__(self)  →  Ready Object
             ↓ Creates        ↓ Initializes
             Returns instance Returns None
```

| Aspect | `__new__` | `__init__` |
|--------|-----------|------------|
| **Purpose** | Create the object | Initialize the object |
| **First Arg** | `cls` (class) | `self` (instance) |
| **Returns** | Must return instance | Must return `None` |
| **When Override** | Singletons, immutable types | Almost always |

### When to Use `__new__`
```python
# 1. Singleton Pattern
class Singleton:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# 2. Subclassing Immutable Types
class UpperStr(str):
    def __new__(cls, value):
        return super().__new__(cls, value.upper())
```

> ⚠️ **Gotcha**: If `__new__` returns instance of different class, `__init__` is SKIPPED!

---

## 🔒 Encapsulation & Name Mangling

| Convention | Syntax | Behavior |
|------------|--------|----------|
| Public | `self.name` | Accessible everywhere |
| Protected | `self._name` | "Internal use" (convention only) |
| Private | `self.__name` | Name mangled to `_ClassName__name` |

```python
class Account:
    def __init__(self):
        self.__secret = "1234"

a = Account()
# a.__secret          # ❌ AttributeError
a._Account__secret    # ✅ Works (but don't do this)
```

---

## 🧩 Design Patterns for Data Engineers

### Mixins (Composition over Inheritance)
```python
class LoggingMixin:
    def log(self, msg):
        print(f"[{self.__class__.__name__}] {msg}")

class S3Mixin:
    def read_s3(self, path): ...

class ETLJob(LoggingMixin, S3Mixin):
    def run(self):
        self.log("Starting...")
        data = self.read_s3("s3://bucket/data")
```

### Descriptors (How @property Works)
```python
class IntField:
    def __init__(self, name):
        self.name = name
    
    def __get__(self, obj, owner):
        return obj.__dict__.get(self.name)
    
    def __set__(self, obj, value):
        if not isinstance(value, int):
            raise TypeError(f"{self.name} must be int")
        obj.__dict__[self.name] = value

class Schema:
    row_count = IntField("row_count")
```

### Wrapper Pattern (`__getattr__`)
```python
class DataFrameWrapper:
    def __init__(self, df):
        self._df = df
    
    def custom_method(self):
        return "Custom behavior"
    
    def __getattr__(self, name):
        # Delegate to underlying DataFrame
        return getattr(self._df, name)
```

---

## 🎯 MRO (Method Resolution Order)

Python uses **C3 Linearization** to resolve the Diamond Problem.

```python
class A: pass
class B(A): pass
class C(A): pass
class D(B, C): pass

print(D.mro())
# [D, B, C, A, object]
```

> 💡 **Rule**: Left-to-right, depth-first, but child before parent.

---

## 🧠 Interview Quick Hits

| Question | Answer |
|----------|--------|
| `is` vs `==` | `is` = identity (same object), `==` = equality (same value) |
| `__slots__` purpose | Memory optimization, no `__dict__` |
| `@staticmethod` vs `@classmethod` | static: no implicit arg, class: gets `cls` |
| `__getattr__` vs `__getattribute__` | `getattr`: only on miss, `getattribute`: every access |
| Why `super()`? | Correctly handles MRO in multiple inheritance |

---

## ⚡ One-Liners to Remember

```python
# Check MRO
ClassName.mro()

# Check if class attribute is descriptor
hasattr(attr, '__get__')

# Get all magic methods
[m for m in dir(obj) if m.startswith('__')]

# Check instance creation
type(instance).__name__
```
