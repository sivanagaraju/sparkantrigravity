# Bounded Contexts — How It Works (Deep Internals)

> Architecture, HLD, sequence diagrams, state machine, DFD, ER diagrams, and table structures.

---

## High-Level Design

```mermaid
flowchart TB
    subgraph "Bounded Context: ORDER MANAGEMENT"
        OA["Order Aggregate"]
        CA["Cart Aggregate"]
        ODB[("Order DB<br/>(PostgreSQL)")]
        OA --> ODB
        CA --> ODB
    end
    
    subgraph "Bounded Context: PAYMENTS"
        PA["Payment Aggregate"]
        RA["Refund Aggregate"]
        PDB[("Payment DB<br/>(PostgreSQL)")]
        PA --> PDB
        RA --> PDB
    end
    
    subgraph "Bounded Context: FULFILLMENT"
        SA["Shipment Aggregate"]
        FDB[("Fulfillment DB<br/>(PostgreSQL)")]
        SA --> FDB
    end
    
    subgraph "Integration Layer"
        K["Apache Kafka<br/>(Event Bus)"]
    end
    
    subgraph "Analytics"
        DW["Data Warehouse<br/>(Snowflake)"]
        CD["Conformed Dimensions<br/>(bridge BCs)"]
        DW --> CD
    end
    
    ODB -->|CDC / Debezium| K
    PDB -->|CDC / Debezium| K
    FDB -->|CDC / Debezium| K
    K -->|ETL| DW
```

## Context Map — Relationships Between Bounded Contexts

```mermaid
flowchart LR
    subgraph "Context Map"
        OM["Order<br/>Management<br/>(Upstream)"]
        PM["Payments<br/>(Downstream)"]
        FM["Fulfillment<br/>(Downstream)"]
        NM["Notifications<br/>(Downstream)"]
        AN["Analytics<br/>(Downstream)"]
    end
    
    OM -->|"Customer-Supplier"| PM
    OM -->|"Customer-Supplier"| FM
    PM -->|"Published Language<br/>(PaymentEvent.avro)"| AN
    FM -->|"Published Language<br/>(ShipmentEvent.avro)"| AN
    OM -->|"Conformist"| NM
    
    style OM fill:#FF6B35,color:#fff
    style PM fill:#4ECDC4,color:#fff
    style FM fill:#45B7D1,color:#fff
    style AN fill:#96CEB4,color:#fff
```

### Context Map Relationship Patterns

| Pattern | Description | When To Use |
|---|---|---|
| **Shared Kernel** | Two BCs share a small model (e.g., `Money` value object). Both must agree on changes | When two BCs are tightly coupled and owned by the same team |
| **Customer-Supplier** | Upstream BC serves downstream BC. Downstream can request changes, upstream prioritizes | When one team produces data another team consumes |
| **Conformist** | Downstream BC accepts upstream's model as-is, zero translation | When you have no leverage over the upstream team |
| **Anti-Corruption Layer** | Downstream BC translates upstream's model into its own language | When upstream model is messy, legacy, or from a 3rd party |
| **Open Host Service** | Upstream exposes a clean, versioned API/event schema for any consumer | When multiple downstream BCs consume from the same upstream |
| **Published Language** | A shared, versioned schema (Avro, Protobuf) used for inter-BC events | Kafka topic schemas between BCs |

## Sequence Diagram — Cross-BC Order Flow

```mermaid
sequenceDiagram
    actor Customer
    participant OM as Order Management BC
    participant PM as Payments BC
    participant FM as Fulfillment BC
    participant K as Kafka
    participant DW as Data Warehouse
    
    Customer->>OM: Place Order
    OM->>OM: Validate order, reserve inventory
    OM->>K: Publish OrderPlaced event
    
    K->>PM: Consume OrderPlaced
    PM->>PM: Charge payment via Stripe
    alt Payment Success
        PM->>K: Publish PaymentCaptured event
        K->>FM: Consume PaymentCaptured
        FM->>FM: Create shipment
        FM->>K: Publish ShipmentCreated event
    else Payment Failed
        PM->>K: Publish PaymentFailed event
        K->>OM: Consume PaymentFailed
        OM->>OM: Cancel order, release inventory
    end
    
    K->>DW: CDC captures all events
    DW->>DW: Build conformed dim_order across BCs
```

## State Machine — Order Entity Across Bounded Contexts

```mermaid
stateDiagram-v2
    [*] --> CartActive: Customer adds item
    
    state "Order Management BC" as OM {
        CartActive --> CheckoutStarted: Begin checkout
        CheckoutStarted --> OrderPlaced: Submit order
        OrderPlaced --> OrderCancelled: Payment fails 3x
    }
    
    state "Payments BC" as PM {
        OrderPlaced --> PaymentPending: Charge initiated
        PaymentPending --> PaymentCaptured: Charge success
        PaymentPending --> PaymentFailed: Charge declined
        PaymentFailed --> PaymentPending: Retry
    }
    
    state "Fulfillment BC" as FM {
        PaymentCaptured --> ShipmentCreated: Create shipment
        ShipmentCreated --> Dispatched: Ship out
        Dispatched --> Delivered: Confirmation
    }
    
    OrderCancelled --> [*]
    Delivered --> [*]
```

**Key insight**: Notice how `Order` transitions through **three different BCs** during its lifecycle. Each BC only knows its own states. The `Order Management BC` does not know about `Dispatched` — that state only exists in the `Fulfillment BC`. This is why a single `order_status` column in a monolithic table always becomes a mess.

## ER Diagram — Schema Per Bounded Context

```mermaid
erDiagram
    ORDER_MANAGEMENT_BC {
        bigint order_id PK
        bigint customer_id FK
        varchar order_status
        decimal total_amount
        timestamp created_at
    }
    
    PAYMENTS_BC {
        bigint payment_id PK
        bigint order_id FK
        varchar payment_status
        decimal amount
        varchar provider
        timestamp processed_at
    }
    
    FULFILLMENT_BC {
        bigint shipment_id PK
        bigint order_id FK
        varchar tracking_number
        varchar carrier
        varchar shipment_status
        timestamp shipped_at
        timestamp delivered_at
    }
    
    DW_CONFORMED_DIM_ORDER {
        bigint order_sk PK
        bigint order_id
        varchar order_status
        varchar payment_status
        varchar shipment_status
        decimal amount
        timestamp order_date
        boolean is_current
    }
    
    ORDER_MANAGEMENT_BC ||--o{ PAYMENTS_BC : "order_id"
    ORDER_MANAGEMENT_BC ||--o{ FULFILLMENT_BC : "order_id"
    ORDER_MANAGEMENT_BC }|--|| DW_CONFORMED_DIM_ORDER : "bridges via CDC"
    PAYMENTS_BC }|--|| DW_CONFORMED_DIM_ORDER : "bridges via CDC"
    FULFILLMENT_BC }|--|| DW_CONFORMED_DIM_ORDER : "bridges via CDC"
```

**Critical pattern**: Each BC has its own `order_id` column, but they are **not foreign keys to each other**. They are independent. The Data Warehouse is the only place where all three are joined together via a **conformed dimension** (`dim_order`).

## Table Structures

```sql
-- ============================================================
-- ORDER MANAGEMENT BOUNDED CONTEXT — owns order lifecycle
-- ============================================================
CREATE TABLE order_mgmt.orders (
    order_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id     BIGINT        NOT NULL,
    order_status    VARCHAR(30)   NOT NULL DEFAULT 'PENDING',
    total_amount    DECIMAL(12,2) NOT NULL,
    currency        CHAR(3)       DEFAULT 'USD',
    created_at      TIMESTAMPTZ   DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   DEFAULT NOW(),
    
    CONSTRAINT chk_order_status CHECK (order_status IN 
        ('PENDING', 'CONFIRMED', 'CANCELLED'))
);

-- ============================================================
-- PAYMENTS BOUNDED CONTEXT — owns payment lifecycle
-- ============================================================
CREATE TABLE payments.payments (
    payment_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id        BIGINT        NOT NULL,  -- NOT a FK to order_mgmt.orders!
    payment_status  VARCHAR(30)   NOT NULL DEFAULT 'INITIATED',
    amount          DECIMAL(12,2) NOT NULL,
    provider        VARCHAR(30)   NOT NULL DEFAULT 'STRIPE',
    stripe_charge_id VARCHAR(100),
    processed_at    TIMESTAMPTZ,
    
    CONSTRAINT chk_payment_status CHECK (payment_status IN 
        ('INITIATED', 'CAPTURED', 'FAILED', 'REFUNDED'))
);

-- ============================================================
-- DATA WAREHOUSE — Conformed dimension bridging all BCs
-- ============================================================
CREATE TABLE analytics.dim_order (
    order_sk         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    
    -- Natural key
    order_id         BIGINT NOT NULL,
    
    -- From Order Management BC
    order_status     VARCHAR(30),
    total_amount     DECIMAL(12,2),
    
    -- From Payments BC
    payment_status   VARCHAR(30),
    payment_provider VARCHAR(30),
    
    -- From Fulfillment BC
    shipment_status  VARCHAR(30),
    tracking_number  VARCHAR(100),
    
    -- SCD Type 2
    effective_from   TIMESTAMPTZ NOT NULL,
    effective_to     TIMESTAMPTZ DEFAULT '9999-12-31',
    is_current       BOOLEAN DEFAULT TRUE
);
```

## Data Flow Diagram

```mermaid
flowchart LR
    subgraph "Source Systems (per BC)"
        S1["Order DB"]
        S2["Payment DB"]
        S3["Fulfillment DB"]
    end
    
    subgraph "Change Data Capture"
        D1["Debezium<br/>Connector"]
    end
    
    subgraph "Event Bus"
        K1["order-mgmt.orders"]
        K2["payments.payments"]
        K3["fulfillment.shipments"]
    end
    
    subgraph "Transformation"
        F["Flink / Spark<br/>Join + Conform"]
    end
    
    subgraph "Consumption"
        DW["dim_order<br/>(Conformed)"]
        DS["Dashboard"]
    end
    
    S1 --> D1 --> K1 --> F
    S2 --> D1 --> K2 --> F
    S3 --> D1 --> K3 --> F
    F --> DW --> DS
```
