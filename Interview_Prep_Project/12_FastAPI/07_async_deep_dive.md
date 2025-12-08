# Python Async/Await Deep Dive - Complete Guide

## 1. What is Asynchronous Programming?

### The Restaurant Analogy

Imagine a restaurant with ONE waiter:

```
SYNCHRONOUS (Blocking):
────────────────────────
Waiter takes Order 1 → Waits in kitchen → Serves → 
Waiter takes Order 2 → Waits in kitchen → Serves → 
Waiter takes Order 3 → Waits in kitchen → Serves

Each customer waits for previous customers to finish!
Total time: 30 minutes (10 min × 3)


ASYNCHRONOUS (Non-blocking):
────────────────────────────
Waiter takes Order 1 → Goes to kitchen → Comes back
Waiter takes Order 2 → Goes to kitchen → Comes back
Waiter takes Order 3 → Goes to kitchen → Comes back
Kitchen calls → Waiter serves Order 2
Kitchen calls → Waiter serves Order 1
Kitchen calls → Waiter serves Order 3

Waiter doesn't WAIT in kitchen, does other work!
Total time: 12 minutes (parallel processing)
```

### Technical Definition

**Synchronous**: Code runs line by line. Each line waits for the previous to complete.

**Asynchronous**: Code can "pause" while waiting for I/O, allowing other code to run.

```
I/O = Input/Output = WAITING for something:
- Database query → waiting for DB server
- HTTP request → waiting for remote server
- File read → waiting for disk
- User input → waiting for keyboard
```

---

## 2. The Event Loop

### What is an Event Loop?

The **event loop** is the heart of async programming. It's a loop that:
1. Runs tasks until they need to wait
2. Switches to other tasks while waiting
3. Resumes tasks when their I/O is complete

```
                    EVENT LOOP
                    ──────────
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
┌───────┐          ┌───────┐          ┌───────┐
│ Task 1│          │ Task 2│          │ Task 3│
│ (run) │──pause──▶│ (run) │──pause──▶│ (run) │
│       │          │       │          │       │
│ wait  │◀─resume──│ wait  │◀─resume──│ done  │
│ done  │          │ done  │          │       │
└───────┘          └───────┘          └───────┘

The event loop NEVER waits. It always finds something to do.
```

### Visualizing the Event Loop

```python
import asyncio

async def task_1():
    print("1: Start")
    await asyncio.sleep(2)  # Pause here, let others run
    print("1: End")

async def task_2():
    print("2: Start")
    await asyncio.sleep(1)  # Pause here, let others run
    print("2: End")

async def main():
    await asyncio.gather(task_1(), task_2())

asyncio.run(main())

# Output:
# 1: Start
# 2: Start    ← Both start immediately!
# 2: End      ← Task 2 finishes first (only 1 second)
# 1: End      ← Task 1 finishes (2 seconds total)

# Total time: 2 seconds (not 3!)
```

---

## 3. Coroutines

### What is a Coroutine?

A **coroutine** is a function that can be paused and resumed. In Python, it's created using `async def`.

```python
# Regular function
def regular_function():
    return "Hello"

# Coroutine function
async def coroutine_function():
    return "Hello"

# Calling them:
result1 = regular_function()        # Returns "Hello"
result2 = coroutine_function()      # Returns a coroutine OBJECT, not "Hello"!

print(result2)  # <coroutine object coroutine_function at 0x...>

# To get the actual result, you must AWAIT it:
result2 = await coroutine_function()  # Now returns "Hello"
```

### Coroutine States

```
┌──────────────┐
│   Created    │ ─── async def foo() called, coroutine object created
└──────┬───────┘
       │ await
       ▼
┌──────────────┐
│   Running    │ ─── Code is executing
└──────┬───────┘
       │ await something
       ▼
┌──────────────┐
│   Suspended  │ ─── Paused, waiting for I/O
└──────┬───────┘
       │ I/O complete
       ▼
┌──────────────┐
│   Running    │ ─── Resumed execution
└──────┬───────┘
       │ return
       ▼
┌──────────────┐
│   Completed  │ ─── Finished, result available
└──────────────┘
```

---

## 4. async and await Keywords

### async - Define a Coroutine

```python
async def fetch_data():
    """This is a coroutine function."""
    return "data"
```

### await - Pause and Wait

```python
async def main():
    # await = "pause here until this completes"
    result = await fetch_data()
    print(result)
```

### Rules of await

```python
# Rule 1: await can ONLY be used inside async functions
def regular_function():
    await something()  # ❌ SyntaxError!

async def async_function():
    await something()  # ✅ OK

# Rule 2: You can only await "awaitable" objects
async def example():
    await "hello"           # ❌ TypeError: can't await str
    await asyncio.sleep(1)  # ✅ OK - asyncio.sleep returns awaitable
    await fetch_data()      # ✅ OK - coroutine is awaitable
```

---

## 5. Running Async Code

### asyncio.run() - Entry Point

```python
import asyncio

async def main():
    print("Hello")
    await asyncio.sleep(1)
    print("World")

# This is how you run async code from synchronous context
asyncio.run(main())  # Creates event loop, runs main(), closes loop
```

### Multiple Ways to Run Coroutines

```python
import asyncio

async def task(name, delay):
    await asyncio.sleep(delay)
    return f"{name} done"

async def main():
    # Method 1: Sequential (slow)
    result1 = await task("A", 1)
    result2 = await task("B", 1)
    # Total: 2 seconds
    
    # Method 2: Concurrent with gather (fast)
    result1, result2 = await asyncio.gather(
        task("A", 1),
        task("B", 1)
    )
    # Total: 1 second (parallel)
    
    # Method 3: Create tasks explicitly
    task1 = asyncio.create_task(task("A", 1))
    task2 = asyncio.create_task(task("B", 1))
    result1 = await task1
    result2 = await task2
    # Total: 1 second (parallel)
```

---

## 6. asyncio.gather vs create_task

### asyncio.gather()

Runs multiple coroutines concurrently and waits for ALL to complete.

```python
import asyncio

async def fetch_user(id):
    await asyncio.sleep(1)
    return f"User {id}"

async def main():
    # All three run concurrently
    users = await asyncio.gather(
        fetch_user(1),
        fetch_user(2),
        fetch_user(3)
    )
    print(users)  # ['User 1', 'User 2', 'User 3']
    # Total time: ~1 second (not 3!)

asyncio.run(main())
```

### asyncio.create_task()

Creates a task that starts running immediately in the background.

```python
import asyncio

async def background_job():
    await asyncio.sleep(5)
    print("Background job done!")

async def main():
    # Start task in background (doesn't wait)
    task = asyncio.create_task(background_job())
    
    # Do other work while task runs
    print("Doing other work...")
    await asyncio.sleep(1)
    print("Still working...")
    
    # Now wait for the task if needed
    await task

asyncio.run(main())

# Output:
# Doing other work...
# Still working...
# (waits 4 more seconds)
# Background job done!
```

### Comparison

| Feature | gather() | create_task() |
|---------|----------|---------------|
| Starts immediately | Yes | Yes |
| Waits automatically | Yes | No (must await) |
| Returns results | As a list | Individual task |
| Error handling | Can use return_exceptions | Manual |
| Use case | Parallel operations | Background work |

---

## 7. Common Async Patterns

### Pattern 1: Parallel HTTP Requests

```python
import asyncio
import aiohttp

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def fetch_all_urls(urls):
    async with aiohttp.ClientSession() as session:
        # Fetch all URLs in parallel
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

# 10 requests in parallel = ~1 second (not 10 seconds!)
urls = ["http://example.com"] * 10
results = asyncio.run(fetch_all_urls(urls))
```

### Pattern 2: Async Database Queries

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_user_with_orders(session: AsyncSession, user_id: int):
    # Execute both queries in parallel
    user_query = select(User).where(User.id == user_id)
    orders_query = select(Order).where(Order.user_id == user_id)
    
    user_result, orders_result = await asyncio.gather(
        session.execute(user_query),
        session.execute(orders_query)
    )
    
    user = user_result.scalar_one()
    orders = orders_result.scalars().all()
    
    return {"user": user, "orders": orders}
```

### Pattern 3: Timeout

```python
import asyncio

async def slow_operation():
    await asyncio.sleep(10)
    return "done"

async def main():
    try:
        # Wait max 2 seconds
        result = await asyncio.wait_for(slow_operation(), timeout=2.0)
    except asyncio.TimeoutError:
        print("Operation timed out!")

asyncio.run(main())
```

### Pattern 4: Semaphore (Limit Concurrency)

```python
import asyncio

async def fetch_url(semaphore, url):
    async with semaphore:  # Only N concurrent requests
        print(f"Fetching {url}")
        await asyncio.sleep(1)
        return f"Result from {url}"

async def main():
    # Limit to 5 concurrent requests
    semaphore = asyncio.Semaphore(5)
    
    urls = [f"http://example.com/{i}" for i in range(20)]
    
    tasks = [fetch_url(semaphore, url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    # 20 URLs, 5 at a time = ~4 seconds (not 20!)

asyncio.run(main())
```

### Pattern 5: Producer-Consumer with Queue

```python
import asyncio

async def producer(queue, n):
    for i in range(n):
        await asyncio.sleep(0.5)  # Simulate work
        await queue.put(f"item-{i}")
        print(f"Produced item-{i}")

async def consumer(queue, name):
    while True:
        item = await queue.get()
        await asyncio.sleep(1)  # Simulate processing
        print(f"{name} consumed {item}")
        queue.task_done()

async def main():
    queue = asyncio.Queue()
    
    # Start producer and consumers
    producer_task = asyncio.create_task(producer(queue, 10))
    consumers = [
        asyncio.create_task(consumer(queue, f"Consumer-{i}"))
        for i in range(3)
    ]
    
    # Wait for producer to finish
    await producer_task
    
    # Wait for all items to be processed
    await queue.join()
    
    # Cancel consumers (they run forever)
    for c in consumers:
        c.cancel()

asyncio.run(main())
```

---

## 8. FastAPI and Async

### How FastAPI Handles Async

```
FastAPI Request Handling:
─────────────────────────

async def endpoint:
  └── Runs in event loop (non-blocking)
      └── Can use await
      └── Other requests run while waiting

def endpoint:
  └── Runs in thread pool (blocking OK)
      └── Cannot use await
      └── FastAPI handles threading
```

### When to Use async def vs def

```python
from fastapi import FastAPI
import asyncio
import time

app = FastAPI()

# ✅ USE async def FOR:
# - Database queries (async driver)
# - HTTP requests (aiohttp, httpx)
# - File I/O (aiofiles)
# - Any await operation

@app.get("/async-db")
async def get_data():
    # Async database query
    result = await db.fetch_all("SELECT * FROM users")
    return result

@app.get("/async-http")
async def call_api():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://api.example.com")
        return response.json()


# ✅ USE def FOR:
# - CPU-bound operations
# - Sync libraries (requests, some ORMs)
# - Blocking operations

@app.get("/sync-cpu")
def heavy_computation():
    # CPU-intensive work
    result = sum(range(10_000_000))
    return {"result": result}

@app.get("/sync-library")
def use_sync_library():
    # Sync library (FastAPI runs in thread pool)
    import requests
    response = requests.get("http://api.example.com")
    return response.json()


# ❌ NEVER DO THIS:
@app.get("/wrong")
async def blocking_in_async():
    time.sleep(5)  # BLOCKS ENTIRE EVENT LOOP!
    return {"message": "bad"}

# ✅ CORRECT:
@app.get("/right")
async def non_blocking():
    await asyncio.sleep(5)  # Non-blocking
    return {"message": "good"}
```

### FastAPI Dependency Injection with Async

```python
from fastapi import Depends

# Async dependency
async def get_db():
    db = await create_async_connection()
    try:
        yield db
    finally:
        await db.close()

# Sync dependency (FastAPI handles it)
def get_settings():
    return load_settings()

# Both work in async endpoint
@app.get("/users")
async def get_users(
    db = Depends(get_db),           # Async dep
    settings = Depends(get_settings) # Sync dep - OK!
):
    return await db.fetch_users()
```

---

## 9. Common Mistakes and Fixes

### Mistake 1: Blocking in Async Function

```python
# ❌ WRONG: Blocks event loop
@app.get("/bad")
async def bad_endpoint():
    import time
    time.sleep(5)  # EVERYONE WAITS!
    return {"status": "done"}

# ✅ FIX 1: Use async sleep
@app.get("/good1")
async def good_endpoint_1():
    await asyncio.sleep(5)  # Non-blocking
    return {"status": "done"}

# ✅ FIX 2: Use run_in_executor for blocking calls
@app.get("/good2")
async def good_endpoint_2():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, time.sleep, 5)  # Runs in thread
    return {"status": "done"}

# ✅ FIX 3: Use sync function (FastAPI handles threading)
@app.get("/good3")
def good_endpoint_3():  # No async!
    time.sleep(5)  # OK - runs in thread pool
    return {"status": "done"}
```

### Mistake 2: Forgetting to Await

```python
# ❌ WRONG: Coroutine never runs!
async def fetch_data():
    return "data"

async def main():
    result = fetch_data()  # Missing await!
    print(result)  # <coroutine object fetch_data at 0x...>

# ✅ CORRECT:
async def main():
    result = await fetch_data()
    print(result)  # "data"
```

### Mistake 3: Calling Async from Sync

```python
# ❌ WRONG: Can't await in regular function
def sync_function():
    result = await fetch_data()  # SyntaxError!

# ✅ FIX 1: Make it async
async def async_function():
    result = await fetch_data()

# ✅ FIX 2: Use asyncio.run() (only at top level)
def sync_function():
    result = asyncio.run(fetch_data())
```

### Mistake 4: Shared State in Concurrent Tasks

```python
# ❌ WRONG: Race condition!
counter = 0

async def increment():
    global counter
    current = counter
    await asyncio.sleep(0.1)  # Context switch here!
    counter = current + 1

async def main():
    await asyncio.gather(increment(), increment(), increment())
    print(counter)  # Might be 1, not 3!

# ✅ CORRECT: Use asyncio.Lock
counter = 0
lock = asyncio.Lock()

async def increment_safe():
    global counter
    async with lock:  # Only one task at a time
        current = counter
        await asyncio.sleep(0.1)
        counter = current + 1
```

---

## 10. Async Libraries for Python

| Category | Sync Library | Async Library |
|----------|--------------|---------------|
| HTTP Client | requests | aiohttp, httpx |
| Database | psycopg2 | asyncpg |
| ORM | SQLAlchemy | SQLAlchemy (async) |
| Redis | redis-py | aioredis / redis.asyncio |
| File I/O | open() | aiofiles |
| Sleep | time.sleep | asyncio.sleep |
| MongoDB | pymongo | motor |
| PostgreSQL | psycopg2 | asyncpg |

---

## 11. Performance Comparison

```python
import asyncio
import time

# SYNC VERSION
def sync_fetch_all():
    results = []
    for i in range(10):
        time.sleep(1)  # Simulate network
        results.append(f"Result {i}")
    return results

# Time: 10 seconds (sequential)

# ASYNC VERSION
async def async_fetch(i):
    await asyncio.sleep(1)  # Simulate network
    return f"Result {i}"

async def async_fetch_all():
    tasks = [async_fetch(i) for i in range(10)]
    return await asyncio.gather(*tasks)

# Time: 1 second (parallel)

# SPEEDUP: 10x faster!
```

---

## 12. Interview Questions

### Q: What's the difference between threading and async?

```
THREADING:                           ASYNC:
─────────                            ─────
Multiple threads                     Single thread
OS manages switching                 Event loop manages
Memory overhead per thread           Lightweight coroutines
Good for CPU-bound                   Good for I/O-bound
GIL limits parallelism               No GIL issues
```

### Q: When would you NOT use async?

```
1. CPU-bound operations (use multiprocessing)
2. Using sync-only libraries
3. Simple scripts with no I/O
4. When code complexity isn't worth the benefit
```

### Q: What happens if you forget await?

```python
async def get_data():
    return await db.query(...)

async def main():
    data = get_data()  # Returns coroutine, not data!
    # RuntimeWarning: coroutine 'get_data' was never awaited
```

### Q: How do you handle errors in gather()?

```python
async def main():
    # Default: First exception stops everything
    try:
        results = await asyncio.gather(task1(), task2())
    except Exception as e:
        print(f"One failed: {e}")
    
    # With return_exceptions: Get all results including exceptions
    results = await asyncio.gather(
        task1(), task2(), task3(),
        return_exceptions=True
    )
    # results might be: ["success", ValueError(...), "success"]
```
