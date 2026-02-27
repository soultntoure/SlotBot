# SlotBot: CrewAI to LangGraph Migration Plan

## Context

SlotBot is a clinical scheduling assistant built on CrewAI with a 5-task sequential pipeline (parse → validate → branch → format). The current architecture has critical flaws:

- **No conversation history** across turns — the backend only receives the current message
- **In-memory session store** — lost on server restart
- **`next_action` type mismatch** bug — `SessionState` model and routing code disagree on valid values
- **Zero observability** — when routing silently fails, nothing is logged or traceable

Transitioning to LangGraph replaces the implicit CrewAI orchestration with an explicit state machine where every node, edge, and state field is typed and visible — directly solving all of these issues.

| | |
|---|---|
| **Scope** | `src/slotbot/` agentic core only. API and frontend changes deferred. |
| **LLM Provider** | Google AI Studio (`langchain-google-genai` + `GOOGLE_API_KEY` env var) |
| **Human-in-the-loop** | Deferred to a future phase. This plan covers the core graph, checkpointing, and tracing. |

---

## What Gets Reused vs Rewritten

| Current File | Fate | Reason |
|---|---|---|
| `google_api/Oauth_client.py` | **Keep as-is** | No CrewAI dependency, works correctly |
| `tools/calendar_tools.py` | **Port** (same logic, new wrapper) | `BaseTool` → `@tool` decorator |
| `models.py` | **Extend** | Fix `next_action` Literal, keep all 3 models |
| `config/agents.yaml` | **Delete** | Text extracted into `prompts.py` |
| `config/tasks.yaml` | **Delete** | Text extracted into `prompts.py` |
| `crew.py` | **Delete** | Replaced entirely by `graph.py` + `nodes.py` |
| `main.py` | **Rewrite** | CLI invokes graph instead of crew |
| `tools/custom_tool.py` | **Delete** | Unused placeholder |

---

## Phase 1 — Foundation: State Schema & Dependency Setup

> **Desired Outcome:** The project imports LangGraph and `langchain-google-genai`. A typed `SlotBotState` schema is defined and unit-testable in isolation. The `next_action` type bug is fixed. No LLM calls yet.

### Work Items

1. **Fix `SessionState.next_action`** in `src/slotbot/models.py`
   - Add `'check_availability'` to the Literal
   - Currently line 64 declares only `'collect_info' | 'execute_operation'`
   - But `crew.py:100` checks for `'check_availability'`, and `tasks.yaml` (`validate_session_state`) describes it as a valid routing value

2. **Create `src/slotbot/state.py`** — the single typed state dict that flows through the entire graph:

   ```python
   class SlotBotState(TypedDict):
       messages: Annotated[list[BaseMessage], add_messages]  # full conversation history
       current_date: str
       parsed_input: Optional[UserInputParsed]
       session_state: Optional[SessionState]
       calendar_result: Optional[str]
       final_response: Optional[str]
   ```

   The `add_messages` reducer on `messages` automatically appends rather than overwrites — this is the mechanism that solves "no conversation history across turns."

3. **Update `pyproject.toml`** — replace `crewai[tools]>=0.134.0,<1.0.0` with LangGraph dependencies. Add `GOOGLE_API_KEY` to `.env`.

### File Changes

| File | Action | What Changes |
|---|---|---|
| `src/slotbot/models.py` | **Modify** | `next_action: Literal['collect_info', 'check_availability', 'execute_operation']` |
| `src/slotbot/state.py` | **Create** | `SlotBotState` TypedDict with `add_messages` reducer |
| `pyproject.toml` | **Modify** | Replace `crewai[tools]` with `langgraph`, `langchain-google-genai`, `langchain-core`, `langgraph-checkpoint-postgres`, `langsmith` |
| `.env` | **Modify** | Add `GOOGLE_API_KEY` |

### Verification

- [ ] `from slotbot.state import SlotBotState` imports without error
- [ ] `SessionState(next_action='check_availability', ...)` validates without Pydantic error
- [ ] `pip install -e .` succeeds with new dependencies

---

## Phase 2 — Tool Conversion: CrewAI BaseTool → LangChain @tool

> **Desired Outcome:** Both calendar tools are callable as LangChain-compatible `@tool` functions. Independently testable without any CrewAI or LangGraph context. Business logic is identical to the current `_run()` methods.

### Work Items

1. **Rewrite `src/slotbot/tools/calendar_tools.py`**
   - Drop `BaseTool` classes, convert to `@tool` decorated functions
   - The `_run()` method bodies (lines 43–85 for book, lines 102–139 for check) are **copied verbatim**
   - New signatures:
     - `check_availability(date: str, time: str, duration: int = 60) -> str`
     - `book_appointment(date: str, time: str, patient_email: str, duration: int = 60, notes: str | None = None) -> str`
   - Keep `CheckAvailabilityArgs` and `BookAppointmentArgs` Pydantic models as `args_schema`
   - Import stays unchanged: `from ..google_api.Oauth_client import get_calendar_service`

2. **Delete `tools/custom_tool.py`** — unused placeholder that only imports from `crewai.tools`

### File Changes

| File | Action | What Changes |
|---|---|---|
| `src/slotbot/tools/calendar_tools.py` | **Rewrite** | `from crewai.tools import BaseTool` → `from langchain_core.tools import tool`; 2 classes become 2 `@tool` functions, identical logic |
| `src/slotbot/tools/custom_tool.py` | **Delete** | Unused |

### Verification

- [ ] `from slotbot.tools.calendar_tools import check_availability, book_appointment` imports cleanly
- [ ] `check_availability.name == "check_availability"` (LangChain tool interface)
- [ ] Tools invocable via `.invoke({"date": "...", "time": "..."})` (mock `get_calendar_service` for unit test)

---

## Phase 3 — Graph Core: Nodes, Edges, and Routing

> **Desired Outcome:** The complete LangGraph graph replaces `CalendarBookingCrew`. Runnable end-to-end from a CLI script. The conditional routing (validate → collect_info OR calendar_action) works correctly for all 3 `next_action` values. CrewAI is fully removed from the project. LangSmith tracing is active via env vars.

### Target Graph Topology

```
START ─→ parse_input ─→ validate_state ─┬─→ collect_info ────→ format_response ─→ END
                                         │                           ↑
                                         └─→ calendar_action ───────┘
```

### Work Items

1. **Create `src/slotbot/prompts.py`** — extract role/goal/backstory + task descriptions **verbatim** from the YAML files into Python string constants. Each prompt combines the agent's persona with its task instructions:

   | Constant | Source (agents.yaml + tasks.yaml) |
   |---|---|
   | `NLP_PARSER_SYSTEM` | `nlp_parser` + `parse_user_input` |
   | `SESSION_MANAGER_SYSTEM` | `session_manager` + `validate_session_state` |
   | `CALENDAR_MANAGER_SYSTEM` | `calendar_manager` + `execute_calendar_action` |
   | `RESPONSE_AGENT_COLLECT_SYSTEM` | `response_agent` + `collect_missing_information` |
   | `RESPONSE_AGENT_FORMAT_SYSTEM` | `response_agent` + `format_user_response` |

2. **Create `src/slotbot/nodes.py`** — one function per graph node. Each receives `SlotBotState`, calls the LLM (via `ChatGoogleGenerativeAI`), and returns a partial state update dict:

   | Node Function | LLM Usage | Returns |
   |---|---|---|
   | `parse_input(state)` | `llm.with_structured_output(UserInputParsed)` | `{"parsed_input": result}` |
   | `validate_state(state)` | `llm.with_structured_output(SessionState)` | `{"session_state": result}` |
   | `collect_info(state)` | Free-text LLM call for follow-up questions | `{"final_response": text}` |
   | `calendar_action(state)` | `llm.bind_tools([check_availability, book_appointment])` with tool-calling loop | `{"calendar_result": result}` |
   | `format_response(state)` | Free-text LLM call for final user message | `{"final_response": text}` |

3. **Create `src/slotbot/graph.py`** — assembles the `StateGraph`:
   - `route_after_validate(state) -> str` — replaces both `should_collect_info()` and `should_execute_action()` from `crew.py`. Returns `"collect_info"` or `"calendar_action"`. **No silent `"default"` fallback** — unknown values log a warning and route to `"collect_info"`.
   - `build_graph() -> StateGraph` — wires all nodes and edges
   - Module-level `graph = build_graph().compile()` for import

4. **Rewrite `src/slotbot/main.py`** — CLI entry invokes `graph.invoke()` with a `HumanMessage` and `current_date`

5. **Delete CrewAI files** — `crew.py`, `config/agents.yaml`, `config/tasks.yaml`, `config/` folder

6. **Clean up `pyproject.toml`** — remove `[tool.crewai]` section, remove `crewai` from deps, update project description

7. **LangSmith tracing** — add env vars to `.env` (no code changes needed):

   ```
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=lsv2_...
   LANGCHAIN_PROJECT=slotbot
   ```

   When set, every `graph.invoke()` automatically sends a trace with per-node inputs/outputs visible in the LangSmith dashboard.

### File Changes

| File | Action | What Changes |
|---|---|---|
| `src/slotbot/prompts.py` | **Create** | All prompt constants extracted verbatim from YAML files |
| `src/slotbot/nodes.py` | **Create** | 5 node functions (parse_input, validate_state, collect_info, calendar_action, format_response) |
| `src/slotbot/graph.py` | **Create** | `build_graph()`, `route_after_validate()`, compiled `graph` |
| `src/slotbot/main.py` | **Rewrite** | `graph.invoke()` instead of `crew.kickoff()` |
| `src/slotbot/crew.py` | **Delete** | Fully replaced by graph.py + nodes.py |
| `src/slotbot/config/agents.yaml` | **Delete** | Text moved to prompts.py |
| `src/slotbot/config/tasks.yaml` | **Delete** | Text moved to prompts.py |
| `src/slotbot/config/` | **Delete folder** | Empty after YAML removal |
| `pyproject.toml` | **Modify** | Remove `[tool.crewai]`, remove `crewai` dep, update description |
| `.env` | **Modify** | Add `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` |

### Verification

- [ ] `python -m slotbot.main` runs the full graph end-to-end with a hardcoded test message
- [ ] `route_after_validate` returns `"collect_info"` for incomplete input, `"calendar_action"` for complete input
- [ ] `from slotbot.graph import graph` compiles without error
- [ ] No `crewai` imports remain anywhere in `src/slotbot/` (`grep -r "crewai" src/` returns nothing)
- [ ] LangSmith dashboard shows traces with all 5 nodes and their inputs/outputs

---

## Phase 4 — Persistence: Postgres Checkpointing

> **Desired Outcome:** Graph state survives server restarts. Each session maps to a LangGraph `thread_id`. Re-invoking with the same thread resumes from saved state with full message history. Multi-turn conversations actually work — the LLM sees all prior messages, not just the current one.

### Work Items

1. **Create `src/slotbot/checkpointer.py`** — factory that reads `POSTGRES_URL` from env and returns a `PostgresSaver`:

   ```python
   def get_checkpointer() -> PostgresSaver:
       conn_str = os.environ["POSTGRES_URL"]
       return PostgresSaver.from_conn_string(conn_str)
   ```

2. **Modify `src/slotbot/graph.py`** — pass checkpointer to `.compile()`:

   ```python
   graph = build_graph().compile(checkpointer=get_checkpointer())
   ```

3. **Update `src/slotbot/main.py`** — pass `config={"configurable": {"thread_id": session_id}}` to `graph.invoke()`. This ties the conversation to a persistent thread.

4. **Add `.env` entry** for `POSTGRES_URL`

### File Changes

| File | Action | What Changes |
|---|---|---|
| `src/slotbot/checkpointer.py` | **Create** | `get_checkpointer()` factory, reads `POSTGRES_URL` from env |
| `src/slotbot/graph.py` | **Modify** | `.compile(checkpointer=get_checkpointer())` |
| `src/slotbot/main.py` | **Modify** | Add `thread_id` config to `graph.invoke()` |
| `.env` | **Modify** | Add `POSTGRES_URL=postgresql://user:pass@localhost:5432/slotbot` |

### Verification

- [ ] Invoke graph with thread `"test-1"`, send `"book appointment"` → get response asking for info
- [ ] Invoke again with same thread `"test-1"`, send `"my email is x@y.com"` → `state["messages"]` contains both turns (the LLM sees prior context)
- [ ] Restart Python process, invoke with thread `"test-1"` → state recovered from Postgres, conversation continues
- [ ] Unit tests use `MemorySaver()` as a drop-in in-memory replacement (no Postgres needed for CI)

---

## Final Target Directory Layout

```
src/slotbot/
├── __init__.py               # unchanged
├── state.py                  # NEW (Phase 1) — SlotBotState TypedDict
├── models.py                 # MODIFIED (Phase 1) — fixed next_action Literal
├── prompts.py                # NEW (Phase 3) — all LLM prompt constants
├── nodes.py                  # NEW (Phase 3) — 5 node functions
├── graph.py                  # NEW (Phase 3, modified Phase 4) — compiled StateGraph
├── checkpointer.py           # NEW (Phase 4) — PostgresSaver factory
├── main.py                   # REWRITTEN (Phase 3, modified Phase 4) — CLI via graph.invoke()
├── tools/
│   ├── __init__.py
│   └── calendar_tools.py     # REWRITTEN (Phase 2) — @tool functions, same logic
└── google_api/
    └── Oauth_client.py       # UNCHANGED

DELETED:
├── crew.py
├── config/agents.yaml
├── config/tasks.yaml
└── tools/custom_tool.py
```

---

## Known Issues Resolution Tracker

| Issue | Fixed In | How |
|---|---|---|
| No conversation history across turns | Phase 1 + 4 | `messages: Annotated[list, add_messages]` + Postgres thread persistence |
| In-memory session store lost on restart | Phase 4 | `PostgresSaver` checkpointer tied to `thread_id` |
| `next_action` type mismatch bug | Phase 1 | Add `'check_availability'` to `SessionState.next_action` Literal |
| No observability / silent routing fallback | Phase 3 | `route_after_validate` logs warnings + LangSmith traces all nodes |
| Tools are CrewAI `BaseTool` | Phase 2 | Rewrite as LangChain `@tool` functions |
| `BookAppointmentOutput` never wired | Phase 3 | `calendar_action` node returns it into typed `state["calendar_result"]` |

---

## Future Work (not in this plan)

- **Human-in-the-loop interrupts** — add `interrupt_before=["collect_info"]` to `.compile()` for ambiguous/edge cases
- **API layer adaptation** — replace `session_store` dict + `crew.kickoff()` with `graph.invoke()` + thread config
- **Frontend adaptation** — wire the API changes through to the React chat UI
