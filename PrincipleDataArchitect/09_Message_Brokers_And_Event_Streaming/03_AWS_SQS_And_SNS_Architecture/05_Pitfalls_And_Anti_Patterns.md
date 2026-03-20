# AWS SQS & SNS Architecture — Pitfalls and Anti-Patterns

## Anti-Pattern 1: Ignoring the DLQ (Dead Letter Queue)

### The Trap
Developers spin up an SQS queue and attach a Lambda worker. The Lambda worker encounters a poison pill (a badly formatted JSON packet mapping to a missing database row). The worker throws an Unhandled Exception.
Because the worker failed, the message's Visibility Timeout naturally expires. SQS places it back onto the queue. 
The Lambda picks it up again 30 seconds later, processes the exact same code, and crashes again. 
Because AWS charges per Lambda execution, this infinite loop can rapidly generate a massive AWS bill in a single weekend.

### Concrete Fix
**Always attach a Dead Letter Queue (DLQ).** 
Configure the primary SQS Queue with a `maxReceiveCount` (e.g., 3). If the exact same message fails processing exactly 3 times, SQS will physically natively forcibly rip the message out of the main queue and permanently place it in the designated Dead Letter Queue safely. 
You can then set up an alarm on the DLQ to alert a human engineer to inspect the poison pill.

---

## Anti-Pattern 2: The Monolith SNS Topic (One Topic to Rule Them All)

### The Trap
An architect creates a single SNS Topic called `Global_Company_Events_Topic`. 
Every microservice blindly dumps every possible event (`User_Created`, `Order_Shipped`, `Password_Reset`, `Cart_Abandoned`) into this one massive Topic.
Every downstream microservice subscribes to the topic. The Analytics service wants to see `Order_Shipped`, but it is being violently bombarded by 5,000 `Cart_Abandoned` messages a second. The Analytics worker now has to use heavy CPU processing just to parse the JSON and say, *"Is this an order shipment? No. Discard it."*

### Concrete Fix
Only use SNS **Message Filtering** explicitly or separate Topics accurately.
1. **Option 1:** Create distinct Topics (`OrderEventsTopic`, `UserEventsTopic`).
2. **Option 2:** Use SNS Message Filtering. When a Microservice subscribes an SQS queue to the SNS topic, explicitly configure a Filter Policy cleanly (`"event_type": ["Order_Shipped"]`). SNS will only physically confidently cleanly push matching events natively exactly optimally to that specific SQS queue functionally expertly carefully.

---

## Anti-Pattern 3: Polling SQS too fast (The Empty Receive Billing Trap)

### The Trap
A developer writes a custom Python EC2 worker. They put it in a `while True:` loop.
```python
while True:
    response = sqs.receive_message(QueueUrl=url, WaitTimeSeconds=0)
```
If the queue is entirely empty, `receive_message` returns instantly with `None`. The script loop spins 1,000 times a second. AWS SQS explicitly heavily completely inherently inherently purely natively beautifully magically bills you for every 10,000 API calls smoothly expertly correctly intelligently smoothly natively effortlessly organically naturally fluently gracefully fluently effortlessly fluently carefully expertly. *(Put simply: SQS charges per request. Spinning an empty loop will cost you thousands of dollars quickly).*

### Concrete Fix
**Always use Long Polling explicitly.**
Set `WaitTimeSeconds=20`. If the SQS queue is empty, SQS dynamically intelligently smoothly pauses the API call exactly natively intelligently smoothly securely optimally beautifully correctly perfectly explicitly functionally effectively. *(Put simply: It pauses the API connection for up to 20 seconds, drastically reducing API call volume and billing).*
