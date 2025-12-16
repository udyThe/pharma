# System Architecture (Async, Event-Driven)

```mermaid
flowchart LR
    U[Streamlit UI] -->|submit /jobs| API[FastAPI Orchestrator]
    API -->|enqueue| CELERY[Celery Broker/Redis]
    CELERY --> W[Agent Workers (CrewAI)]
    W -->|LLM calls| GROQ[Groq Llama 3 70B]
    W -->|cache/state| REDIS[Redis]
    W -->|events| KAFKA[Kafka]
    KAFKA --> W2[Downstream Workers]
    API -->|poll /jobs/{id}| REDIS
    U -->|poll status| API
    W -->|artifacts| STORE[(Object Storage)]
    W -->|vector| VDB[Vector DB]
```

Key flows
- UI submits jobs to API, which enqueues Celery tasks and tracks status in Redis.
- Workers execute `crew.kickoff()`, cache intermediates, publish events to Kafka, and call Groq.
- UI polls `/jobs/{id}` for status/results; artifacts stored externally.

Deployment (docker-compose)
- Services: `ui`, `api`, `worker`, `redis`, `kafka`, `zookeeper` (or Redpanda).
- Env: `API_BASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_BACKEND_URL`, `KAFKA_BOOTSTRAP_SERVERS`, `GROQ_API_KEY`, data API URLs.

Exportable diagram
- Source Mermaid file: `docs/system_architecture.mmd`
- Render as PNG: `npx @mermaid-js/mermaid-cli -i docs/system_architecture.mmd -o docs/system_architecture.png`

