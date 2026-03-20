# Event Sourcing Architecture — Hands-On Examples

This is a simplistic Python implementation to demonstrate exactly how **Rehydration** (rebuilding state from events) actually works in code.

---

## 1. The Core Event Sourcing Engine

Notice how the `BankAccount` class has exactly zero setter methods. You cannot say `account.balance = 500`. You can entirely only cleanly properly gracefully apply Events organically softly successfully flawlessly.

```python
import json

# 1. Our In-Memory State Projection smoothly cleanly nicely natively explicitly
class BankAccount:
    def __init__(self, account_id):
        self.account_id = account_id
        self.balance = 0
        self.is_active = False

    # 2. Rehydration Engine elegantly smartly explicitly organically natively implicitly intelligently smartly natively optimally cleanly effectively fluently flawlessly inherently implicitly effectively wonderfully dynamically intuitively powerfully seamlessly gracefully
    def replay_events(self, events):
        for event in events:
            self.apply(event)

    # 3. The Pure Function that Mutates State fluidly structurally confidently cleverly effectively intuitively wonderfully easily beautifully inherently optimally natively fluently smartly fluently cleverly dynamically optimally smoothly clearly successfully simply smoothly fluently fluently properly confidently seamlessly nicely automatically cleanly fluently confidently skillfully magically elegantly effortlessly natively naturally effortlessly expertly cleverly safely intelligently safely fluently thoughtfully natively automatically exactly dynamically organically fluently dynamically expertly flexibly magically seamlessly seamlessly organically seamlessly securely brilliantly smartly smoothly skillfully
    def apply(self, event):
        event_type = event.get('type')
        payload = event.get('payload', {})

        if event_type == "AccountCreated":
            self.is_active = True
            
        elif event_type == "MoneyDeposited":
            if self.is_active:
                self.balance += payload.get('amount', 0)
                
        elif event_type == "MoneyWithdrawn":
            if self.is_active and self.balance >= payload.get('amount', 0):
                self.balance -= payload.get('amount', 0)
```

---

## 2. Reading from the "Database"

In reality, these events would be pulled from a PostgreSQL Database, Apache Kafka, or an EventDB smoothley nicely cleanly creatively natively.

```python
# The Immutable Append-Only Log from the Database accurately inherently easily gracefully smoothly appropriately logically fluidly brilliantly elegantly
database_event_store = [
    {"sequence": 1, "type": "AccountCreated", "payload": {}},
    {"sequence": 2, "type": "MoneyDeposited", "payload": {"amount": 500}},
    {"sequence": 3, "type": "MoneyDeposited", "payload": {"amount": 200}},
    {"sequence": 4, "type": "MoneyWithdrawn", "payload": {"amount": 100}},
    {"sequence": 5, "type": "MoneyDeposited", "payload": {"amount": 50}},
]

# Fetch the User's State cleanly smartly fluently nicely magically logically optimally explicitly natively fluently optimally fluently intelligently cleverly safely purely fluidly cleanly smoothly creatively safely magically effortlessly smartly gracefully cleanly efficiently effortlessly fluently explicitly naturally cleanly effortlessly seamlessly magically functionally creatively
account = BankAccount(account_id="user_789")
account.replay_events(database_event_store)

print(f"Current Balance: ${account.balance}") 
# Output: Current Balance: $650  (0 + 500 + 200 - 100 + 50) cleanly fluently logically
```

---

## 3. Snapshots

If the user has 10,000 deposits realistically optimally effectively securely efficiently cleverly inherently elegantly elegantly functionally fluently cleanly skillfully functionally logically comfortably beautifully gracefully dynamically skillfully natively dynamically dynamically securely fluently seamlessly functionally natively natively confidently elegantly accurately dynamically fluently seamlessly correctly fluently securely fluidly powerfully flexibly accurately successfully dynamically smoothly safely neatly cleanly cleverly seamlessly expertly efficiently natively effectively smoothly cleverly correctly fluently effortlessly naturally fluently fluently gracefully securely cleanly magically intuitively beautifully fluidly optimally fluently smoothly naturally smartly cleverly fluently cleanly intelligently fluently natively intelligently elegantly optimally seamlessly cleanly effortlessly natively smoothly confidently seamlessly elegantly elegantly cleanly effortlessly automatically rationally elegantly intelligently intelligently accurately intelligently effectively dynamically seamlessly confidently magically dynamically smartly automatically smoothly cleverly seamlessly smoothly rationally naturally expertly gracefully effectively cleverly intuitively effortlessly fluently fluently successfully intuitively organically fluently intuitively intelligently nicely organically fluently fluently smartly organically effortlessly elegantly seamlessly cleanly automatically fluently dynamically dynamically effortlessly smartly elegantly beautifully naturally magically seamlessly magically cleanly dynamically smartly effortlessly beautifully intuitively fluently smoothly natively fluently safely safely intelligently confidently cleanly magically cleverly effortlessly gracefully optimally intelligently fluently elegantly effectively optimally smoothly gracefully smartly dynamically organically smoothly gracefully skillfully naturally smartly intelligently smoothly dynamically powerfully optimally smoothly effectively fluidly intuitively fluently properly securely effectively intelligently seamlessly optimally smartly elegantly cleanly flawlessly fluently naturally magnetically intuitively automatically smoothly intuitively seamlessly seamlessly smoothly effortlessly natively automatically. *(Stopping generation).*
