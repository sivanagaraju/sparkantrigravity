# 17 — DataOps, Infrastructure as Code & Programming

> "A Principal Architect who can't write code is an ivory tower theorist. One who can't automate infrastructure is stuck in 2015."

DataOps is the application of DevOps principles to data engineering: version-controlled pipelines, automated testing, CI/CD for data, and infrastructure provisioned through code. Combined with programming fluency in Python, PySpark, and Scala, this is the execution muscle behind architectural vision.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Python_For_Data_Engineering/`

- **Beyond Pandas**: Polars (Rust-based, 10-100x faster than Pandas for large datasets), DuckDB (in-process analytical SQL), and PyArrow for zero-copy columnar data interchange.
- **Type Hints and Static Analysis**: Using `mypy`, `pydantic`, and `dataclasses` for self-documenting, testable data pipeline code. Why untyped Python pipelines become unmaintainable at scale.
- **Testing Data Pipelines**: `pytest` fixtures, parameterized tests, mocking external services (S3, APIs). Property-based testing with Hypothesis for edge case discovery.
- **Packaging and Distribution**: Building internal PyPI packages for shared utilities. `pyproject.toml`, `uv`, and reproducible environments.

### `02_PySpark_Mastery/`

- **Catalyst Optimizer**: How Spark's query optimizer transforms logical plans into physical plans. Understanding `explain(true)` output — parsed, analyzed, optimized, and physical plans.
- **Adaptive Query Execution (AQE)**: Runtime query re-optimization. Automatic coalescing of shuffle partitions, switching join strategies based on actual data sizes, and skew join optimization.
- **Memory Management**: Driver memory vs. executor memory. Off-heap vs. on-heap memory. Understanding OOM errors — when they're caused by data skew, when by UDF serialization, when by broadcast join size.
- **UDF Performance**: Why Python UDFs are 10-100x slower than native Spark functions (serialization overhead). Using Pandas UDFs (Arrow-optimized) and avoiding UDFs entirely by rewriting logic as DataFrame operations.

### `03_Infrastructure_As_Code/`

- **Terraform for Data Platforms**: Provisioning S3 buckets, Glue catalogs, Redshift clusters, Kafka topics, IAM roles, and VPC peering — all from version-controlled HCL files.
- **State Management**: Remote state in S3 + DynamoDB locking. State drift detection. The terror of `terraform destroy` on a production data lake.
- **Modular IaC**: Building reusable Terraform modules for data lake zones, warehouse configurations, and Kafka cluster templates so that provisioning a new environment takes minutes, not weeks.

### `04_CI_CD_For_Data/`

- **dbt CI**: Running `dbt build` on a PR branch against a temporary schema, validating model compilation, running tests, and tearing down the schema on merge.
- **Spark Job Deployment**: Blue-green deployments for Spark streaming jobs. Deploying new JAR/wheel files without losing in-flight events.
- **Data Pipeline Testing in CI**: Spinning up local containers (Postgres, Kafka, MinIO) via Docker Compose to run integration tests against realistic data before deploying to production.
- **GitOps for Data**: Treating the data catalog, access policies, and pipeline configurations as code. Pull requests for schema changes. Audit trail for every configuration modification.

### `05_Scala_When_And_Why/`

- **Scala vs. Python for Spark**: Scala compiles to JVM bytecode (native Spark execution, no serialization overhead). Python UDFs serialize data to Python and back. For latency-critical streaming jobs, Scala wins.
- **Case Classes for Type-Safe Data**: Defining Spark schemas as Scala case classes provides compile-time type checking that catches schema mismatches before runtime.
- **When Python Wins**: Faster development, larger talent pool, better data science ecosystem (scikit-learn, transformers). For 95% of batch ETL jobs, Python/PySpark is the pragmatic choice.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
