# Feedback Intelligence Backend — GPT-only (Topics + Sentiment) + UI

All language analysis uses a GPT model via the OpenAI API.

## 1. Setup & Usage

### Prerequisites
* **Python 3.8+**
* **`quickstart.sh`** must be executable: `chmod +x quickstart.sh`

### Environment Setup
1.  **Set OpenAI API Key:** The application requires an OpenAI API key to perform sentiment and topic analysis.
    ```bash
    export OPENAI_API_KEY="sk-..."
    ```
2.  **Optional: Set GPT Model:** You can override the default GPT model.
    ```bash
    export GPT_MODEL="gpt-4.1-nano" # (or gpt-3.5-turbo, gpt-4o, etc.)
    ```

### How to Run the App and Tests
The `quickstart.sh` script handles environment setup, dependency installation, testing, and running the server.

| Command | Action | Notes |
| :--- | :--- | :--- |
| `./quickstart.sh` | **Install, Test, and Run** | Installs dependencies, runs tests, then starts the server. |
| `./quickstart.sh test` | **Run Tests Only** | Runs `pytest`. When `TESTING=1`, the NLP module uses an offline stub instead of calling the OpenAI API. |
| `./quickstart.sh run` | **Run Server Only** | Starts the `uvicorn` server on `http://0.0.0.0:8000`. Requires `OPENAI_API_KEY`. |
| `./quickstart.sh reset`| **Reset Database** | Deletes the local SQLite database file (`app/app.db`). |

### Access
* **API Documentation (Swagger UI):** `http://localhost:8000/docs`
* **Application/UI (if one exists):** `http://localhost:8000/`

---

## 2. Assumptions Made

### Customer Data & Feedback
* **Feedback Volume:** We assume the initial feedback volume is low to moderate, suitable for a prototype and paying per-request to a third-party LLM API.
* **Language:** Assumed to be English for direct consumption by the LLM (GPT). Non-English feedback would require pre-translation or a multilingual LLM.
* **Latency Tolerance:** We assume the API caller can tolerate the typical latency (several hundred milliseconds to a few seconds) associated with an external GPT API call for topic and sentiment analysis, as this processing happens synchronously upon feedback submission.

### Topics & Sentiment
* **Fixed Categories:** The initial set of topics (`product_quality`, `delivery`, `pricing`, `customer_service`, `other`) is assumed to cover the vast majority of feedback use cases.
* **LLM Accuracy:** We assume the chosen GPT model provides sufficient accuracy for sentiment and topic classification for our business needs.

### System Behavior
* **Alerting Logic:** We assume an alert is warranted immediately upon receiving a single negative sentiment feedback. More sophisticated threshold-based alerting (e.g., "5 negative in 1 hour") is not implemented.
* **Local Persistence:** The use of SQLite (`app/app.db`) implies that the system is intended for single-instance, local development or low-volume prototyping, not multi-instance production deployment.

---

## 3. Technical Decisions Log

### Language
| Choice | Why Chosen | Alternatives & Why Rejected |
| :--- | :--- | :--- |
| **Python** | **Maturity and Ecosystem** for web services (FastAPI/Uvicorn), data handling, and direct, excellent library support for **OpenAI API** (`openai>=1.40.0`). | **Node.js/TypeScript**: Good for high concurrency but would introduce more boilerplate for LLM and database interaction in this context. |

### Web Framework
| Choice | Why Chosen | Alternatives & Why Rejected |
| :--- | :--- | :--- |
| **FastAPI** | **Performance** (asynchronous nature via Starlette/Uvicorn), **Automatic Documentation** (Swagger UI/OpenAPI spec), and ease of defining **Pydantic** data models for request/response validation. | **Flask**: Simpler for microservices but lacks built-in asynchronous support and auto-documentation without extra libraries. **Django**: Too heavy and feature-rich for a simple API backend. |

### Storage
| Choice | Why Chosen | Alternatives & Why Rejected |
| :--- | :--- | :--- |
| **SQLite with SQLAlchemy 2.0** | **Simplicity and Zero-Config** for development/prototyping (via `app/app.db`). **SQLAlchemy** provides a robust ORM and future-proof migration path to a production database. | **PostgreSQL/MySQL**: Overkill for a local prototype; introduces external dependency/setup complexity. **NoSQL (MongoDB)**: Less suitable for structured, relational data like customer feedback linked to customers. |

### Core Logic (NLP/Intelligence)
| Choice | Why Chosen | Alternatives & Why Rejected |
| :--- | :--- | :--- |
| **OpenAI GPT Model** | **SOTA Performance** for zero-shot text classification (sentiment/topic) and **speed of implementation**. Allows immediate focus on business logic rather than model training/tuning. | **Open Source LLM (e.g., Llama 3)**: Requires managing infrastructure (e.g., GPUs via self-hosting or services like Hugging Face) and potentially more effort for prompt engineering or fine-tuning to reach target accuracy. |

---

## 4. If This Went to Production

### Prioritized Improvements

1.  **Asynchronous LLM Calls:** Current implementation likely blocks the worker process while waiting for the GPT API response. This must be refactored to use `async/await` within FastAPI to keep the server non-blocking and handle more concurrent requests.
2.  **Robust Error Handling:** Implement retries and circuit breakers for external API calls (OpenAI) to handle transient errors and service unavailability gracefully.
3.  **Alerting Abstraction:** Abstract the alerting mechanism (currently a simple DB read) to an external service (e.g., PagerDuty, email, Slack) via a dedicated, non-blocking background task.
4.  **Database Migration Tool:** Introduce Alembic for schema migrations instead of relying on `Base.metadata.create_all()` for production.

### Scaling, Security, and Monitoring

#### Scaling
* **Database:** Migrate from SQLite to a managed **PostgreSQL or MySQL** database service (e.g., AWS RDS, Azure Database) to support concurrent writes, backups, and replication.
* **Application:** Deploy the FastAPI application using **Docker/Kubernetes** and scale horizontally by adding more instances behind a load balancer.
* **LLM Cost/Latency:**
    * For high volume, introduce an **in-memory cache** (e.g., Redis) for recently processed, identical feedback messages.
    * Consider **batching** API calls if the submission pattern allows it, or exploring **fine-tuning** an open-source model if costs become prohibitive.

#### Security
* **Secrets Management:** Store `OPENAI_API_KEY` and database credentials in a secure vault (e.g., AWS Secrets Manager, HashiCorp Vault) and inject them securely into the running container, rather than using plain environment variables.
* **Input Validation:** Ensure all API endpoints have strict Pydantic models with maximum lengths and type checking to prevent injection attacks and resource exhaustion.
* **Rate Limiting:** Implement rate limiting on the `/feedback` endpoint to protect against abuse and control costs associated with the external LLM API.

#### Monitoring
* **Application Performance Monitoring (APM):** Use a tool like **Datadog, New Relic, or Prometheus/Grafana** to monitor key metrics:
    * **Latency:** Track P95/P99 latency, particularly for the `/feedback` endpoint (as it involves external API latency).
    * **Error Rate:** Monitor HTTP 5xx errors and external API call failure rates.
* **Logging:** Implement structured logging (JSON format) and centralize logs into a system like the **ELK stack (Elasticsearch, Logstash, Kibana)** for easy searching and analysis.
* **Cost Monitoring:** Implement a dashboard to track **OpenAI API usage and costs** to set budgets and detect unexpected spikes.