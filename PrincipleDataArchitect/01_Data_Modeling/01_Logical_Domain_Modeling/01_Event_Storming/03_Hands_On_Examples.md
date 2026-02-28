# Event Storming — Hands-On Examples

> Real SQL/Python/Spark code, configuration examples, before-vs-after comparisons, exercises.

---

## Example 1: E-Commerce — From Sticky Notes to Schema

### The Event Storming Output

After a 2-hour Big Picture session, the team identified these key events for Order Management:

```
Customer Registered → Product Viewed → Cart Updated → Checkout Started →
Address Validated → Coupon Applied → Payment Initiated → Payment Captured →
Order Confirmed → Inventory Reserved → Shipment Created → Shipment Dispatched →
Tracking Updated → Shipment Delivered → Review Solicited → Review Submitted
```

### Translating Events → Fact Table

```sql
-- ============================================================
-- FACT TABLE: Derived directly from the event timeline
-- Each row = one domain event that actually happened
-- ============================================================

CREATE TABLE fact_order_events (
    event_id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_type          VARCHAR(50)   NOT NULL,    -- 'ORDER_PLACED', 'PAYMENT_CAPTURED', etc.
    event_timestamp     TIMESTAMPTZ   NOT NULL,    -- when the event occurred
    
    -- Foreign keys to dimensions (discovered as Aggregates in Phase 3)
    order_id            BIGINT        NOT NULL,
    customer_id         BIGINT        NOT NULL,
    product_id          BIGINT,                    -- NULL for non-product events
    
    -- Event-specific payload (flexible schema)
    event_payload       JSONB,
    
    -- Audit fields
    ingested_at         TIMESTAMPTZ   DEFAULT NOW(),
    source_system       VARCHAR(30)   NOT NULL     -- 'web_app', 'mobile_app', 'pos'
);

-- Partition by month for performance at scale
-- (This decision comes from knowing the query patterns — Phase 4 Read Models)
CREATE TABLE fact_order_events_2025_01 
    PARTITION OF fact_order_events 
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### Translating Aggregates → Dimension Tables

```sql
-- ============================================================
-- DIMENSION: From the "Order" Aggregate cluster (Phase 3)
-- ============================================================

CREATE TABLE dim_order (
    order_sk            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id            BIGINT        NOT NULL,    -- Natural key (business key)
    customer_id         BIGINT        NOT NULL,
    
    order_status        VARCHAR(30)   NOT NULL,    -- Derived from latest event
    total_amount        DECIMAL(12,2),
    currency_code       CHAR(3)       DEFAULT 'USD',
    coupon_code         VARCHAR(20),
    shipping_method     VARCHAR(30),
    
    -- SCD Type 2 fields
    effective_from      TIMESTAMPTZ   NOT NULL,
    effective_to        TIMESTAMPTZ   DEFAULT '9999-12-31',
    is_current          BOOLEAN       DEFAULT TRUE,
    
    CONSTRAINT uq_order_natural UNIQUE (order_id, effective_from)
);

-- ============================================================
-- DIMENSION: From the "Customer" Aggregate cluster
-- ============================================================

CREATE TABLE dim_customer (
    customer_sk         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id         BIGINT        NOT NULL,
    
    email               VARCHAR(255),
    full_name           VARCHAR(200),
    registration_date   DATE,
    customer_tier       VARCHAR(20),              -- 'FREE', 'PREMIUM', 'ENTERPRISE'
    
    -- SCD Type 2
    effective_from      TIMESTAMPTZ   NOT NULL,
    effective_to        TIMESTAMPTZ   DEFAULT '9999-12-31',
    is_current          BOOLEAN       DEFAULT TRUE
);
```

### Translating Bounded Contexts → Kafka Topics

```yaml
# ============================================================
# KAFKA TOPICS: One namespace per Bounded Context (Phase 3)
# ============================================================

# Bounded Context: Order Management
topics:
  - name: order-mgmt.cart.events
    partitions: 6
    partition_key: customer_id      # Group by customer for ordering
    value_schema: CartEvent.avsc
    retention_ms: 604800000         # 7 days

  - name: order-mgmt.order.events
    partitions: 12
    partition_key: order_id         # All events for same order → same partition
    value_schema: OrderEvent.avsc
    retention_ms: 2592000000        # 30 days

# Bounded Context: Payments
  - name: payments.payment.events
    partitions: 12
    partition_key: payment_id
    value_schema: PaymentEvent.avsc
    retention_ms: 7776000000        # 90 days (compliance)

# Bounded Context: Fulfillment
  - name: fulfillment.shipment.events
    partitions: 6
    partition_key: shipment_id
    value_schema: ShipmentEvent.avsc
    retention_ms: 2592000000        # 30 days
```

### Translating Policies → dbt Transformation Logic

```sql
-- ============================================================
-- dbt Model: Implements the policy "WHEN Payment Failed 3x → Cancel Order"
-- Discovered as a purple sticky note in Phase 4
-- ============================================================

-- models/marts/order_auto_cancellations.sql

WITH failed_payments AS (
    SELECT 
        order_id,
        COUNT(*) AS failure_count,
        MAX(event_timestamp) AS last_failure_at
    FROM {{ ref('stg_payment_events') }}
    WHERE event_type = 'PAYMENT_FAILED'
    GROUP BY order_id
    HAVING COUNT(*) >= 3
),

active_orders AS (
    SELECT order_id, order_status
    FROM {{ ref('dim_order') }}
    WHERE is_current = TRUE
      AND order_status NOT IN ('CANCELLED', 'DELIVERED')
)

SELECT 
    ao.order_id,
    fp.failure_count,
    fp.last_failure_at,
    'AUTO_CANCEL' AS cancellation_reason
FROM active_orders ao
JOIN failed_payments fp ON ao.order_id = fp.order_id
```

---

## Example 2: Translating Read Models → Materialized Views

From Phase 4, the team identified this Read Model: *"Admin Dashboard needs: daily revenue + order count + return rate"*

```sql
-- ============================================================
-- MATERIALIZED VIEW: Directly from the green "Read Model" sticky note
-- ============================================================

CREATE MATERIALIZED VIEW mv_daily_business_metrics AS
SELECT 
    DATE_TRUNC('day', e.event_timestamp) AS metric_date,
    
    -- Revenue metrics
    COUNT(DISTINCT CASE WHEN e.event_type = 'ORDER_CONFIRMED' 
                        THEN e.order_id END) AS orders_placed,
    SUM(CASE WHEN e.event_type = 'PAYMENT_CAPTURED' 
             THEN (e.event_payload->>'amount')::DECIMAL END) AS total_revenue,
    
    -- Return metrics
    COUNT(DISTINCT CASE WHEN e.event_type = 'RETURN_REQUESTED' 
                        THEN e.order_id END) AS returns_requested,
    
    -- Calculated
    ROUND(
        COUNT(DISTINCT CASE WHEN e.event_type = 'RETURN_REQUESTED' THEN e.order_id END)::DECIMAL /
        NULLIF(COUNT(DISTINCT CASE WHEN e.event_type = 'ORDER_CONFIRMED' THEN e.order_id END), 0) * 100,
        2
    ) AS return_rate_pct

FROM fact_order_events e
GROUP BY 1
ORDER BY 1 DESC;

-- Refresh daily via Airflow
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_business_metrics;
```

---

## Exercise: Run Your Own Mini Event Storming

### Solo Exercise (15 minutes)

1. **Pick a domain you know well** (your team's data pipeline, your company's signup flow, or even ordering pizza)
2. **Timer: 5 minutes** — Write every "thing that happens" as a past-tense event on paper/sticky notes
3. **Timer: 5 minutes** — Arrange them left-to-right chronologically
4. **Timer: 5 minutes** — Circle clusters of related events and name the aggregate

### Questions to Answer After the Exercise

- How many events did you discover? (If < 10, you're not going deep enough)
- Did you find any "branches" where the flow can go in two directions?
- Did you find any "loops" where the process cycles back?
- Were there any "hot spots" where you weren't sure what happens?

### Team Exercise (2 hours)

1. Book a room with a large empty wall (or open a Miro board)
2. Invite: 1-2 engineers, 1 product manager, 1 domain expert, 1 QA
3. Follow the 4 phases above
4. Photograph the wall at the end — this IS your domain model's first draft
