# RabbitMQ Architecture — Hands-On Examples

While RabbitMQ execution generally completely happens natively via AMQP Client Libraries (Pika for Python, amqplib for Node.js), we can conceptualize the literal API mechanically.

## Scenario 1: Setting up the Core Geometric Routing (Fanout)

Imagine a social media application where a user uploads a new post. Three separate microservices completely care about this exactly simultaneously:
1. Standard Newsfeed ingestion.
2. Push Notifications (FCM/APNS).
3. Search Indexer (Elasticsearch).

### Execution (Pseudo-Code / Logic)

```javascript
// The Administrator structurally declares the Architecture ONCE natively.

// 1. We create a "Fanout" Exchange. This explicitly ignores explicit targeting keys 
// and acts as a massive broadcast tower.
channel.assertExchange('new_post_broadcast', 'fanout', { durable: true });

// 2. We explicitly generate 3 isolated physical task Queues.
channel.assertQueue('newsfeed_updater_queue', { durable: true });
channel.assertQueue('push_notification_queue', { durable: true });
channel.assertQueue('elasticsearch_indexer_queue', { durable: true });

// 3. We absolutely mathematically "Bind" all 3 queues physically directly to the Fanout Exchange.
channel.bindQueue('newsfeed_updater_queue', 'new_post_broadcast', '');
channel.bindQueue('push_notification_queue', 'new_post_broadcast', '');
channel.bindQueue('elasticsearch_indexer_queue', 'new_post_broadcast', '');
```

---

## Scenario 2: The Producer (Emitting the Event)

The Core API microservice executes perfectly decoupled logic. It does not literally physically know the Search Indexer exists structurally. 

### Execution (Node.js)

```javascript
const newPostData = { user_id: 1104, content: "Hello world" };

// The API mathematically drops the payload completely blindly exclusively into the Exchange.
// The Exchange fundamentally perfectly duplicates the message mechanically into all 3 bound queues instantly.
channel.publish(
  'new_post_broadcast',   // The Exchange name
  '',                     // Empty routing key (Fanout entirely ignores this)
  Buffer.from(JSON.stringify(newPostData)),
  { persistent: true }    // Tell RabbitMQ to mathematically save this physically to hard drive
);

// The Core API immediately responds HTTP 200 OK directly to the User's browser.
```

---

## Scenario 3: The Consumer (Acknowledging Completion)

We examine the exact Python logic the Push Notification cluster runs continuously.

### Execution (Python with Pika)

```python
def generate_and_push_notification(ch, method, properties, body):
    try:
        data = json.loads(body)
        
        # Simulated mathematical heavy lifting (Communicating outwardly to Apple APNS)
        apns.send_push(data['user_id'], "New Post created!")
        
        # The Push succeeded structurally perfectly. 
        # The Worker structurally commands RabbitMQ to physically DELETE the message mechanically.
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print("Success: Message Acknowledged and Deleted from Queue.")

    except Exception as e:
        # A catastrophic network failure hitting Apple's servers mechanically occurred.
        # We explicitly command RabbitMQ to NACK the message and actively place it 
        # structurally mathematically back at the front of the line to retry securely later.
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        print("Failure: Re-Queuing Message.")

# The Consumer subscribes explicitly to its specific physical Queue via TCP Persistent connection.
channel.basic_consume(
    queue='push_notification_queue', 
    on_message_callback=generate_and_push_notification, 
    auto_ack=False  # CRITICAL: We explicitly manually control deletion exclusively.
)

channel.start_consuming()
```
