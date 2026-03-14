# Oracle Architecture — Concept Overview

> SGA, PGA, and the multi-process architecture that dominated enterprise databases for 40 years.

## Architecture

```mermaid
flowchart TB
    subgraph "Oracle Instance"
        subgraph "SGA (System Global Area)"
            BC["Buffer Cache<br/>(data blocks)"]
            SP["Shared Pool<br/>(parsed SQL, data dict)"]
            RL["Redo Log Buffer"]
        end
        subgraph "Background Processes"
            DBWR["DBWn (DB Writer)"]
            LGWR["LGWR (Log Writer)"]
            SMON["SMON (System Monitor)"]
            PMON["PMON (Process Monitor)"]
            CKPT["CKPT (Checkpoint)"]
        end
    end
    
    subgraph "Storage"
        DF["Data Files"]
        RF["Redo Log Files"]
        CF["Control Files"]
        UF["Undo Tablespace"]
    end
    
    BC --> DBWR --> DF
    RL --> LGWR --> RF
```

## Oracle vs PostgreSQL Conceptual Mapping

| Oracle Concept | PostgreSQL Equivalent |
|---|---|
| SGA | Shared Buffers + WAL Buffers |
| PGA | Backend process memory (work_mem) |
| Redo Log | WAL (Write-Ahead Log) |
| Undo Tablespace | MVCC dead tuples + VACUUM |
| DBWn | Background Writer + Checkpointer |
| LGWR | WAL Writer |
| Shared Pool | Prepared statement cache |

## References

| Resource | Link |
|---|---|
| *Oracle Database Concepts* | Oracle official documentation |
| *Expert Oracle Database Architecture* | Thomas Kyte |
