# Degenerate & Outrigger Dimensions — Further Reading

> Books, GitHub repos, blog posts, and cross-references.

---

## 📚 Books

| Book | Author | Section |
|---|---|---|
| *The Data Warehouse Toolkit* 3rd Ed. | Ralph Kimball & Margy Ross | Ch. 3: Retail Sales — degenerate dims explained |
| *Star Schema: The Complete Reference* | Christopher Adamson | Ch. 8: Outrigger dimensions and snowflaking |
| *Agile Data Warehouse Design* | Lawrence Corr | Ch. 5: Advanced dimension types |
| *Building a Scalable Data Warehouse with Data Vault 2.0* | Dan Linstedt | Comparison with Data Vault approach |

## 🔗 GitHub Repos

| Repo | Description |
|---|---|
| [DataEngineer-io/data-engineer-handbook](https://github.com/DataEngineer-io/data-engineer-handbook) | Comprehensive data engineering resources including modeling patterns |
| [kimball-group/design-tips](https://www.kimballgroup.com/category/design-tips/) | Kimball Group's official design tips archive (web) |
| [dbt-labs/jaffle-shop](https://github.com/dbt-labs/jaffle-shop) | Reference dbt project with dimensional modeling examples |
| [gnebbia/data-engineering-resources](https://github.com/gnebbia/data-engineering-resources) | Curated list including data warehouse modeling |

## 📝 Key Articles

| Article | Source |
|---|---|
| [Degenerate Dimensions](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/degenerate-dimension/) | Kimball Group — official definition |
| [Outrigger Dimensions](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/outrigger-dimension/) | Kimball Group — official definition with guidance |
| [Junk Dimensions](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/junk-dimension/) | Kimball Group — comparison with degenerate |

## 🔗 Cross-References

| Concept | Path | Connection |
|---|---|---|
| SCD Extreme Cases | [../02_SCD_Extreme_Cases](../02_SCD_Extreme_Cases/) | Outriggers interact with SCD — temporal alignment matters |
| Conformed Dimensions | [../04_Conformed_Dimensions](../04_Conformed_Dimensions/) | Outriggers like dim_geography can be conformed across fact tables |
| Star Schema Fundamentals | [../../10_Data_Modeling_For_Analytics/01_Star_Schema_Fundamentals](../../10_Data_Modeling_For_Analytics/01_Star_Schema_Fundamentals/) | Degenerate dims are a core star schema concept |
| Factless Fact Tables | [../03_Factless_Fact_Tables](../03_Factless_Fact_Tables/) | Factless facts are often composed entirely of dimension FKs + degenerate dims |
