# Interview Angle: Spatial Databases

## How This Appears

In senior and principal-level system design interviews, spatial intelligence primarily appears in mapping, delivery, and ride-hailing prompts:
1.  "Design Uber / Lyft / Grab."
2.  "Design DoorDash / UberEats."
3.  "Design a Yelp / Foursquare proximity search ('Places near me')."

While Junior candidates will naively suggest scanning a SQL table, Principal candidates must articulate Spatial Indexing, Grid Systems, and partitioning strategies.

## Sample Questions & Answer Frameworks

### Q1: "How would you design a system to find the 5 nearest drivers to a rider immediately?"

*   **Weak Answer:** "I will store drivers in MySQL with Lat and Lon columns. I will query the database `WHERE distance(driver, rider) < 5` and `ORDER BY distance LIMIT 5`." (Fails instantly: Full table scan computing Haversine formulas on active rows).
*   **Good Answer:** "I will use PostGIS with a GiST index. I'll utilize the index-assisted nearest neighbor operator `<->` to rapidly traverse the R-Tree down to the 5 closest drivers without scanning the table."
*   **Principal Answer:** "For a global scale like Uber, an R-Tree updating constantly under heavy write loads (drivers moving every 4 seconds) creates massive index locking contention. Instead, I would use a Discrete Global Grid System like Uber H3. I'll translate driver coordinates into H3 Hex IDs (Resolution 9). I'll partition a NoSQL database (like Cassandra or Redis) using this Hex ID. When a rider requests a car, I calculate their Hex ID, instantly query that exact Redis partition, and if no drivers are there, I expand outward to the 6 mathematically perfect neighboring hexagons using simple bitwise math."
*   **What They're Testing:** Understanding the scalability limits of localized R-Trees vs global discrete grid systems (Geohash/H3/S2) under massive concurrent read/write loads.

### Q2: "What is a Geohash, and what is its primary weakness?"

*   **Weak Answer:** "It's a way to turn a location into a simple string to save space."
*   **Strong Answer:** "Geohash interleaves the bits of Latitude and Longitude into a single base32 string, mapping 2D space onto a 1D Z-order curve. It's incredibly powerful because proximity queries become simple `LIKE 'prefix%'` string matching. However, its major weakness is edge effects at the boundaries of the grid. Two locations could be a millimeter apart physically, but if they straddle the boundary of two massive parent Geohash squares, their Geohash strings will share absolutely no prefix prefix similarity. Additionally, because the grid relies on longitude, the physical area of a Geohash box warps heavily depending on its distance from the equator."
*   **What They're Testing:** Understanding space-filling curves and the "Boundary Problem" of hierarchical grids.

### Q3: "Explain the two steps of a Spatial Join in a database like PostGIS."

*   **Strong Answer:** "Because polygon math is heavily CPU bound, spatial DBs employ a Two-Phase approach. First is the Filter Phase: the database uses the GiST (R-Tree) index to compare the Minimum Bounding Rectangles (MBRs) of the shapes. This is an extremely fast index traversal that returns candidates, but introduces false positives. Second is the Refine Phase: the database pulls the exact geometry of the surviving candidates and executes precise algebraic intersection math (e.g., using the GEOS library) to drop the false positives and return the mathematically true intersection."
*   **What They're Testing:** Proving you know how a complex query planner actually approaches heavy computational tasks (Bounding Box pruning).

## Whiteboard Exercise

**The O2O (Online-To-Offline) Proximity Architecture**

Draw how to decouple rapidly changing live locations (drivers) from static complex geometries (restaurants/zones).

```mermaid
graph TD
    App(Rider / User App) --> API[Matchmaking API]
    
    subgraph "The Fast Path (Live Actors)"
        API --> H3Lib[Calculate H3 Hexagon for User]
        H3Lib --> Redis[(Redis: Driver Locations <br/> Key: H3_Hex_ID <br/> Value: Set of Driver IDs)]
    end
    
    subgraph "The Slow Path (Static Analysis)"
        BI(Data Scientists) --> CloudDWH[(Cloud WH: SnowFlake)]
        CloudDWH --> GEOP[GeoParquet Tables <br/> Trips, Zones]
        Note over CloudDWH: Massively Parallel <br> Spatial Joins
    end
    
    API -. async telemetry .-> Kafka[Kafka]
    Kafka --> CloudDWH
    
    style Redis fill:#ffcccb,stroke:#a00,stroke-width:2px
    style CloudDWH fill:#90EE90,stroke:#090,stroke-width:2px
```
*Narrative to practice:* "We split the architecture. Transient, highly-volatile spatial tracking (drivers moving) relies exclusively on fast discrete grid key-value resolution (Redis + H3). We completely avoid R-Trees here. Deep analytical spatial workloads (e.g., how many rides started in the 'Downtown Polygon' last month) are batched to a columnar cloud warehouse using distributed bounding-box pruning algorithms over GeoParquet."
