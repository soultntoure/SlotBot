# slotbot

## Overview

This is the core application package for SlotBot. It orchestrates a four-agent CrewAI pipeline that parses natural language scheduling requests, validates session state, executes Google Calendar operations, and returns a clinical-quality response — all in a single `kickoff` call.

## Purpose

- Define all CrewAI agents, tasks, and conditional execution logic
- Provide structured Pydantic models shared across agents and the API
- Expose a CLI entry point for local testing
- House Google API authentication and calendar tool integrations

## Module Components

| Component | Purpose | Key Details |
|-----------|---------|-------------|
| `crew.py` | Agent/task orchestration | `CalendarBookingCrew` — 4 agents, 5 tasks, conditional branching |
| `models.py` | Shared Pydantic data models | `UserInputParsed`, `SessionState`, `BookAppointmentOutput` |
| `main.py` | CLI entry point | `run()` — fires a hardcoded sample request for local testing |
| `tools/` | Google Calendar tool wrappers | See [tools/README.md](tools/README.md) |
| `config/` | YAML agent and task definitions | `agents.yaml`, `tasks.yaml` |
| `google_api/` | OAuth authentication client | `Oauth_client.py` — `get_calendar_service()` |

---

## Python Files in This Module

### 1. crew.py

#### Overview

Defines `CalendarBookingCrew`, the central orchestrator decorated with `@CrewBase`. It wires four specialized agents to five tasks executed sequentially, with two of those tasks being conditional — they run only when the session state warrants it.

#### Components

| Component | Purpose | Key Details |
|-----------|---------|-------------|
| `CalendarBookingCrew` | Main crew class | `@CrewBase` decorated; holds `_session_state_output` for inter-task state |
| `nlp_parser` agent | NLP intent extraction | Gemini 2.5 Flash; resolves relative dates to ISO 8601 |
| `session_manager` agent | Session routing | Determines `next_action`: `collect_info` or `execute_operation` |
| `calendar_manager` agent | Calendar execution | Equipped with `BookAppointmentTool` and `CheckAvailabilityTool` |
| `response_agent` agent | Response generation | Produces patient-facing, clinical-quality messages |
| `parse_user_input` task | NLP parsing | Output: `UserInputParsed` |
| `validate_session_state` task | State determination | Output: `SessionState`; triggers `_save_session_state` callback |
| `collect_missing_information` task | Info gathering | `ConditionalTask` — runs when `next_action == 'collect_info'` |
| `execute_calendar_action` task | Calendar API call | `ConditionalTask` — runs when `next_action` is `check_availability` or `execute_operation` |
| `format_user_response` task | Response formatting | Always runs; synthesises outputs from conditional tasks |
| `_save_session_state()` | Callback bridge | Captures `validate_session_state` output into `_session_state_output` |
| `_get_next_action()` | State reader | Parses `next_action` from stored JSON; returns `'default'` on failure |
| `should_collect_info()` | Condition function | Returns `True` when `next_action == 'collect_info'` |
| `should_execute_action()` | Condition function | Returns `True` when `next_action` is an execution intent |

#### Usage Examples

```python
from src.slotbot.crew import CalendarBookingCrew
from datetime import datetime

crew_instance = CalendarBookingCrew()
result = crew_instance.crew().kickoff(inputs={
    "user_message": "Book me an appointment on Friday at 3pm, patient@example.com",
    "current_date": datetime.now().isoformat(),
})
print(result.raw)
```

#### Significance

The callback-based state bridge (`_save_session_state` → `_get_next_action`) solves a CrewAI limitation: `ConditionalTask` condition functions receive the previous task's output, but that output may not yet be serialised. Storing raw output in `_session_state_output` and re-parsing it in the condition functions makes conditional routing reliable across all CrewAI output formats.

---

### 2. models.py

#### Overview

Defines three Pydantic models used as structured outputs for crew tasks. They serve as the data contract between agents, ensuring downstream tasks receive typed, validated information rather than raw strings.

#### Components

| Component | Purpose | Key Details |
|-----------|---------|-------------|
| `UserInputParsed` | NLP extraction result | `intent` (Literal), `patient_email`, `start_time`, `end_time`, `temporal_expression`, `missing_info` |
| `SessionState` | Routing decision | `identity_status`, `info_completeness_status`, `missing_info`, `next_action` |
| `BookAppointmentOutput` | Booking result | `status` (`booked`/`failed`), `confirmation_details`, `failure_reason` |

#### Usage Examples

```python
from src.slotbot.models import UserInputParsed, SessionState

# Used as output_pydantic in Task definitions:
task = Task(config=..., output_pydantic=UserInputParsed)

# Direct instantiation for testing:
parsed = UserInputParsed(
    intent="book",
    patient_email="patient@example.com",
    start_time="2025-07-15T17:00:00",
    end_time="2025-07-15T18:00:00",
    missing_info=[],
)
```

#### Significance

Using `output_pydantic` on tasks forces the LLM to emit valid JSON matching the model schema. This eliminates brittle string parsing between agents and gives the API layer a predictable response contract.

---

### 3. main.py

#### Overview

Minimal CLI script for running the crew locally with a hardcoded sample message. Used for quick smoke-testing without standing up the API server.

#### Components

| Component | Purpose | Key Details |
|-----------|---------|-------------|
| `run()` | CLI entry point | Calls `CalendarBookingCrew().crew().kickoff(inputs={...})` |

#### Usage Examples

```bash
# Run from project root (requires Google credentials):
python -m src.slotbot.main
```

```python
from src.slotbot.main import run
result = run()
```

#### Significance

Keeps the development feedback loop short — engineers can validate agent behaviour and task sequencing without HTTP tooling.

---

## Subdirectories

### tools/

**Purpose**: Google Calendar tool wrappers exposed to the `calendar_manager` agent.

**Key Components**: `BookAppointmentTool`, `CheckAvailabilityTool`, `custom_tool.py` scaffold.

For technical details, see [tools/README.md](tools/README.md)

---

### config/

**Purpose**: YAML definitions for all agents (`agents.yaml`) and tasks (`tasks.yaml`). Separates prompt engineering and agent configuration from Python orchestration logic.

**Key Components**: Role, goal, and backstory definitions for 4 agents; description, expected output, and agent assignments for 5 tasks.

---

### google_api/

**Purpose**: Google Calendar OAuth 2.0 authentication. Manages token refresh and first-time browser-based auth flow.

**Key Components**: `get_calendar_service()` — returns an authenticated `googleapiclient` service object. Reads from `token.json`; falls back to `credentials.json` OAuth flow on port 8080.

---

## Module Significance

| Aspect | Value |
|--------|-------|
| **Architectural Layer** | Domain / Application Core |
| **Pattern** | Multi-agent orchestration (CrewAI `@CrewBase`) |
| **LLM** | Gemini 2.5 Flash Lite (`gemini/gemini-2.5-flash-lite-preview-06-17`) |
| **Dependencies** | `crewai`, `pydantic`, `google-api-python-client`, `python-dotenv` |
| **Consumed By** | `api/` layer via `CalendarBookingCrew` import |
| **Key Design Decision** | Callback bridge for reliable conditional task routing |
