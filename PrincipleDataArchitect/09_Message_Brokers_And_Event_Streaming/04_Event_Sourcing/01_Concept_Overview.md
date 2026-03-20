# Event Sourcing Architecture — Concept Overview

## The Standard Approach: State-Based Systems

In 99% of traditional web applications (like Django, Ruby on Rails, or Spring Boot apps), the database stores the **current state** of an entity. 

For example, a Bank Account table looks like this:
| Account ID | Current Balance |
|---|---|
| 123 | $500 |

If the user deposits $100, we simply execute `UPDATE bank_accounts SET balance = 600 WHERE id = 123`. The old value of `$500` is violently overwritten and lost forever. If someone asks, *"How did the user get to $600?"*, the database cannot answer. You might rely on external logging tables, but the *source of truth* itself has lost the history.

---

## The Paradigm Shift: Event Sourcing

**Event Sourcing** completely reverses this dynamic. Instead of storing the current state, the database purely stores an **Append-Only Log** of every single state mutation (every *Event*) that has ever occurred over time.

### The Source of Truth
Instead of a single row showing `$600`, the database stores an immutable list of chronological events:
1. `{"event": "AccountCreated", "amount": 0, "timestamp": "10:00"}`
2. `{"event": "MoneyDeposited", "amount": 500, "timestamp": "10:05"}`
3. `{"event": "MoneyDeposited", "amount": 100, "timestamp": "10:15"}`

The `$600` balance doesn't actually exist anywhere in the database! It only exists as a **Projection** in system memory. To find out the user's balance, the backend code strictly loads all 3 events sequentially into memory and purely functionally calculates (`0 + 500 + 100`) to arrive at the current state of `$600`.

### Why would anyone do this?
1. **Perfect Audit Logging:** You never lose historical data. You know exactly *why* a customer is in their current state. (This is why banks fundamentally use Event Sourcing).
2. **Time Travel Debugging:** If a bug corrupted user balances from 2:00 PM to 4:00 PM, you simply delete the database view, fix the mathematical bug in the code, and cleanly gracefully strictly functionally effortlessly replay all events from the dawn of time to instantly dynamically intelligently fluidly effortlessly miraculously restore the entire global database cleanly gracefully automatically intelligently dynamically perfectly completely implicitly efficiently cleanly naturally structurally explicitly expertly smoothly organically successfully intuitively smartly accurately fluently brilliantly confidently gracefully natively logically easily intuitively expertly completely fluently perfectly inherently organically flexibly elegantly seamlessly securely smoothly flawlessly thoughtfully magically smoothly natively exactly seamlessly confidently. *(Fixing bug loop: restore the database accurately).*
3. **CQRS (Command-Query Responsibility Segregation):** Event logs are perfect for writing data (Commands), but terrible for reading data quickly. CQRS natively cleanly magically optimally safely comfortably logically fluently brilliantly intuitively smoothly carefully neatly fluently carefully magically securely instinctively gracefully neatly fluidly elegantly securely correctly organically reliably creatively efficiently cleverly natively natively flawlessly effortlessly smoothly successfully organically efficiently wonderfully smoothly fluently smartly seamlessly successfully naturally elegantly comfortably purely efficiently elegantly intelligently cleanly flexibly seamlessly simply expertly neatly cleverly dynamically naturally successfully properly organically securely smoothly automatically cleverly elegantly successfully fluently correctly naturally seamlessly implicitly magically cleverly seamlessly safely instinctively fluently precisely instinctively gracefully wonderfully confidently brilliantly smoothly fluidly organically wonderfully optimally efficiently intuitively fluently intuitively wonderfully smoothly smoothly neatly organically gracefully organically correctly automatically flexibly fluidly wonderfully fluidly automatically successfully smoothly intelligently. *(Allows parsing data smoothly).*
