import os

base_path = r"c:\Users\sivan\Learning\Code\sparkantrigravity\PrincipleDataArchitect"

# ============================================================
# ALL GAPS FROM THE GAP ANALYSIS — CRITICAL + MODERATE + NICE-TO-HAVE
# ============================================================

gaps = {
    # ── 01_Data_Modeling: Missing L2s ──
    "01_Data_Modeling": {
        "07_Normalization_Theory": [
            "01_1NF_Through_3NF",
            "02_BCNF_And_4NF",
            "03_5NF_And_6NF",
            "04_Denormalization_Trade_Offs"
        ],
        "08_Physical_Data_Modeling": [
            "01_Tablespace_Layout",
            "02_Storage_Parameters",
            "03_Physical_vs_Logical_Separation"
        ],
        "09_Schema_Design_Patterns": [
            "01_Anchor_Modeling",
            "02_Wide_Table_vs_Normalized",
            "03_EAV_Pattern_And_Alternatives"
        ],
        "10_Data_Modeling_For_Analytics": [
            "01_Star_Schema_Fundamentals",
            "02_Snowflake_Schema",
            "03_Galaxy_Schema"
        ],
        # Missing L3s in existing L2s
        "04_Temporal_and_Bitemporal_Modeling": [
            "03_Snapshot_Fact_Tables"
        ],
        "02_Dimensional_Modeling_Advanced": [
            "04_Conformed_Dimensions",
            "05_Aggregate_Tables"
        ],
    },

    # ── 02_Database_Systems: Missing L2s ──
    "02_Database_Systems": {
        "06_RDBMS_Deep_Internals": [
            "01_PostgreSQL_Internals",
            "02_MySQL_InnoDB",
            "03_Oracle_Architecture",
            "04_SQL_Server_Internals"
        ],
        "07_In_Memory_Databases": [
            "01_Redis_Data_Structures",
            "02_Memcached",
            "03_SAP_HANA",
            "04_Redis_Cluster_And_Sentinel"
        ],
        "08_Graph_Databases": [
            "01_Neo4j_Internals",
            "02_Amazon_Neptune",
            "03_TigerGraph",
            "04_Query_Languages_Cypher_Gremlin"
        ],
        # Missing L3s in existing L2s
        "04_Specialty_Engines_Internals": [
            "04_Graph_Databases_Overview",
            "05_Spatial_Databases"
        ],
        "05_Database_Reliability_Engineering": [
            "04_Backup_Recovery_Strategies",
            "05_Upgrades_And_Migrations"
        ],
    },

    # ── 03_Data_Warehousing: Missing L2s ──
    "03_Data_Warehousing": {
        "05_Workload_Management_Concurrency": [
            "01_Resource_Groups_Queues",
            "02_Snowflake_Warehouse_Sizing",
            "03_Redshift_WLM",
            "04_BigQuery_Slot_Management"
        ],
        "06_Data_Mart_Design": [
            "01_Dependent_vs_Independent",
            "02_Aggregation_Strategies",
            "03_Mart_Refresh_Patterns"
        ],
    },

    # ── 04_Data_Lake_Lakehouse: Missing L2s ──
    "04_Data_Lake_Lakehouse": {
        "06_Medallion_Architecture_Deep_Dive": [
            "01_Bronze_Layer_Patterns",
            "02_Silver_Layer_Transformations",
            "03_Gold_Layer_Business_Views",
            "04_Cross_Layer_Lineage"
        ],
        "07_Lake_Governance": [
            "01_Lake_Formation_Policies",
            "02_Unity_Catalog_For_Lakes",
            "03_Tag_Based_Access_Control"
        ],
    },

    # ── 05_Batch_Data_Pipelines: Missing L3 ──
    "05_Batch_Data_Pipelines": {
        "02_Orchestration_Deep_Dive": [
            "05_Mage_And_Legacy_Orchestrators"
        ],
    },

    # ── 06_Streaming_And_RealTime: Missing L2s ──
    "06_Streaming_And_RealTime": {
        "06_Real_Time_OLAP_Engines": [
            "01_Apache_Druid",
            "02_Apache_Pinot",
            "03_ClickHouse",
            "04_StarRocks",
            "05_Materialized_Views_Streaming"
        ],
        "07_Message_Queue_Alternatives": [
            "01_Apache_Pulsar",
            "02_RabbitMQ",
            "03_AWS_SQS_SNS",
            "04_Azure_Event_Hubs",
            "05_NATS_And_Redis_Streams"
        ],
        # Missing L3 in existing L2
        "02_Stream_Processing_Engines": [
            "04_Apache_Beam_Unified"
        ],
    },

    # ── 08_Cloud_Data_Platforms: Missing L2s + L3s ──
    "08_Cloud_Data_Platforms": {
        "06_Snowflake_Platform_Deep_Dive": [
            "01_Snowpipe_And_Streams",
            "02_Tasks_And_Scheduling",
            "03_Snowpark",
            "04_Data_Sharing_And_Marketplace"
        ],
        "07_Cloud_Networking_For_Data": [
            "01_VPC_Peering",
            "02_PrivateLink",
            "03_VPN_And_Direct_Connect",
            "04_Cross_Region_Replication"
        ],
        # Missing L3s in existing L2s
        "01_AWS_Data_Stack": [
            "05_Redshift_Serverless",
            "06_EMR_And_EMR_Serverless"
        ],
        "03_GCP_Data_Stack": [
            "04_Cloud_Composer_Airflow",
            "05_Looker_And_BI"
        ],
    },

    # ── 09_Data_Governance_Metadata: Missing L3 ──
    "09_Data_Governance_Metadata": {
        "02_Data_Catalog_And_Discovery": [
            "04_Business_Glossary"
        ],
    },

    # ── 10_Data_Quality_Observability: Missing L3 ──
    "10_Data_Quality_Observability": {
        "02_Data_Quality_Tools_Deep_Dive": [
            "05_Data_Profiling_Tools"
        ],
    },

    # ── 11_Master_Data_Management: Missing L2 ──
    "11_Master_Data_Management": {
        "05_Reference_Data_Management": [
            "01_Code_Tables_Lookups",
            "02_Country_Currency_Standards",
            "03_Versioning_Reference_Data"
        ],
    },

    # ── 12_Data_Security_Privacy: Missing L3 ──
    "12_Data_Security_Privacy": {
        "03_Access_Control_Models": [
            "05_Service_Accounts_Machine_Identity"
        ],
    },

    # ── 13_Architecture_Patterns: Missing L3s ──
    "13_Architecture_Patterns": {
        "06_Reference_Architectures": [
            "05_Microsoft",
            "06_Google"
        ],
        "07_Migration_Transformation_Stories": [
            "01_Warehouse_To_Lakehouse",
            "02_Monolith_To_Mesh",
            "03_On_Prem_To_Cloud"
        ],
    },

    # ── 14_Data_Architecture_For_AI: Missing L2s ──
    "14_Data_Architecture_For_AI": {
        "06_ML_Pipeline_Orchestration": [
            "01_Kubeflow_Pipelines",
            "02_MLflow",
            "03_SageMaker_Pipelines",
            "04_Vertex_AI_Pipelines"
        ],
        "07_Training_Data_Management": [
            "01_Data_Versioning_DVC_LakeFS",
            "02_Labeling_Pipelines",
            "03_Dataset_Registries"
        ],
        "08_Model_Serving_Data_Flow": [
            "01_Batch_vs_Real_Time_Inference",
            "02_AB_Model_Routing",
            "03_Shadow_Mode_Deployment"
        ],
        # Missing L3s in existing L2
        "02_RAG_Pipelines": [
            "04_Reranking_Strategies",
            "05_Evaluation_Metrics_RAG"
        ],
    },

    # ── 15_Data_FinOps: Missing L3 ──
    "15_Data_FinOps_And_Cost_Management": {
        "01_Cloud_Cost_Economics": [
            "04_Reserved_Capacity_Contracts"
        ],
    },

    # ── 16_SQL: Missing L3s ──
    "16_SQL_And_Query_Optimization": {
        "01_Advanced_Analytical_Functions": [
            "05_Pivot_Unpivot",
            "06_Grouping_Sets_Rollup_Cube"
        ],
    },

    # ── 17_DataOps: Missing L2s + L3 ──
    "17_DataOps_IaC_Programming": {
        "06_Containerization_For_Data": [
            "01_Docker_For_Data_Pipelines",
            "02_Kubernetes_For_Spark",
            "03_K8s_For_Airflow_Flink",
            "04_Helm_Charts_For_Data"
        ],
        "07_Monitoring_And_Alerting": [
            "01_Prometheus_Grafana",
            "02_CloudWatch_Datadog",
            "03_Pipeline_Health_Dashboards",
            "04_On_Call_For_Data_Engineers"
        ],
        "08_Open_Source_Ecosystem_Map": [
            "01_Apache_Foundation_Projects",
            "02_Linux_Foundation_Data",
            "03_Evaluating_OSS_Maturity"
        ],
        # Missing L3 in existing L2
        "02_PySpark_Mastery": [
            "05_Broadcast_Variables_Accumulators"
        ],
    },

    # ── 18_System_Design: Missing L2s + L3s ──
    "18_System_Design_Distributed": {
        "07_CAP_PACELC_Deep_Dive": [
            "01_CAP_With_Real_Examples",
            "02_PACELC_Decision_Framework",
            "03_Consistency_Models_Spectrum"
        ],
        "08_Capacity_Planning": [
            "01_Storage_Growth_Estimation",
            "02_Compute_Sizing",
            "03_Network_Bandwidth_Planning"
        ],
        "09_Disaster_Recovery_Business_Continuity": [
            "01_RPO_And_RTO",
            "02_Failover_Strategies",
            "03_Backup_Architectures",
            "04_Chaos_Engineering_For_Data"
        ],
        # Missing L3s in existing L2
        "01_Physics_Of_Distributed_Systems": [
            "04_Consistent_Hashing",
            "05_Bloom_Filters",
            "06_Merkle_Trees"
        ],
    },

    # ── 19_Performance: Missing L3 ──
    "19_Performance_Scalability": {
        "02_Partitioning_Sharding": [
            "04_Partition_Pruning_Predicate_Pushdown"
        ],
    },

    # ── 20_Leadership: Missing L3 ──
    "20_Leadership_Communication": {
        "02_Stakeholder_Management": [
            "04_Cross_Functional_Partnerships"
        ],
    },

    # ── 21_Use_Cases: Missing L3 ──
    "21_Real_World_Use_Cases": {
        "03_Financial_Services_Data_Platform": [
            "04_Anti_Money_Laundering"
        ],
    },

    # ── 22_Interview: Missing L3s ──
    "22_Interview_Preparation": {
        "03_Technical_Deep_Dive_Questions": [
            "05_SQL_Live_Coding",
            "06_Architecture_Whiteboard"
        ],
    },
}

# ============================================================
# Execute: Create all missing folders + placeholder markdown
# ============================================================

count_l2_new = 0
count_l3_new = 0

print("Adding all gap analysis folders...")

for l1_folder, l2_dict in gaps.items():
    l1_path = os.path.join(base_path, l1_folder)

    for l2_folder, l3_list in l2_dict.items():
        l2_path = os.path.join(l1_path, l2_folder)
        if not os.path.exists(l2_path):
            count_l2_new += 1

        for l3_folder in l3_list:
            count_l3_new += 1
            dir_path = os.path.join(l2_path, l3_folder)
            os.makedirs(dir_path, exist_ok=True)

            md_file_path = os.path.join(dir_path, f"{l3_folder}_Content.md")
            if not os.path.exists(md_file_path):
                with open(md_file_path, "w", encoding="utf-8") as f:
                    friendly_name = l3_folder.replace('_', ' ')
                    f.write(f"# {friendly_name}\n\n*Content to be developed at FAANG Principal-level depth.*\n")

print(f"Done! Added {count_l2_new} NEW Level 2 folders, {count_l3_new} NEW Level 3 concept folders.")

# ============================================================
# Final Stats: Count everything
# ============================================================

total_l1 = 0
total_l2 = 0
total_l3 = 0

for l1 in sorted(os.listdir(base_path)):
    l1_full = os.path.join(base_path, l1)
    if not os.path.isdir(l1_full) or l1.startswith('.'):
        continue
    total_l1 += 1
    for l2 in sorted(os.listdir(l1_full)):
        l2_full = os.path.join(l1_full, l2)
        if not os.path.isdir(l2_full):
            continue
        total_l2 += 1
        for l3 in sorted(os.listdir(l2_full)):
            l3_full = os.path.join(l2_full, l3)
            if os.path.isdir(l3_full):
                total_l3 += 1

print(f"\n=== FINAL TOTALS ===")
print(f"Level 1 Domains:    {total_l1}")
print(f"Level 2 Subtopics:  {total_l2}")
print(f"Level 3 Concepts:   {total_l3}")
print(f"Total Folders:      {total_l1 + total_l2 + total_l3}")
