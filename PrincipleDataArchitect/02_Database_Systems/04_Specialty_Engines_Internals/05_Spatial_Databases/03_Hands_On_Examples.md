# Hands-On Examples: Spatial Databases (PostGIS)

The following examples utilize **PostgreSQL + PostGIS**, the industry standard for relational spatial workloads.

## 1. Setup & Geometry Creation

First, enable the spatial extension and create a table recognizing SRID 4326 (standard GPS coordinates).

```sql
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create a table for delivery zones
CREATE TABLE delivery_zones (
    id SERIAL PRIMARY KEY,
    zone_name VARCHAR(100),
    geom GEOMETRY(Polygon, 4326)
);

-- Note the GiST index. Crucial for the "Filter Phase" of spatial joins.
CREATE INDEX idx_delivery_zones_geom ON delivery_zones USING GIST (geom);

-- Insert a polygon (WKT - Well Known Text format)
INSERT INTO delivery_zones (zone_name, geom)
VALUES (
    'Downtown Core',
    ST_GeomFromText('POLYGON((-122.42 37.78, -122.40 37.78, -122.40 37.77, -122.42 37.77, -122.42 37.78))', 4326)
);
```

## 2. The Spatial Join (Point in Polygon)

A standard JOIN uses a foreign key. A **Spatial Join** executes a topological function (e.g., `ST_Contains`) on the `ON` clause. 

```sql
-- Assume we have an 'orders' table with a GEOMETRY(Point) column
SELECT 
    d.zone_name, 
    COUNT(o.id) as total_orders
FROM 
    delivery_zones d
JOIN 
    orders o 
ON 
    ST_Contains(d.geom, o.location) 
GROUP BY 
    d.zone_name;
```

*Under the hood:* The planner uses the `idx_delivery_zones_geom` GiST index to quickly eliminate orders completely outside the bounding boxes of the delivery zones, then performs point-in-polygon math only on the intersecting subsets.

## 3. High-Performance Nearest Neighbor (KNN)

Using the `<->` index-assisted distance operator.

```sql
-- Let's find the 5 closest drivers to a customer requesting a ride.
-- Customer is at longitude -122.41, latitude 37.77
SELECT 
    driver_id, 
    location
FROM 
    active_drivers
ORDER BY 
    location <-> ST_SetSRID(ST_MakePoint(-122.41, 37.77), 4326)
LIMIT 5;
```
*Why this is expert-level:* The `<->` operator computes distance between *bounding boxes* in the index. When used with an `ORDER BY` and `LIMIT`, it traverses the GiST tree downwards towards the target, stopping exactly after 5 elements. It prevents scanning the entire driver table. 

## 4. Distance Queries: Geography vs. Geometry

When computing distance across the Earth, calculating raw degrees is mathematically useless in flat geometry since longitude lines converge at the poles. You must cast to `Geography` to utilize the spherical distance calculation (meters).

```sql
-- BAD (Geometry calculation): Will return a meaningless value in degrees
SELECT ST_Distance(
    ST_SetSRID(ST_MakePoint(-122.41, 37.77), 4326),
    ST_SetSRID(ST_MakePoint(-118.24, 34.05), 4326)
);

-- GOOD (Geography calculation): Will strictly return meters measuring along the Earth's curve
SELECT ST_Distance(
    ST_SetSRID(ST_MakePoint(-122.41, 37.77), 4326)::geography,
    ST_SetSRID(ST_MakePoint(-118.24, 34.05), 4326)::geography
);
```
*Note:* The `ST_DWithin` function handles this perfectly and utilizes spatial indexes, making it superior to `<` thresholding on an `ST_Distance` call.

## 5. Integrating with H3 (Via extensions or application logic)

If utilizing the `h3-pg` extension, you can generate H3 indexes natively in Postgres.

```sql
-- Convert a point geometry to H3 resolution 9 (approx 100k sq meters)
SELECT h3_lat_lng_to_cell(ST_Point(-122.41, 37.77), 9);
-- Returns: '8928308280fffff'

-- Aggregate billions of events purely by standard group by (Incredibly fast)
SELECT 
    h3_lat_lng_to_cell(location, 9) as hex_id, 
    COUNT(*) as heat_density
FROM 
    pickup_events 
GROUP BY 
    1;
```
Using H3 effectively transforms a complex Spatial intersection problem into a localized hash aggregation problem (handled blisteringly fast by columnar/analytical engines).
