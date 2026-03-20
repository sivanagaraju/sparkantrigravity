# 🧠 Mind Map – Hadoop & HDFS

---

## How to Use This Mind Map
- **For Revision**: Grasping the physical layout of NameNodes vs DataNodes, and the 128MB Block/3x Replication math.
- **For Application**: Understanding why you must aggregate tiny JSON files into massive Parquet chunks before touching HDFS.
- **For Interviews**: Explaining the shift from "Coupled Storage/Compute" (Hadoop) to "Decoupled Storage/Compute" (S3/Snowflake), and the genesis of Data Locality.

---

## 🗺️ Theory & Concepts

### The Paradigm Shift: Data Locality
- **Old World (SANs):** "Moving Data to Compute." Pull 100TB over the network into the shiny, expensive CPU. Network I/O crashes.
- **Hadoop World (HDFS):** "Moving Compute to Data." Push a 50KB Java program to the 100 cheap servers holding the 100TB of data locally. Process using PCI-Express bus speeds, bypassing the network. 

### The Master/Worker Architecture
- **NameNode (The Brain):** Stores no actual data. Keeps a massive dictionary in its RAM tracking exactly which file maps to which blocks, and which DataNodes currently hold those blocks.
- **DataNodes (The Muscle):** Dumb commodity servers packed with hard drives. They physically store the block byte strings and send "Heartbeats" to the NameNode every 3 seconds confirming they are alive.

### Data Geometry
- **Block Size (128 MB):** Files are shattered into massive pieces. Minimizes spinning disk head "seek time" physically on the platter.
- **Replication (3x):** Because hardware breaks, every block is physically copied to 3 independent servers. If a Heartbeat goes quiet, the NameNode detects 2x replication and commands the forging of a 3rd copy immediately.

---

## 🗺️ Execution Layers

### Layer 1: HDFS
- Strictly the physical storage file system mimicking a massive Unix drive (`hdfs dfs -ls /`).

### Layer 2: YARN (Yet Another Resource Negotiator)
- The cluster "Operating System" or Resource Manager.
- Applications ask YARN: *"I need 50 containers with 2GB RAM."* YARN allocates the CPU/RAM boundaries logically across the physical servers.

### Layer 3: MapReduce / Hive / Spark
- The actual analytical frameworks executing inside the YARN containers directly against the HDFS blocks. MapReduce uses disk for intermediate steps (slow). Spark keeps intermediate steps in RAM (fast).

---

## 🗺️ Mistakes & Anti-Patterns

### M01: The "Small Files" Crisis
- **Root Cause:** Streaming millions of 1KB text files directly into HDFS.
- **Diagnostic:** NameNode RAM violently exhausts (150 bytes metadata per file). The entire PB-scale cluster permanently halts over 5GB of active data.
- **Correction:** Buffer and aggregate files into 128MB minimum chunks via Kafka/Flume before writing to the Data Lake.

### M02: Coupled Hardware Traps
- **Root Cause:** Needing to store cheap, massive Video surveillance archives.
- **Diagnostic:** The company spends $10M buying 200 physical Hadoop Pizza Boxes to get the requisite hard disk limits, wasting the hundreds of expensive Intel CPUs packaged with them.
- **Correction:** The architectural catalyst for moving to S3 (Pure Storage) uncoupled from Compute.

---

## 🗺️ Interview Angle

### Q: Why did the map-reduce shuffle phase cause such massive slow downs?
- Assertive Answer: "Because MapReduce was hyper-paranoid about failure. After the Map phase finished sorting local chunks, it strictly wrote all intermediate data physically to the spinning hard drive. The Shuffle phase then ripped that data off the drive and jammed it through the network switch. The combination of Physical Disk I/O plus Network I/O made it notoriously slow, which is specifically what Spark fixed by retaining intermediate DAG steps completely in RAM."

### Q: Why is HDFS strictly Write-Once, Read-Many (WORM)?
- Assertive Answer: "Because a distributed 128MB block architecture physically cannot support mid-file random mutation. If you edited byte 4,000 to be longer, Hadoop would have to forcefully rewrite the entire 128MB block and re-broadcast it linearly over the network to 3 separate replica nodes. True database updates require a NoSQL index layer like HBase acting as a buffer on top."

---

## 🗺️ Assessment & Reflection
- What is the difference between a NameNode failure (SPOF) and a DataNode failure?
- Explain exactly why 5 PB of logical application data consumes 15 PB of physical hard drives in an on-premise HDFS cluster.
- Why does Hive exist if MapReduce can process everything natively?
