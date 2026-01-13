
## 1️⃣ Principles

* One endpoint per  **logical functionality** , not per agent.
* Agents are  **internal orchestration** , not exposed as separate endpoints.
* Endpoints should be **RESTful** and return structured JSON (schemas from `/schemas/`).

---

## 2️⃣ Recommended MVP API Endpoints

| Endpoint                    | HTTP Method | Purpose                                                               | Input / Output                                | Notes                                                           |
| --------------------------- | ----------- | --------------------------------------------------------------------- | --------------------------------------------- | --------------------------------------------------------------- |
| `/api/ingest/bursa`       | POST        | Trigger ingestion of Bursa announcements / PDFs                       | Input:`year`, optional `company`          | Returns ingestion status, number of announcements ingested      |
| `/api/ingest/news`        | POST        | Trigger news scraping / ingestion                                     | Input:`sources`,`keywords`,`date_range` | Returns status and count                                        |
| `/api/intelligence/query` | POST        | Main Copilot chat interface                                           | Input:`query_text`, optional `user_role`  | Output: CopilotAnswer JSON (text + citations + tables + alerts) |
| `/api/alerts`             | GET         | List current alerts                                                   | Input: optional `company_code`/`severity` | Output: list of active alerts, reasons, links                   |
| `/api/sql`                | POST        | Run natural language → SQL queries on tabular Bursa / financial data | Input:`query_text`                          | Output: table / numeric results (structured JSON)               |
| `/api/documents/{doc_id}` | GET         | Fetch raw / processed document                                        | Input:`doc_id`                              | Output: structured document object (for RAG / NLP debugging)    |
| `/api/health`             | GET         | System health check                                                   | None                                          | Returns status of ETL, DB, vector DB, agents                    |

---

### 3️⃣ Optional / Future Extensions

* `/api/ingest/upload` → for manual PDF or CSV upload
* `/api/intelligence/summary` → auto-generated company summary
* `/api/alerts/config` → allow UI-based alert rules (MVP can hardcode)

---

## 4️⃣ Total Count (MVP)

* **Core endpoints:** 6–7
* Optional: +2 for uploads / config

---

## 5️⃣ Mapping to Agents

| API Endpoint            | Uses Agent(s)                               |
| ----------------------- | ------------------------------------------- |
| `/intelligence/query` | Supervisor → RAG / NLP / Financial / Alert |
| `/sql`                | Supervisor → SQL agent                     |
| `/alerts`             | Alert agent (direct or via Supervisor)      |
| `/ingest/*`           | ETL pipeline (no agent)                     |
| `/documents/{doc_id}` | ETL output (no agent)                       |
| `/health`             | None (system check)                         |

---

### ✅ Key Takeaways

1. **Agents are *internal*** — you don’t need separate endpoints for each.
2. **Copilot / query endpoint** is the **main interface** for chat.
3. ETL / ingestion endpoints are  **trigger-only** , not user-facing.
4. Alerts can be **fetched via a GET** endpoint.
