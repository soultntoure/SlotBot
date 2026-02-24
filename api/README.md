# api

## Overview

This module is the FastAPI HTTP layer for SlotBot. It exposes a session-based chat interface over REST, mapping incoming user messages to `CalendarBookingCrew` executions and returning the crew's natural language response to the caller.

## Purpose

- Serve a stateful chat API with per-session crew instances
- Handle request validation and response serialisation via Pydantic schemas
- Bridge the HTTP transport layer to the core `slotbot` domain package
- Provide health and root endpoints for operational monitoring

## Module Components

| Component | Purpose | Key Details |
|-----------|---------|-------------|
| `main.py` | FastAPI app factory | Registers CORS, mounts routers, exposes `GET /` |
| `schemas.py` | API-level Pydantic models | `ChatRequest`, `ChatResponse` |
| `dependencies.py` | Session lifecycle management | `get_crew_instance()`, `create_new_session()`, `session_store` |
| `routes/` | Route handlers | `POST /start_chat`, `POST /chat`, `GET /health` |

---

## Python Files in This Module

### 1. main.py

#### Overview

Creates the FastAPI application, applies CORS middleware permitting all origins, and mounts the `chat` and `health` routers. Also defines a root endpoint for basic liveness confirmation.

#### Components

| Component | Purpose | Key Details |
|-----------|---------|-------------|
| `app` | FastAPI instance | CORS: all origins, methods, and headers allowed |
| `session_store` | In-memory session map | `Dict[str, Any]` keyed by session UUID |
| `GET /` | Root liveness endpoint | Returns `{"message": "SlotBot API is running"}` |
| `chat_router` | Chat route group | Mounted from `api.routes.chat` |
| `health_router` | Health route group | Mounted from `api.routes.health` |

#### Usage Examples

```bash
# Start the API server from the project root:
uvicorn api.main:app --reload --port 8000
```

```python
# The app object can be imported directly in tests:
from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.get("/")
assert response.json() == {"message": "SlotBot API is running"}
```

#### Significance

CORS is currently open (`allow_origins=["*"]`) to support local frontend development. In production this should be scoped to known origins. The `session_store` is intentionally in-memory for simplicity; replacing it with Redis or a database is the primary scaling concern.

---

### 2. schemas.py

#### Overview

Defines the public API data contract. Keeps API-level models separate from the internal domain models in `src/slotbot/models.py`, ensuring the HTTP surface can evolve independently of crew internals.

#### Components

| Component | Purpose | Key Details |
|-----------|---------|-------------|
| `ChatRequest` | Incoming chat payload | `session_id: str`, `user_message: str` |
| `ChatResponse` | Outgoing chat payload | `session_id: str`, `chatbot_response: str` |

#### Usage Examples

```python
from api.schemas import ChatRequest, ChatResponse

# Deserialise incoming request body:
request = ChatRequest(session_id="abc-123", user_message="Book me Friday at 3pm")

# Serialise outgoing response:
response = ChatResponse(session_id="abc-123", chatbot_response="Your appointment is confirmed.")
```

#### Significance

Thin, explicit schemas at the API boundary follow the Open-Closed Principle — internal model changes do not force API consumers to update. The commented-out `SessionStateAPI` and `UserInputParsedAPI` examples show how internal state can be surfaced to the frontend if needed.

---

### 3. dependencies.py

#### Overview

Manages the in-memory `session_store` and provides two helper functions consumed by route handlers. Each session maps to a dedicated `CalendarBookingCrew` instance, preserving per-user conversation state across requests.

#### Components

| Component | Purpose | Key Details |
|-----------|---------|-------------|
| `session_store` | Module-level session registry | `Dict[str, {"crew": CalendarBookingCrew}]` |
| `get_crew_instance()` | Lazy crew retrieval | Creates a new crew if session ID is unseen; returns existing otherwise |
| `create_new_session()` | Session initialisation | Generates a UUID, pre-warms a crew instance, stores in `session_store` |

#### Usage Examples

```python
from api.dependencies import get_crew_instance, create_new_session

# Start a new session:
session_id = create_new_session()

# Retrieve the crew for an existing session:
crew = get_crew_instance(session_id)
result = crew.crew().kickoff(inputs={...})
```

#### Significance

Isolating session logic here (rather than inside route handlers) keeps routes thin and testable. The note in the docstring acknowledges the current limitation: `CalendarBookingCrew._session_state_output` is instance-level state, so concurrent requests to the same session could cause race conditions — a known trade-off for the current in-memory design.

---

## Subdirectories

### routes/

**Purpose**: Contains individual `APIRouter` modules, one per resource group, keeping route handlers focused and independently testable.

**Key Components**:
- `chat.py` — `POST /start_chat` (creates session), `POST /chat` (runs crew, returns response with multi-format output handling)
- `health.py` — `GET /health` (returns `{"status": "ok"}`)

---

## Module Significance

| Aspect | Value |
|--------|-------|
| **Architectural Layer** | Interface / Transport (HTTP) |
| **Pattern** | Router-per-resource, thin controllers, dependency injection |
| **Dependencies** | `fastapi`, `uvicorn`, `pydantic`, `src.slotbot.crew` |
| **Consumed By** | Frontend clients; external HTTP consumers |
| **Session Strategy** | In-memory `Dict`; swap for Redis/DB in production |
| **Key Design Decision** | Multi-format crew output handling in `routes/chat.py` ensures resilience across CrewAI output types (`TaskOutput.raw`, `str`, `dict`) |
