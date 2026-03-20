# Amazon S3 & Cloud Storage — How It Works

## 1. Buckets, Keys, and Objects

S3 operates entirely on three fundamental primitives:

1.  **Buckets:** The top-level logical container for your data (e.g., `company-production-data`). Bucket names must be globally unique across all of AWS because they form the base of the public HTTP URL routing layer.
2.  **Objects:** The actual combination of your File Data (the bytes) and Metadata (e.g., Content-Type, custom tags). Objects can range from 0 bytes up to roughly 5 Terabytes.
3.  **Keys:** The unique string identifier for the object inside the bucket (e.g., `logs/app1/2023/10/01/error.log`).

When you query an Object, you are essentially querying a massive distributed NoSQL Key-Value database where the Key is the URI and the Value is the File Data.

---

## 2. Strong Read-After-Write Consistency

Historically (prior to December 2020), S3 was an "Eventually Consistent" system. If you uploaded a file, and immediately ran a `LIST` command, the file might not appear for a few seconds. If you overwrote an existing file and instantly downloaded it, you might get the old version.
This made running complex Data Lakes (like Apache Hadoop directly on S3) terrifying, as MapReduce jobs would occasionally fail because they couldn't find files that were just written by a previous step.

**Modern Architecture:**
S3 engineering achieved a monumental feat in 2020: **Strong Read-After-Write Consistency** without sacrificing performance.
- When an application executes an HTTP `PUT` to create `data.csv`, S3 physically writes the payload to multiple independent storage devices across a minimum of 3 Availability Zones.
- S3 does not return a `200 OK` until the write is safely committed to the necessary quorum of hard drives.
- The immediate very next `GET` or `LIST` command is mathematically guaranteed to retrieve the newest data.

---

## 3. S3 Physical Durability — "11 Nines"

Amazon offers a durability guarantee of **99.999999999%**. 
If you store 10,000,000 files in S3, you can statistically expect to lose a single file every 10,000 years.

### How is this physically achieved?
Unlike traditional RAID arrays that mirror 2 or 3 hard drives, S3 utilizes **Erasure Coding**. 
1. When you upload a 10MB PDF, S3 mathematically shreds the file into, for example, 12 data fragments.
2. It then calculates an additional 4 mathematical "parity" fragments using Reed-Solomon equations.
3. S3 physically distributes these 16 fragments across dozens of servers located in 3 completely independent physical datacenters (Availability Zones) separated by miles.
4. If a meteor strikes an entire datacenter (wiping out 5 fragments), S3's math can perfectly reconstruct the original 10MB PDF using any 11 surviving fragments from the remaining datacenters.

---

## 4. Intelligent Storage Tiers

Because data gets "cold" over time (nobody usually queries 5-year-old application logs), keeping it on fast NVMe storage is financially wasteful. S3 introduced lifecycle storage tiers to mechanically move data between physical hardware grades.

1.  **S3 Standard:** Fast, immediate retrieval. High storage cost, zero retrieval cost. Used for active website assets or daily ETL processing.
2.  **S3 Standard-IA (Infrequent Access):** Same speed as standard. Half the storage cost, but you are billed a fee *every time you read the data*. Used for monthly reporting backups.
3.  **S3 Glacier Deep Archive:** Pennies per terabyte. The data is physically moved to robotic tape drives. It takes 12-48 hours to execute a `GET` request because a literal robot arm has to locate the magnetic tape in an Amazon warehouse, load it, and spin it up. Used exclusively for extreme long-term legal compliance archiving.

---

## 5. Amazon S3 Select (Push-Down Queries)

Typically, to filter a 5GB CSV file stored in S3, your application has to download the entire 5GB over the network into RAM, parse it, and find the 10 rows it wants. This is an immense waste of network bandwidth and CPU.

**S3 Select** pushes the compute *down* into the storage layer. 
You can send a specific SQL query directly into the S3 API:
`SELECT * FROM s3object s WHERE s.status_code = '500'`

S3 physically executes the parsing using internal AWS compute instances directly next to the storage drives, and returns *only* the resulting 1 MB of text over the network to the client. This mimics the Data Locality concept of Hadoop, but orchestrated via cloud API.
