# 🧠 Mind Map – Spatial Databases
---
## How to Use This Mind Map
- **For Development**: Refer to the Anti-Patterns checklist before coding a spatial JOIN to ensure you are utilizing the R-Tree effectively (avoiding `ST_Distance`).
- **For Architecture**: Choose between Relational Spatial (PostGIS - best for complex intersecting polygons) vs. Discrete Grids (H3/Geohash - best for high-throughput live tracking).
- **For Interviews**: Leverage the vocabulary of the "Two-Phase" spatial query and "MBR Bounding Boxes" when asked to design O2O maps.

---
## 🗺️ Core Fundamentals
### Geometric Forms
- **Vector**: Points, Lines, Polygons. (e.g., User Location, Road Network, City Boundary).
- **Raster**: Pixel grids holding localized data. (e.g., Elevation mapping, Satellite Imagery).
### Plane Constraints
- **Geometry**: Operates on a flat Cartesian plane. Mathematically simple, but stretches massively closer to the poles.
- **Geography**: Computes over the curvature of the Earth. Required for accurate cross-continent distance calculations (Meters instead of meaningless flat Degrees).
- **SRID (Spatial Reference ID)**: EPSG:4326 (WGS 84 GPS standard). Mixing SRIDs across data sources results in disastrous implicit data corruption.

---
## 🗺️ Indexing Strategies & Engine Internals
### The R-Tree (GiST)
- Organizes data into overlapping Minimum Bounding Rectangles (MBRs).
- Optimized for containment, intersection, and bounding box searches.
- Highly locked on insertion/update. Unsuitable for millions of moving drivers.
### The Two-Phase Query
- **1. Filter Phase**: Instant traversal of the R-Tree index evaluating MBR overlap (Fast, False Positives).
- **2. Refine Phase**: Fetching exact vertices from disk to execute exhaustive Point-in-Polygon mathematical algorithms (CPU Heavy, True validation).
### Discrete Global Grids (DGG)
- **Geohash**: Encodes 2D to 1D via recursive squares. Suffers from unequal neighbor distances and massive distortion at the poles.
- **Uber H3**: Encodes to 1D via 16-resolution Hexagons. Superior because the center of the hexagon to all 6 identical neighbors is perfectly equidistant.

---
## 🗺️ Execution & Optimization 
### Proximity / KNN
- **Avoid**: Sorting on `ST_Distance()`. Forces a sequential table scan of Haversine calculations.
- **Embrace**: Index-assisted distance traversing like PostGIS `<->` operator in `ORDER BY` clauses to cleanly cap execution at `LIMIT K`.
### Scale & Storage
- Cloud Native Geospatial flips the ecosystem.
- Massive scale spatial joins now bypass standard databases, relying on querying **GeoParquet** files via analytic MPP engines (Snowflake/BigQuery).

---
## 🗺️ Pitfalls & Traps (Anti-Patterns)
### P01: The Invalid Geometry Crush
- **The Issue**: "Bowtie" polygons or unclosed line-strings break ETL topology libraries.
- **The Fix**: Strict `CHECK(ST_IsValid(geom))` constraints and pipeline sanitization using `ST_MakeValid()`.
### P02: The B-Tree Fallacy
- **The Issue**: Indexing a spatial column as a normal index. B-Trees cannot index multiple overlapping nested boundaries.
- **The Fix**: Enforce GiST (Generalized Search Trees) for spatial implementations.
### P03: Boundary Edge Effects & MAUP
- **The Issue**: Analytics warping wildly based on how arbitrary state or neighborhood lines are drawn.
- **The Fix**: Enforce strict mapping across uniform global grids to achieve statistically neutral results.

---
## 🗺️ Common Interview System Designs
### 01: The Ride-Hailing App (Uber/Lyft)
- **Challenge**: Scale real-time proximity matchmaking.
- **Pattern**: Move away from R-Tree lookups. Rely tightly on App-side H3 calculations sending purely integers to Redis/Cassandra partitions for blistering fast matchmaking.
### 02: O2O Delivery (DoorDash)
- **Challenge**: Routing limits driving bounds (e.g., bounded by a river).
- **Pattern**: Quick bounding box prune via Spatial DB (`ST_DWithin`), matched linearly against actual Road Routing Graph computations (Isochrones).

---
## 🗺️ Assessment & Reflection
- "Am I computing `ST_Distance` inside a `WHERE` clause instead of `ST_DWithin`, causing an invisible Cartesian full table scan?"
- "Do my batch analytic queries fail suddenly due to a `TopologyException` from unsanitized third-party polygon data?"
- "Is my architecture attempting to manage 10 million constantly shifting driver locations inside a Postgres GiST index rather than using a Discrete Global Grid?"
