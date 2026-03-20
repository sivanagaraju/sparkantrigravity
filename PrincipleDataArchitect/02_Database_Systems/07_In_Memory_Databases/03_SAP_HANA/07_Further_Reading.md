# Further Reading: SAP HANA

## 📚 Books
- **SAP HANA 2.0: An Introduction** by Denys van Kempen (ISBN: 9781493218578) — *The foundational textbook for SAP DBAs detailing the entire architecture from delta merges to scale-out topology.*
- **Data Intensive Applications** by Martin Kleppmann (ISBN: 9781449373320) — *Chapter 3 covers the core difference between analytical column stores and transactional row stores, the fundamental duality HANA attempts to bridge.*
- **Core Data Services for ABAP** by Renzo Colle (ISBN: 9781493218981) — *Detailed technical guides on moving from the "Data-to-code" paradigm to pushing analytical views deep into the HANA database engine.*

## 📄 Academic Papers & Core Articles
- **[A Common Database Approach for OLTP and OLAP Using an In-Memory Column Database](https://dl.acm.org/doi/10.1145/1559845.1559846)** (Hasso Plattner, 2009) — *The literal foundational paper from SAP's co-founder introducing the HTAP concept and laying the architectural groundwork for what became SAP HANA.*
- **[The SAP HANA Database – An Architecture Overview](https://sites.computer.org/debull/A12mar/hana.pdf)** (Färber et al.) — *A rigorous technical breakdown of the C++ dictionary encoding, L1/L2 Delta structure, and NUMA thread bindings.*

## 🏢 FAANG & Enterprise Engineering Blogs
- **[Intel Optane PMem with SAP HANA](https://www.intel.com/content/www/us/en/architecture-and-technology/optane-dc-persistent-memory.html)** (Intel Labs) — *Detailed breakdown of the non-volatile memory hardware transformation that allows massive HANA instances to reboot instantly.*
- **[Migrating Walmart’s Legacy supply chain to S/4HANA](https://www.sap.com/)** (SAP TechEd Case Studies) — *Various conference keynotes historically discuss the technical scaling of the world's largest retail database onto clustered in-memory appliances.*

## 📺 Conference Talks
- **[SAP HANA Architecture Under the Hood](https://www.youtube.com/watch?v=R9_uQJ8k658)** (SAP TechEd Keynotes) — *Visual diagrams of the split between the Index Server, Name Server, and XS Engine architectures within the HANA scale-out environment.*
- **[The Code-to-Data Paradigm Shift](https://www.youtube.com/watch?v=0kHwGgOa9v0)** — *Understanding how ABAP integration evolved to strictly push complex join execution into the HANA SIMD layer.*

## 💻 Curated GitHub Repositories & Docs
- **[Official SAP HANA Performance Guide](https://help.sap.com/docs/SAP_HANA_PLATFORM)** — *Read specifically the chapters on "Delta Merge", "Statement Memory Restrictions", and "Native Storage Extension (NSE)".*
- **[SAP HANA Advanced Modeling](https://github.com/SAP-samples)** — *Examples of HANA SQLScript, Core Data Services (CDS), and Calculation Views used to push logic to the lowest hardware levels.*

## 🔗 Cross-References within this Curriculum
- For details on pure transient in-memory architectures (which HANA is NOT), read `02_Memcached`.
- For background on the disk storage limitations that necessitated HANA's creation, refer to `01_Storage_Engines_and_Disk_Layout`.
