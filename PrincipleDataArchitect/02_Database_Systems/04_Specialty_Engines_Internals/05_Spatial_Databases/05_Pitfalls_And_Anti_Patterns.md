# Pitfalls & Anti-Patterns: Spatial Databases

## 1. The Missing Spatial Index (The Silent Killer)

In a relational database, forgetting an index on `user_id` results in a sequential scan. In a spatial database, forgetting an index on a polygon column during a spatial join operation (`ST_Intersects`) results in a **Cartesian Explosion**. 

*   **Symptom:** A query joining 10,000 points against 500 delivery zones runs for 45 minutes and takes down the production database cluster.
*   **The Trap (PostGIS Specific):** A standard B-Tree index on a GEOMETRY column is useless. You must explicitly request a GiST (Generalized Search Tree) or SP-GiST index:
    ```sql
    -- INCORRECT: Standard B-Tree
    CREATE INDEX idx_geom ON zones(geom); 
    
    -- CORRECT: Spatial R-Tree
    CREATE INDEX idx_geom_spatial ON zones USING GIST (geom);
    ```

## 2. Abusing ST_Distance vs. ST_DWithin

Developers frequently retrieve points within a radius using the `ST_Distance` function because it reads intuitively:
`WHERE ST_Distance(geomA, geomB) < 1000`

*   **The Trap:** `ST_Distance` is a mathematical function evaluated *after* rows are fetched. The database planner cannot use a spatial index to prune the tree for this operation. It forces a full table scan, calculating the exact distance between the target and every single row in the massive database.
*   **The Fix:** Always use `ST_DWithin`, which is heavily optimized to use the bounding-box index (the GiST R-Tree) in its filtering phase.
    `WHERE ST_DWithin(geomA, geomB, 1000)`

## 3. The SRID Mismatch Silent Failure

Spatial Reference Identifiers (SRIDs) dictate how the Earth's curve is modeled (e.g., standard Lat/Lon vs. Web Mercator).

*   **The Trap:** Querying an intersection between two geometries with different SRIDs (e.g., 4326 vs 3857) often does not throw a hard SQL error. It implicitly assumes they are on a massive, unitless Cartesian plane, yielding wildly incorrect results (e.g., placing coordinates meant for New York physically into the middle of the Atlantic Ocean).
*   **The Fix:** Always enforce SRID constraints on table creation (`GEOMETRY(Point, 4326)`) and cast dynamic inputs rigorously: `ST_SetSRID(ST_MakePoint(lon, lat), 4326)`. Check mismatches using `ST_SRID()`.

## 4. The Funky Data Problem (Invalid Geometries)

A polygon's line strings cannot cross themselves (a "bowtie" polygon), and a polygon must be "closed" (the final vertex must equal the first vertex).

*   **The Trap:** Inserting dirty data from external APIs or mapping tools. Later, running an `ST_Area` or `ST_Intersection` on that dirty row throws a fatal `TopologyException` during a massive batch analytical query, failing the entire ETL pipeline.
*   **The Fix:** Add check constraints to strictly block invalid geometries on writes.
    ```sql
    ALTER TABLE land_parcels ADD CONSTRAINT enforce_valid_geom CHECK (ST_IsValid(geom));
    ```
    If ingesting dirty data is unavoidable, run `ST_MakeValid(geom)` to force the database to mathematically resolve self-intersections during the insertion pipeline.

## 5. Ignoring Edge Effects and MAUP

The **Modifiable Areal Unit Problem (MAUP)** is a fundamental statistical flaw in spatial analytics.

*   **The Trap:** Aggregating population density or sales data by arbitrary geographic boundaries (like zip codes or voting districts). If you draw the lines slightly differently, the statistical distribution wildly changes, giving analysts conflicting "insights."
*   **The Fix:** For deep analytical machine learning workflows, do not aggregate by organic/administrative boundaries (e.g., "Neighborhood borders"). Aggregate using strict mathematically uniform discrete global grids (like **Uber H3** or **Geohash**). This ensures perfectly uniform binning regardless of arbitrary human boundary redrawing.

## Decision Matrix: Spatial DB vs Traditional Databases

| Workload | Recommended Technology | Why B-Trees/SQL Fail Here |
| :--- | :--- | :--- |
| **Nearest N Drivers (Ride-hail)** | H3 + Redis/Cassandra, PostGIS (`<->`) | Calculating Haversine limits scale. Need fixed proximity clustering (H3) or R-Tree limits. |
| **Point in Complex Polygon** | PostGIS, BigQuery Geography | Requires 2-Phase evaluating (MBR + CPU intensive GEOS math) which a B-Tree cannot do. |
| **Global Analytical Aggregation** | Snowflake / BigQuery with GeoParquet | Heavy MPP scale. Row-based PostGIS instances max out RAM on 1B+ rows during massive intersection analytics. |
| **Simple Lat/Lon Radius (Small scale)** | Standard Postgres / MySQL | If the dataset is just 10,000 stores, pulling them into application memory and filtering locally is fine. A specialized engine is overkill. |
