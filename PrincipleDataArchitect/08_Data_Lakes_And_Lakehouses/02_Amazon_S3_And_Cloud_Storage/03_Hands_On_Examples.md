# Amazon S3 & Cloud Storage — Hands-On Examples

The primary method for interacting with S3 programmatically involves the AWS CLI or an SDK (like Python's `boto3`). 

---

## Scenario 1: Interacting with S3 Files

Because S3 uses a flat namespace rather than a directory tree, "folders" are just visual illusions created by the `/` character in object keys.

### Execution

```bash
# Upload a local file to S3
$ aws s3 cp ./monthly_report.pdf s3://financial-corp-bucket/2023/reports/monthly_report.pdf
upload: ./monthly_report.pdf to s3://financial-corp-bucket/2023/reports/monthly_report.pdf

# List the "directory" contents
# Notice it behaves like a normal filesystem listing
$ aws s3 ls s3://financial-corp-bucket/2023/reports/
2023-11-01 10:00:00    1048576 monthly_report.pdf

# The immense power of S3 Sync
# This command recursively compares your local directory to the S3 bucket.
# It mathematically hashes every file, and ONLY uploads files that have changed or are new,
# making it incredibly efficient for continuous backups.
$ aws s3 sync /local/data/warehouse/ s3://financial-corp-bucket/data-lake/
```

---

## Scenario 2: Generating Presigned URLs

A massive architectural challenge involves allowing users to download private files (like a purchased ebook) without routing massive network traffic through your application servers.

**The Fix:** The backend application cryptographically signs a temporary S3 URL. The user's browser uses this URL to download the file *directly* from AWS, totally bypassing your application servers. 

### Execution (Python / Boto3)

```python
import boto3

s3_client = boto3.client('s3')

# Generate a secure, temporary URL that expires in precisely 3600 seconds (1 hour).
# The user doesn't need AWS credentials; the URL itself serves as the cryptographic token.
presigned_url = s3_client.generate_presigned_url(
    'get_object',
    Params={
        'Bucket': 'premium-ebooks-b2c',
        'Key': 'architecture_guide_2023.pdf'
    },
    ExpiresIn=3600
)

print(presigned_url)
# Output: https://premium-ebooks-b2c.s3.amazonaws.com/architecture_guide_2023.pdf?AWSAccessKeyId=AKIA...&Expires=...&Signature=...

# Your application returns this URL to the user's browser.
# The browser issues an HTTP GET directly to AWS.
```

---

## Scenario 3: Multipart Uploads (For Massive Files)

When an application attempts to upload a 50 GB database dump to S3 using a single HTTP `PUT` request, it is virtually guaranteed to fail midway due to TCP packet loss or network hiccups, requiring the application to start the 50 GB upload entirely from scratch.

### The Solution
AWS handles this using **Multipart Uploads**. 
1. The client breaks the 50 GB file into 10,000 independent 5 MB chunks.
2. The client uploads these chunks to S3 in parallel across multiple threads.
3. If Chunk #452 fails due to a network blip, the client *only* retries Chunk #452.
4. Once all 10,000 chunks reach AWS, the client sends a `CompleteMultipartUpload` API call. S3 stitches the file together internally and presents it as a single contiguous object.

### Execution

```bash
# Fortunately, the high-level AWS CLI handles this massive complexity automatically.
# Any file over a certain threshold triggers the multipart protocol gracefully in the background.

$ aws s3 cp ./massive_postgres_dump.sql.gz s3://db-backups-bucket/
Completed 100.5 GiB / 500.0 GiB (100.0 MiB/s) ... 
```

---

## Scenario 4: Querying Data in Place (S3 Select)

Instead of downloading a massive CSV to parse it with `grep`, you can push the SQL logic directly down to the S3 hardware.

### Execution (Python / Boto3)

```python
import boto3

s3 = boto3.client('s3')

# We have a 10GB CSV of all global flights, but we only want delays over 120 minutes originating in JFK.
response = s3.select_object_content(
    Bucket='global-flight-data',
    Key='2023_all_flights.csv',
    ExpressionType='SQL',
    Expression="SELECT s.FlightNum, s.Delay FROM s3object s WHERE s.Origin = 'JFK' AND cast(s.Delay as int) > 120",
    InputSerialization={'CSV': {'FileHeaderInfo': 'USE'}},
    OutputSerialization={'CSV': {}}
)

for event in response['Payload']:
    if 'Records' in event:
        print(event['Records']['Payload'].decode('utf-8'))
```
