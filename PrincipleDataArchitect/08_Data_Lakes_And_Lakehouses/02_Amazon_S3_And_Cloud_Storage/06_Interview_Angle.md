# Amazon S3 & Cloud Storage — Interview Angle

## How This Appears

S3 is the cornerstone of modern Cloud Architecture. Interviewers use it as a pivot point to determine if you actually understand Decoupled Architectures versus on-premise monoliths.

Almost every "Design Netflix" or "Design a Global Photo Sharing App" interview natively requires you to invoke S3 (or an equivalent Object Store) to handle the massive blob storage scale.

---

## Sample Questions

### Q1: "Explain the fundamental difference between Block Storage, File Storage, and Object Storage. When would you use each?"

**Weak answer (Mid-Level):** "Block storage is for hard drives. File storage is for networks. Object storage is S3, which is for big files."

**Strong answer (Principal):** 
1.  **Block Storage (EBS/SAN):** Data is written in fixed-size bare-metal sectors directly to a disk. It offers single-digit millisecond latency and supports aggressive random-access R/W. *Use Case:* Attaching to an EC2 instance to run the raw engine of a PostgreSQL database. It exists on one machine and cannot scale horizontally.
2.  **File Storage (EFS/NFS):** Data is organized into a hierarchical, standard POSIX tree structure (Files, Folders, Inodes) accessible by multiple servers simultaneously over a network. *Use Case:* A shared drive where 50 web servers need concurrent read-access to a massive active WordPress `wp-content` media directory where directory locking is required.
3.  **Object Storage (S3):** Data and Metadata are bundled into an immutable 'Object', placed onto a flat namespace across distributed hardware worldwide, accessible via HTTP APIs. It trades nanosecond latency for theoretically infinite horizontal distribution. *Use Case:* Creating the "Data Lake" gravity well for a multi-petabyte analytics platform or hosting static globally distributed web assets.

---

### Q2: "Our web application allows users to upload massive 5GB videos. If we route these uploads through our primary Node.js Web API servers to save them locally, the servers crash under the memory load. How do we fix this?"

**Strong answer (Principal):**
"We must completely bypass the Node.js tier for the heavy payload transfer.
We will refactor the frontend to use **S3 Presigned URLs**. 
1. The frontend asks the isolated Node.js backend for an upload token. 
2. The Node.js server authenticates the user, securely signs a temporary 15-minute S3 upload URL, and returns it.
3. The frontend executes a multi-part HTTP `PUT` directly to Amazon S3 using the URL. 
4. The 5GB of network transit entirely bypasses our infrastructure, leveraging AWS's infinite bandwidth. 
5. Finally, we configure S3 to trigger an AWS Lambda function upon a successful `ObjectCreated` event, which securely updates our primary PostgreSQL database marking the video as successfully ingested."

---

### Q3: "Before 2020, running heavy Spark workloads against S3 was extremely dangerous. Why, and how did AWS fix it?"

**Strong answer (Principal):**
"Historically, S3 utilized an **Eventual Consistency** model. When a Spark job overwrote a massive Parquet file, S3 initially updated it in one datacenter, but it might take two seconds to replicate that new version to all storage nodes globally. 
If Step 2 of the Spark pipeline immediately executed a `LIST` or `GET` command, it occasionally hit an older, un-updated replica node. The pipeline processed the old data, permanently corrupting the analytical output silently.
AWS resolved this in December 2020 by rolling out **Strong Read-After-Write Consistency**. Now, `PUT` requests physically block and do not return a success signal until a vast majority quorum of hardware is successfully updated, guaranteeing the next immediate `GET` retrieves the flawless latest state, bringing S3 parity with traditional HDFS guarantees."

---

## What They're Really Testing

1. **Trade-offs:** Can you distinguish between when a query requires a standard RDBMS vs a decoupled Cloud Data Warehouse querying S3?
2. **Architecture:** Do you realize S3 is an HTTP API, not a mounted `C:\` drive?
3. **Operations:** Do you understand the billing logic of scanning unstructured files in the cloud (Athena partitions) and the dangers of public bucket policies?
