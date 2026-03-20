# Apache Kafka Architecture — Hands-On Examples

The standard way to interact with Kafka is via native Java/Python/Go client libraries inside your microservices. However, DevOps and Architects heavily use the built-in Kafka bash scripts to debug streams manually.

## Scenario 1: Creating a Topic with Horizontal Scale

Before producing or consuming data, the Administrator must physically structure the log geometry.

### Execution (Terminal)

```bash
# We create a new topic for analyzing live credit card transactions.
# We explicitly specify 12 Partitions, meaning we can horizontally scale identical
# Fraud Detection Microservices to a maximum of exactly 12 parallel nodes.
# We specify Replication Factor 3, meaning Kafka will perfectly mirror the data 
# across 3 separate physical servers so we can survive hardware rack failures.

kafka-topics.sh \
  --bootstrap-server my-kafka-broker:9092 \
  --create \
  --topic credit_card_transactions \
  --partitions 12 \
  --replication-factor 3
```

---

## Scenario 2: Producing Data (The Checkout Service)

In reality, your Node.js application executes this. But for debugging, we can manually inject JSON events heavily into the physical partition log.

### Execution (Terminal)

```bash
# This opens a raw interactive prompt. Every time you hit enter, a message hits the cluster.
kafka-console-producer.sh \
  --bootstrap-server my-kafka-broker:9092 \
  --topic credit_card_transactions

> {"user_id": 402, "amount": 100.50, "status": "APPROVED"}
> {"user_id": 912, "amount": 5.00, "status": "DENIED"}
> {"user_id": 881, "amount": 4500.00, "status": "APPROVED"}
```

---

## Scenario 3: Consuming Data (The Fraud Detection Service)

We emulate a microservice spinning up and subscribing to the massive firehose of data.

### Execution (Terminal)

```bash
# We connect as an explicit member of the "fraud_detector_group" consumer group.
# Notice the '--from-beginning' flag. If this is our very first time booting up, 
# Kafka forces us to read the multi-Terabyte backlog perfectly linearly from the 
# absolute start of time before processing real-time tail events.
kafka-console-consumer.sh \
  --bootstrap-server my-kafka-broker:9092 \
  --topic credit_card_transactions \
  --group fraud_detector_group \
  --from-beginning
```

---

## Scenario 4: Diagnosing the "Lag" Crisis

The Data Engineering team's absolute worst nightmare is **Consumer Lag**. 

If the Checkout Service is producing 10,000 credit card swipes a second, but the Fraud Detection servers are heavily bottlenecked on CPU and only processing 2,000 a second, the queue violently builds up. Fraud alerts will trigger 45 minutes late, rendering them completely useless.

We can execute an administrative command to definitively measure exactly how badly the consumers are failing.

### Execution (Terminal)

```bash
# Evaluate exactly where the Consumer Group bookmark is positioned versus the Head of the log
kafka-consumer-groups.sh \
  --bootstrap-server my-kafka-broker:9092 \
  --describe \
  --group fraud_detector_group

# OUTPUT EXPLANATION:
# TOPIC                     PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG     CONSUMER-ID
# credit_card_transactions  0          500000          500005          5       fraud-node-1
# credit_card_transactions  1          490000          900000          410000  fraud-node-2

# The Architect instantly realizes Partition 1 has a massive LAG of 410,000 messages. 
# Node 2 is catastrophically failing or mathematically bottlenecked. 
# The Architect must immediately spin up more containers to horizontally absorb the load.
```
