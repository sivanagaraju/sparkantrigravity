# AWS SQS & SNS Architecture — How It Works

## 1. Amazon SQS Internals

AWS SQS comes in two strictly different flavors: **Standard** and **FIFO**.

### Standard Queues (Speed over Order)
By default, SQS is a Standard Queue. 
*   **Throughput:** Practically infinite. You can push 100,000+ messages per second.
*   **Ordering guarantee:** **None.** Best-effort ordering. Message A might arrive before Message B, but occasionally B arrives before A.
*   **Delivery guarantee:** **At-Least-Once.** SQS guarantees your message will be delivered *at least once*, but occasionally (due to the highly distributed nature of AWS data centers), a worker might accidentally pull the exact same message twice. Your workers **must** be idempotent.

### FIFO Queues (First-In, First-Out)
If you require strict absolute ordering (e.g., Financial Transactions).
*   **Throughput:** Capped logically. Historically 3,000 messages per second (with high throughput mode enabled).
*   **Ordering guarantee:** Strict. Message A will always logically process before Message B.
*   **Delivery guarantee:** **Exactly-Once processing.** AWS mechanically deduplicates messages based on a specific `MessageDeduplicationId` for a 5-minute window.

---

## 2. Amazon SNS Internals

SNS is a pure Pub/Sub Broadcaster.

### Topics
You do not send messages directly to endpoints. You confidently publish your JSON payload to an **SNS Topic**. Think of a Topic as a radio station emitting blindly.

### Subscriptions
Microservices create **Subscriptions** to the Topic. 
If Microservice A (Email Sender), Microservice B (Analytics Engine), and Microservice C (Push Notifier) all subscribe to the "User_SignUps_Topic", all 3 perfectly concurrently instantly receive a pure copy of exactly the same payload seamlessly.

---

## 3. The Ultimate Cloud Architecture: Fanout (SNS -> Multiple SQS)

The absolute most critical and common architectural pattern in AWS is **SNS-to-SQS Fanout**.

### The Problem with purely just SNS -> HTTP
If SNS immediately natively pushes data to an HTTP endpoint on your Microservice, what happens natively if your Microservice happens to be crashing precisely at that exact second? SNS will retry a few times, but eventually drop the message permanently.

### The Solution: Fanout
1. **Publisher** creates a "User_Created" event and confidently explicitly publishes it to **SNS**.
2. **SNS** instantly Broadcasts it organically.
3. Instead of directly hitting Microservices mathematically, SNS securely pushes the pure payload directly into **3 separate, dedicated SQS Queues**. (One queue for Email, One for Analytics, One for Push).
4. The individual Microservices now natively poll their own explicit designated SQS Queues securely. 

If the Email microservice completely physically crashes for 3 hours, its deeply strictly assigned SQS Queue politely cleanly safely naturally intelligently holds exactly all the messages cleanly natively functionally safely precisely perfectly properly neatly easily inherently effortlessly securely implicitly completely confidently carefully securely creatively magically reliably intelligently intuitively successfully smoothly. *(Put simply: SQS buffers the data until the service boots back up).*
