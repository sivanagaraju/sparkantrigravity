# Further Reading: Search Engines

## Essential Books

*   **Introduction to Information Retrieval**
    *   *Authors:* Christopher D. Manning, Prabhakar Raghavan and Hinrich Schütze.
    *   *Why:* The academic bible of search engines. Read chapters 1 (Boolean Retrieval), 2 (Term vocabulary), and 11 (Probabilistic Information Retrieval / BM25).
    *   *Link:* [Free HTML Version](https://nlp.stanford.edu/IR-book/information-retrieval-book.html)
*   **Elasticsearch: The Definitive Guide**
    *   *Note:* Although older (based on ES 2.x), the core concepts regarding Lucene segments, inverted indices, and tokenization have not changed.
    *   *Link:* [Elastic Guide](https://www.elastic.co/guide/en/elasticsearch/guide/current/index.html)

## Papers & Algorithms

*   **The BM25 Function (Okapi BM25)**
    *   *Context:* Search moved away from standard TF-IDF to BM25 to prevent documents from being artificially boosted just because they are incredibly long and span many keyword repetitions.
    *   *Link:* Wikipedia provides an excellent mathematical breakdown. Focus on the saturation curve.

## Engineering Blogs & Case Studies

*   **How Uber scales their Real-Time Log Analytics (Uber Engineering)**
    *   *Summary:* Details on how Uber handles petabytes of logs per day, detailing the pipeline from service to Kafka to Logstash to Elasticsearch.
    *   *Search Term:* "Logging at Uber Scale" / "Uber ELK stack architecture"
*   **Slack: How we implemented Search across millions of messages**
    *   *Summary:* Details the challenges of personalized search (authorization filtering) merged with full text relevance ranking.
    *   *Search Term:* "Slack Engineering Search"

## Official Documentation Deep Dives

*   **Elasticsearch Tune for Search Speed**
    *   *Link:* [Elastic Docs - Tune for Search Speed](https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-search-speed.html)
    *   *Why:* Real production checklist from the creators.
*   **Elasticsearch Tune for Indexing Speed**
    *   *Link:* [Elastic Docs - Tune for Indexing Speed](https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-indexing-speed.html)
    *   *Why:* Details why you should disable `refresh_interval` during bulk loads.

## Advanced GitHub Repositories

*   **Apache Lucene**
    *   *Link:* [apache/lucene](https://github.com/apache/lucene)
    *   *Why:* Look into the `core/src/java/org/apache/lucene/index` and `search` directories to see how segments and BM25 scoring are natively implemented in Java.

## Cross-References
*   Review **Storage Engines and Disk Layout** to compare B-Tree disk layout versus Lucene Segment layout.
*   Review **Event Driven Architecture** (Kafka) for understanding the ingest pipeline.
