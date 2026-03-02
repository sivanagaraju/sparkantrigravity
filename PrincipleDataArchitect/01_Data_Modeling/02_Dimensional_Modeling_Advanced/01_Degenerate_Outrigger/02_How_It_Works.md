# Degenerate & Outrigger Dimensions — How It Works (Deep Internals)

> HLD, ER diagrams, DDL table structures, sequence diagrams, and data flow.

---

## High-Level Design — Star vs Snowflake with Outriggers

```mermaid
flowchart TB
    subgraph "Pure Star Schema (no outriggers)"
        FS["fact_sales"]
        DP1["dim_product<br/>(includes brand cols)"]
        DC1["dim_customer<br/>(includes geo cols)"]
        DD1["dim_date"]
        FS --> DP1
        FS --> DC1
        FS --> DD1
    end
    
    subgraph "With Outriggers (snowflaked)"
        FS2["fact_sales"]
        DP2["dim_product"]
        DB["dim_brand<br/>(OUTRIGGER)"]
        DC2["dim_customer"]
        DG["dim_geography<br/>(OUTRIGGER)"]
        DD2["dim_date"]
        FS2 --> DP2
        DP2 --> DB
        FS2 --> DC2
        DC2 --> DG
        FS2 --> DD2
    end
    
    style DB fill:#4ECDC4,color:#fff
    style DG fill:#4ECDC4,color:#fff
```

## ER Diagram — Degenerate Dimensions in a Transaction Fact

```mermaid
erDiagram
    FACT_SALES {
        bigint sale_sk PK
        bigint date_sk FK
        bigint product_sk FK
        bigint customer_sk FK
        bigint store_sk FK
        varchar order_number "DEGENERATE DIM"
        varchar invoice_number "DEGENERATE DIM"
        varchar receipt_id "DEGENERATE DIM"
        decimal quantity
        decimal unit_price
        decimal discount_amount
        decimal net_amount
    }
    
    DIM_PRODUCT {
        bigint product_sk PK
        varchar product_name
        varchar category
        bigint brand_sk FK "FK to outrigger"
        varchar size
        varchar color
    }
    
    DIM_BRAND {
        bigint brand_sk PK
        varchar brand_name
        varchar parent_company
        varchar brand_country
        date founded_year
    }
    
    DIM_CUSTOMER {
        bigint customer_sk PK
        varchar customer_name
        varchar email
        bigint geo_sk FK "FK to outrigger"
        varchar customer_tier
    }
    
    DIM_GEOGRAPHY {
        bigint geo_sk PK
        varchar city
        varchar state_province
        varchar country
        varchar postal_code
        varchar region
    }
    
    FACT_SALES ||--o{ DIM_PRODUCT : "product_sk"
    FACT_SALES ||--o{ DIM_CUSTOMER : "customer_sk"
    DIM_PRODUCT }o--|| DIM_BRAND : "brand_sk (outrigger)"
    DIM_CUSTOMER }o--|| DIM_GEOGRAPHY : "geo_sk (outrigger)"
```

## Table Structures

### Degenerate Dimensions in the Fact Table

```sql
-- ============================================================
-- Fact table with degenerate dimensions (order_number, invoice_number)
-- These are dimensional — you filter/group by them — but have no separate dim
-- ============================================================

CREATE TABLE fact_sales (
    sale_sk             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    
    -- Foreign keys to dimensions
    date_sk             INT           NOT NULL REFERENCES dim_date(date_sk),
    product_sk          BIGINT        NOT NULL REFERENCES dim_product(product_sk),
    customer_sk         BIGINT        NOT NULL REFERENCES dim_customer(customer_sk),
    store_sk            BIGINT        NOT NULL REFERENCES dim_store(store_sk),
    
    -- DEGENERATE DIMENSIONS: no separate dim table
    order_number        VARCHAR(30)   NOT NULL,   -- drill-back to source
    invoice_number      VARCHAR(30),              -- source system reference
    receipt_id          VARCHAR(50),              -- POS receipt identifier
    
    -- Measures
    quantity            INTEGER       NOT NULL,
    unit_price          DECIMAL(10,2) NOT NULL,
    discount_amount     DECIMAL(10,2) DEFAULT 0,
    net_amount          DECIMAL(12,2) NOT NULL,
    tax_amount          DECIMAL(10,2) DEFAULT 0,
    
    -- Partition key
    sale_date           DATE          NOT NULL
) PARTITION BY RANGE (sale_date);

-- Index on degenerate dims for drill-back queries
CREATE INDEX idx_fact_sales_order ON fact_sales(order_number);
CREATE INDEX idx_fact_sales_invoice ON fact_sales(invoice_number);
```

### Outrigger Dimension Tables

```sql
-- ============================================================
-- OUTRIGGER: dim_brand hangs off dim_product
-- ============================================================

CREATE TABLE dim_brand (
    brand_sk            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    brand_id            INT           NOT NULL,   -- natural key
    brand_name          VARCHAR(200)  NOT NULL,
    parent_company      VARCHAR(200),
    brand_country       VARCHAR(100),
    founded_year        INT,
    
    -- SCD Type 2
    effective_from      DATE          NOT NULL,
    effective_to        DATE          DEFAULT '9999-12-31',
    is_current          BOOLEAN       DEFAULT TRUE
);

CREATE TABLE dim_product (
    product_sk          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id          INT           NOT NULL,   -- natural key
    product_name        VARCHAR(500)  NOT NULL,
    category            VARCHAR(100),
    subcategory         VARCHAR(100),
    
    -- FK to outrigger
    brand_sk            BIGINT        REFERENCES dim_brand(brand_sk),
    
    size                VARCHAR(20),
    color               VARCHAR(50),
    weight_kg           DECIMAL(8,2),
    
    -- SCD Type 2
    effective_from      DATE          NOT NULL,
    effective_to        DATE          DEFAULT '9999-12-31',
    is_current          BOOLEAN       DEFAULT TRUE
);

-- ============================================================
-- OUTRIGGER: dim_geography hangs off dim_customer
-- ============================================================

CREATE TABLE dim_geography (
    geo_sk              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city                VARCHAR(200)  NOT NULL,
    state_province      VARCHAR(200),
    country             VARCHAR(100)  NOT NULL,
    postal_code         VARCHAR(20),
    region              VARCHAR(100),
    latitude            DECIMAL(9,6),
    longitude           DECIMAL(9,6)
);

CREATE TABLE dim_customer (
    customer_sk         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id         INT           NOT NULL,
    customer_name       VARCHAR(300),
    email               VARCHAR(255),
    
    -- FK to outrigger
    geo_sk              BIGINT        REFERENCES dim_geography(geo_sk),
    
    customer_tier       VARCHAR(20),
    registration_date   DATE,
    
    -- SCD Type 2
    effective_from      DATE          NOT NULL,
    effective_to        DATE          DEFAULT '9999-12-31',
    is_current          BOOLEAN       DEFAULT TRUE
);
```

## Sequence Diagram — Query Execution with Outrigger JOIN

```mermaid
sequenceDiagram
    participant User as BI Analyst
    participant Q as Query Engine
    participant FS as fact_sales
    participant DP as dim_product
    participant DB as dim_brand (outrigger)
    
    User->>Q: SELECT brand_name, SUM(net_amount)<br/>FROM fact_sales<br/>JOIN dim_product JOIN dim_brand<br/>WHERE brand_country = 'USA'
    Q->>FS: Scan fact_sales (partitioned)
    Q->>DP: Hash join on product_sk
    Q->>DB: Hash join on brand_sk
    Note over Q: 3-way JOIN instead of 2-way<br/>Extra JOIN cost: ~5-15% overhead
    Q->>User: Return aggregated results
```

## Data Flow Diagram — Degenerate Dim Lifecycle

```mermaid
flowchart LR
    subgraph "Source System"
        OT["orders table<br/>order_number is PK"]
    end
    
    subgraph "ETL/ELT"
        E["Extract order_number"]
        L["Load directly into fact<br/>(no dim lookup needed)"]
    end
    
    subgraph "Data Warehouse"
        FT["fact_sales<br/>order_number = degenerate dim"]
    end
    
    subgraph "Analytics"
        DR["Drill-back query:<br/>WHERE order_number = 'ORD-12345'"]
    end
    
    OT --> E --> L --> FT --> DR
```

## When Outriggers Cause Problems

The Kimball Group's official guidance: **use outriggers sparingly**. The extra JOIN has two costs:

1. **Query performance**: Each outrigger adds one more hash/merge join to every query touching that dimension path
2. **SCD complexity**: If `dim_brand` is SCD Type 2, the surrogate key in `dim_product.brand_sk` must be point-in-time correct — the ETL must look up the brand_sk that was current when the product record was created

**Kimball's preferred alternative**: Denormalize brand attributes directly into `dim_product`. Accept the data duplication. Star schemas prioritize query speed over storage efficiency.
