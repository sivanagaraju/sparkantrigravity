import os

base_path = r"c:\Users\sivan\Learning\Code\sparkantrigravity\PrincipleDataArchitect"

structure = {
    "00_Role_Definition": {
        "01_Career_Ladder_And_Scope": ["01_Level_Differences", "02_Principal_Archetypes", "03_Impact_Metrics"],
        "02_Influence_Without_Authority": ["01_Stakeholder_Alignment", "02_Architecture_Review_Board", "03_Writing_Memos"],
        "03_Strategic_Decision_Making": ["01_Build_vs_Buy", "02_Managing_Technical_Debt", "03_Vendor_Lock_in"],
        "04_Navigating_Organizational_Politics": ["01_Conways_Law", "02_High_Visibility_Failures", "03_Mentorship_Scale"]
    },
    "01_Data_Modeling": {
        "01_Logical_Domain_Modeling": ["01_Event_Storming", "02_Bounded_Contexts", "03_Polymorphism_Trap"],
        "02_Dimensional_Modeling_Advanced": ["01_Degenerate_Outrigger", "02_SCD_Extreme_Cases", "03_Factless_Fact_Tables"],
        "03_Data_Vault_2_0_Architecture": ["01_Philosophy_Use_Cases", "02_Hubs_Links_Satellites", "03_Hash_Keys_vs_Natural"],
        "04_Temporal_and_Bitemporal_Modeling": ["01_Valid_vs_Transaction_Time", "02_As_Of_Queries"],
        "05_Graph_Data_Modeling": ["01_Property_Graphs", "02_Fraud_Detection_Schemas", "03_Super_Nodes"],
        "06_NoSQL_and_Document_Modeling": ["01_Query_Driven_Modeling", "02_Embedding_vs_Referencing", "03_Schema_Evolution"]
    },
    "02_Database_Systems": {
        "01_Storage_Engines_and_Disk_Layout": ["01_B_Trees_vs_LSM_Trees", "02_Page_Architecture", "03_Compaction_Strategies"],
        "02_Transactions_and_Consistency": ["01_MVCC_Internals", "02_Isolation_Levels", "03_Distributed_Consensus"],
        "03_NewSQL_and_Distributed_RDBMS": ["01_Spanner_Cockroach_TiDB", "02_PACELC_Theorem", "03_Data_Distribution_Mechanics"],
        "04_Specialty_Engines_Internals": ["01_Time_Series_Databases", "02_Search_Engines", "03_Vector_Databases"],
        "05_Database_Reliability_Engineering": ["01_WAL_and_Durability", "02_Replication_Topologies", "03_Connection_Pooling"]
    },
    "03_Data_Warehousing": {
        "01_DW_Philosophy_And_Methodology": ["01_Inmon_vs_Kimball_vs_Vault", "02_Enterprise_Bus", "03_Semantic_Layer_Resurgence"],
        "02_MPP_Engine_Internals": ["01_Snowflake_Architecture", "02_Redshift_Architecture", "03_BigQuery_Architecture", "04_Synapse_Analytics"],
        "03_Advanced_SCD_Implementation": ["01_Types_0_1_2_3", "02_Types_4_6", "03_Type_7_Dual_Keys"],
        "04_Modern_DW_Patterns": ["01_Activity_Schema", "02_One_Big_Table_OBT", "03_Zero_Copy_Cloning", "04_Time_Travel"]
    },
    "04_Data_Lake_Lakehouse": {
        "01_Data_Lake_Foundations": ["01_Zone_Architecture", "02_File_Format_Selection", "03_Partitioning_Strategy", "04_Small_Files_Problem"],
        "02_Delta_Lake_Deep_Dive": ["01_Transaction_Log", "02_Z_Ordering_Liquid_Clustering", "03_Change_Data_Feed", "04_Deletion_Vectors"],
        "03_Apache_Iceberg_Deep_Dive": ["01_Metadata_Layer_Architecture", "02_Hidden_Partitioning", "03_Schema_Evolution", "04_Catalog_Integration"],
        "04_Apache_Hudi_Deep_Dive": ["01_CoW_vs_MoR", "02_Timeline_Architecture", "03_Compaction_Strategies"],
        "05_Table_Format_Head_To_Head": ["01_Decision_Matrix", "02_UniForm_XTable", "03_Vendor_Lock_in_Analysis"]
    },
    "05_Batch_Data_Pipelines": {
        "01_ETL_vs_ELT_Decision_Framework": ["01_When_ETL_Wins", "02_When_ELT_Wins", "03_Hidden_Cost_of_ELT"],
        "02_Orchestration_Deep_Dive": ["01_Airflow_Internals", "02_Dagster_vs_Prefect", "03_DAG_Anti_Patterns", "04_Idempotency_By_Design"],
        "03_dbt_Transformation_Mastery": ["01_Incremental_Models", "02_Snapshots_SCD2", "03_Ref_Graph_Execution", "04_Testing_Philosophy"],
        "04_Pipeline_Reliability_Engineering": ["01_Backfill_Strategies", "02_Dead_Letter_Queues", "03_Pipeline_SLAs_Alerting", "04_Cost_Estimation"]
    },
    "06_Streaming_And_RealTime": {
        "01_Apache_Kafka_Internals": ["01_Partition_Mechanics", "02_Consumer_Group_Rebalancing", "03_Exactly_Once_Semantics", "04_KRaft_Mode", "05_Schema_Registry_Compatibility"],
        "02_Stream_Processing_Engines": ["01_Apache_Flink_Deep_Dive", "02_Spark_Structured_Streaming", "03_Kafka_Streams"],
        "03_Event_Driven_Architecture_Patterns": ["01_Event_Sourcing", "02_CQRS", "03_Outbox_Pattern", "04_Saga_Pattern"],
        "04_CDC_Change_Data_Capture": ["01_Log_Based_Debezium", "02_Query_Based", "03_Ordering_and_Deduplication"],
        "05_Windowing_and_Late_Data": ["01_Window_Types", "02_Watermarks_Allowed_Lateness", "03_Side_Outputs"]
    },
    "07_Data_Integration_And_APIs": {
        "01_Integration_Patterns": ["01_Point_to_Point", "02_Hub_and_Spoke", "03_Publish_Subscribe", "04_API_Led_Connectivity"],
        "02_Data_Virtualization": ["01_Query_Federation", "02_When_Virtualization_Wins", "03_When_Virtualization_Fails"],
        "03_Schema_Management_And_Evolution": ["01_Schema_Registry", "02_Schema_Evolution_Rules", "03_Data_Contracts"],
        "04_API_Design_For_Data_Products": ["01_REST_GraphQL_gRPC", "02_Pagination_Patterns", "03_Rate_Limiting"]
    },
    "08_Cloud_Data_Platforms": {
        "01_AWS_Data_Stack": ["01_S3_Storage_Classes", "02_Glue_Catalog_ETL", "03_Athena_Lake_Formation", "04_Kinesis"],
        "02_Azure_Data_Stack": ["01_ADLS_Gen2", "02_Synapse_Analytics", "03_Purview", "04_Databricks_On_Azure"],
        "03_GCP_Data_Stack": ["01_BigQuery_Internals", "02_Dataflow", "03_PubSub_vs_Kafka"],
        "04_Databricks_Unified_Platform": ["01_Unity_Catalog", "02_Delta_Live_Tables", "03_Photon_Engine", "04_SQL_Warehouses"],
        "05_Multi_Cloud_Strategy": ["01_Data_Gravity", "02_Abstraction_Layers", "03_Best_Of_Breed"]
    },
    "09_Data_Governance_Metadata": {
        "01_Governance_Frameworks": ["01_DAMA_DMBOK", "02_DCAM", "03_Stewardship_Models"],
        "02_Data_Catalog_And_Discovery": ["01_Modern_Catalogs", "02_Active_Metadata", "03_Search_UX"],
        "03_Data_Lineage": ["01_Column_Level_Lineage", "02_OpenLineage_Standard", "03_Impact_Analysis"],
        "04_Data_Mesh_Architecture": ["01_Domain_Ownership", "02_Data_As_Product", "03_Self_Serve_Platform", "04_Federated_Governance"],
        "05_Data_Contracts": ["01_Specification", "02_Contract_Testing_CI_CD", "03_Organizational_Challenge"]
    },
    "10_Data_Quality_Observability": {
        "01_Quality_Dimensions_And_Metrics": ["01_The_6_Pillars", "02_DQ_Scorecards", "03_Cost_Of_Bad_Data"],
        "02_Data_Quality_Tools_Deep_Dive": ["01_Great_Expectations", "02_Soda_Core", "03_dbt_Tests", "04_ML_Anomaly_Detection"],
        "03_Data_Observability": ["01_The_5_Pillars", "02_Building_vs_Buying", "03_Alert_Fatigue"],
        "04_Quality_Gates_Medallion": ["01_Bronze_Gate", "02_Silver_Gate", "03_Gold_Gate", "04_Circuit_Breakers"],
        "05_Data_Reconciliation": ["01_Source_To_Target", "02_Cross_System", "03_Drift_Detection"]
    },
    "11_Master_Data_Management": {
        "01_MDM_Architecture_Styles": ["01_Registry_Style", "02_Consolidation_Style", "03_Coexistence_Style", "04_Centralized_Style"],
        "02_Entity_Resolution_Algorithms": ["01_Deterministic_Matching", "02_Probabilistic_Matching", "03_ML_Matching", "04_Graph_Based_Resolution"],
        "03_The_Golden_Record": ["01_Survivorship_Rules", "02_Trust_Scores", "03_Hierarchy_Management"],
        "04_Customer_360_Architecture": ["01_Building_Unified_View", "02_Identity_Resolution_At_Scale", "03_Real_Time_vs_Batch"]
    },
    "12_Data_Security_Privacy": {
        "01_Defense_In_Depth_Architecture": ["01_Zero_Trust", "02_Security_Layers", "03_Blast_Radius"],
        "02_Encryption_Deep_Dive": ["01_At_Rest", "02_In_Transit", "03_In_Use", "04_Key_Management"],
        "03_Access_Control_Models": ["01_RBAC", "02_ABAC", "03_Row_Column_Security", "04_Dynamic_Masking"],
        "04_PII_Handling_Framework": ["01_Classification", "02_Tokenization_Pseudonymization", "03_Right_To_Erasure"],
        "05_Compliance_Frameworks": ["01_GDPR", "02_CCPA", "03_HIPAA", "04_SOX"]
    },
    "13_Architecture_Patterns": {
        "01_Lambda_Architecture": ["01_The_Three_Layers", "02_Operational_Pain", "03_When_Lambda_Wins"],
        "02_Kappa_Architecture": ["01_Streaming_Source_Of_Truth", "02_The_Replay_Problem", "03_When_Kappa_Breaks"],
        "03_Data_Mesh_Architecture": ["01_The_Four_Principles", "02_Organizational_Prerequisites", "03_Central_Platform_Role"],
        "04_Data_Fabric_Architecture": ["01_Metadata_Driven_Integration", "02_Fabric_vs_Mesh", "03_Vendor_Landscape"],
        "05_Event_Driven_Microservices": ["01_Database_Per_Service", "02_API_Composition", "03_Choreography_vs_Orchestration", "04_Strangler_Fig"],
        "06_Reference_Architectures": ["01_Netflix", "02_LinkedIn", "03_Uber", "04_Airbnb"]
    },
    "14_Data_Architecture_For_AI": {
        "01_Feature_Stores_and_Serving": ["01_Online_vs_Offline", "02_Point_In_Time_Correctness", "03_Feature_Registries"],
        "02_RAG_Pipelines": ["01_Vector_Embedding_Pipelines", "02_Chunking_Strategies", "03_Hybrid_Search"],
        "03_LLMOps_and_Evaluation": ["01_Prompt_Logging", "02_Golden_Datasets"],
        "04_Data_Moats": ["01_Architecting_The_Flywheel", "02_Synthetic_Data_Generation"],
        "05_AI_Data_Governance": ["01_Copyright_PII_Scrubbing", "02_Access_Control_For_Embeddings"]
    },
    "15_Data_FinOps_And_Cost_Management": {
        "01_Cloud_Cost_Economics": ["01_Compute_Storage_Separation", "02_Spot_Preemptible_Instances", "03_Egress_Cost_Landmines"],
        "02_Query_Cost_Optimization": ["01_Snowflake_Credits", "02_BigQuery_Bytes_Scanned", "03_Redshift_Cost_Patterns", "04_Query_Cost_Governance"],
        "03_Storage_Optimization": ["01_Storage_Tiering_Lifecycles", "02_Compression_ROI", "03_Small_File_Consolidation"],
        "04_Chargeback_And_Showback_Models": ["01_Chargeback_vs_Showback", "02_Tagging_Strategy", "03_Unit_Economics"]
    },
    "16_SQL_And_Query_Optimization": {
        "01_Advanced_Analytical_Functions": ["01_Window_Functions", "02_Running_Totals", "03_Percentiles_Cont_Disc", "04_QUALIFY_Clause"],
        "02_Recursive_CTEs_And_Hierarchies": ["01_Bill_Of_Materials", "02_Organizational_Chart", "03_Graph_Traversal"],
        "03_EXPLAIN_Plans_Optimizer": ["01_Reading_EXPLAIN_ANALYZE", "02_Join_Algorithms", "03_Statistics_Histograms", "04_Index_Advisor"],
        "04_SQL_Anti_Patterns": ["01_Implicit_Type_Conversions", "02_Correlated_Subqueries", "03_SELECT_Star", "04_OR_Conditions"],
        "05_SQL_Dialect_Differences": ["01_PG_vs_Snowflake_vs_BQ_vs_Spark", "02_Writing_Portable_SQL"]
    },
    "17_DataOps_IaC_Programming": {
        "01_Python_For_Data_Engineering": ["01_Beyond_Pandas", "02_Type_Hints", "03_Testing_Pytest", "04_Packaging"],
        "02_PySpark_Mastery": ["01_Catalyst_Optimizer", "02_AQE", "03_Memory_Management", "04_UDF_Performance"],
        "03_Infrastructure_As_Code": ["01_Terraform_For_Data", "02_State_Management", "03_Modular_IaC"],
        "04_CI_CD_For_Data": ["01_dbt_CI", "02_Spark_Job_Deployment", "03_Data_Pipeline_Testing", "04_GitOps"],
        "05_Scala_When_And_Why": ["01_Scala_vs_Python", "02_Case_Classes", "03_When_Python_Wins"]
    },
    "18_System_Design_Distributed": {
        "01_Physics_Of_Distributed_Systems": ["01_Latency_Numbers", "02_Idempotency", "03_Backpressure"],
        "02_Netflix_Scale": ["01_Viewing_History", "02_AB_Testing"],
        "03_Amazon_Scale": ["01_Saga_Pattern", "02_Multi_Region_Active_Active"],
        "04_LinkedIn_Scale": ["01_Activity_Feed", "02_Secondary_Indexing"],
        "05_Uber_Scale": ["01_Geohashing_S2_Cells", "02_Lambda_Architecture_SLA"],
        "06_Architecture_Decision_Records_ADR": ["01_Documenting_The_Why", "02_Living_With_Tech_Debt"]
    },
    "19_Performance_Scalability": {
        "01_Advanced_Indexing": ["01_B_Tree_Depth", "02_Covering_Indexes", "03_Partial_Indexes", "04_GiST_GIN_BRIN"],
        "02_Partitioning_Sharding": ["01_Range_Hash_List", "02_Horizontal_Sharding", "03_The_Resharding_Tax"],
        "03_Caching_Layers_Invalidation": ["01_Cache_Patterns", "02_Cache_Invalidation", "03_Thundering_Herd", "04_Materialized_Views"],
        "04_Data_Compression_Encoding": ["01_Columnar_vs_Row", "02_RLE_vs_Dictionary", "03_Zstd_vs_Snappy"],
        "05_Query_Execution_Plans": ["01_Nested_Loop_Hash_Merge", "02_Cardinality_Failures", "03_Data_Skew_Straggler"]
    },
    "20_Leadership_Communication": {
        "01_Writing_Technical_Vision": ["01_1_3_5_Year_Roadmap", "02_Amazon_6_Pager", "03_RFC_Process", "04_ADRs"],
        "02_Stakeholder_Management": ["01_Speaking_To_C_Suite", "02_The_Art_Of_No", "03_Managing_Tech_Debt"],
        "03_Building_Architecture_Reviews": ["01_The_ARB", "02_Lightweight_Flow", "03_Running_Effective_Reviews"],
        "04_Mentoring_Growing_Engineers": ["01_The_Multiplier_Effect", "02_Architecture_Office_Hours", "03_Giving_Hard_Feedback"],
        "05_Vendor_Technology_Evaluation": ["01_The_POC_Framework", "02_Build_vs_Buy", "03_Navigating_Sales_Cycles"]
    },
    "21_Real_World_Use_Cases": {
        "01_E_Commerce_Data_Platform": ["01_Product_Catalog", "02_Order_Pipeline", "03_Real_Time_Pricing", "04_Recommendation_Data"],
        "02_Media_Streaming_Data_Platform": ["01_Content_Ingestion", "02_Viewing_History", "03_AB_Testing", "04_Personalization_Flow"],
        "03_Financial_Services_Data_Platform": ["01_Transaction_Processing", "02_Fraud_Detection", "03_Regulatory_Reporting"],
        "04_Healthcare_Data_Platform": ["01_HIPAA_Data_Lake", "02_Clinical_Trial_Integration", "03_Real_Time_Patient_Monitoring"],
        "05_IoT_And_Manufacturing": ["01_Time_Series_At_Scale", "02_Predictive_Maintenance", "03_Digital_Twin"],
        "06_Cross_Domain_Migration_Scenarios": ["01_On_Prem_To_Lakehouse", "02_Monolith_To_Data_Mesh", "03_Cost_Optimization_Exercise"]
    },
    "22_Interview_Preparation": {
        "01_Behavioral_Deep_Dives": ["01_STAR_Method_L7", "02_Leadership_Scenarios", "03_Influence_Stories", "04_Failure_Stories"],
        "02_System_Design_Questions": ["01_25_Data_Architecture_Prompts", "02_The_45_Minute_Framework", "03_Handling_What_About"],
        "03_Technical_Deep_Dive_Questions": ["01_Database_Internals", "02_Distributed_Systems", "03_Data_Modeling", "04_Performance"],
        "04_Case_Study_Exercises": ["01_Current_To_Target_State", "02_Cost_Optimization", "03_Organizational_Exercise"],
        "05_Compensation_And_Negotiation": ["01_FAANG_Bands", "02_Leveling_Negotiations", "03_Counter_Offer_Strategy"],
        "06_Resume_And_Portfolio": ["01_2_Page_Resume", "02_Architecture_Portfolio", "03_GitHub_Open_Source"]
    }
}

count_l2 = 0
count_l3 = 0

print("Generating 3-level directory structure...")

for l1_folder, l2_dict in structure.items():
    # Make sure we don't accidentally create an invalid path if l1 is missing
    l1_path = os.path.join(base_path, l1_folder)
    if not os.path.exists(l1_path):
        os.makedirs(l1_path)

    for l2_folder, l3_list in l2_dict.items():
        count_l2 += 1
        for l3_folder in l3_list:
            count_l3 += 1
            # Build the path
            dir_path = os.path.join(l1_path, l2_folder, l3_folder)
            
            # Create the directories
            os.makedirs(dir_path, exist_ok=True)
            
            # Create a placeholder markdown file in the Level 3 folder
            md_file_path = os.path.join(dir_path, f"{l3_folder}_Content.md")
            if not os.path.exists(md_file_path):
                with open(md_file_path, "w", encoding="utf-8") as f:
                    friendly_name = l3_folder.replace('_', ' ')
                    f.write(f"# {friendly_name}\n\n*Content to be developed at FAANG Principal-level depth.*\n")

print(f"Success! Created {count_l2} Level 2 constraint folders, and {count_l3} Level 3 concept folders w/ markdown files.")
