# AWS SQS & SNS Architecture — Concept Overview

## Why This Exists

If Apache Kafka is for massive Big Data streams, and RabbitMQ is for highly-customizable traditional routing, **AWS SQS & SNS** is for building infinitely scalable, zero-maintenance Distributed Systems purely inside the AWS Ecosystem.

When building true Cloud-Native microservices, organizations rarely want to manage their own Kafka clusters or RabbitMQ nodes. They want a fully managed service that structurally scales from 0 messages a day to 10 billion messages a day without ever managing infrastructure.

*   **SQS (Simple Queue Service):** AWS's fully managed Message Queue (Point-to-Point).
*   **SNS (Simple Notification Service):** AWS's fully managed Pub/Sub Messaging engine (Broadcast/Fanout).

---

## What is Amazon SQS?

SQS is the ultimate decouple mechanism for processing tasks.
*   **The Paradigm:** It is a Pull-Based (Polling) queue. Workers explicitly ask SQS, *"Do you have any work for me?"*
*   **The Scale:** SQS scales perfectly. You can dump 100,000 messages onto a queue instantly, and it provides practically unlimited throughput.

### The "Visibility Timeout" Lock
When a worker pulls a message from SQS:
1. SQS does **not** immediately delete it.
2. Instead, SQS initiates a **Visibility Timeout** (e.g., 30 Seconds) and hides the message from all other polling workers.
3. If the worker successfully processes the data and issues a specific `DeleteMessage` API call, SQS permanently deletes it.
4. If the worker crashes, the 30-second Visibility Timeout expires. The message natively "re-appears" visibly back in the queue, allowing another worker to pick it up and retry the execution cleanly.

---

## What is Amazon SNS?

While SQS is exactly one-to-one (One message processed by One worker), **SNS is exclusively One-to-Many**.
*   **The Paradigm:** Push-Based Publishing. A service drops a single message into an SNS "Topic".
*   **The Subscribers:** SNS instantly and actively pushes a copy of that message out to every subscribed endpoint.
*   **Valid Subscribers:** SNS can actively push messages securely into SQS Queues, AWS Lambda functions, HTTP/HTTPS webhooks, Email, or SMS endpoints.
