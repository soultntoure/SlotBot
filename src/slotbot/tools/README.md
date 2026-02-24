# tools

## Overview

This module provides CrewAI-compatible tool wrappers for interacting with Google Calendar. Each tool encapsulates a single calendar operation, exposing it as a callable action that agents can invoke during crew execution.

## Purpose

- Wrap Google Calendar API calls as CrewAI `BaseTool` subclasses
- Enforce typed input schemas so agents pass well-formed arguments
- Isolate external service integration behind a clean tool interface
- Provide a `custom_tool.py` scaffold for adding new tools

## Module Components

| Component | Purpose | Key Details |
|-----------|---------|-------------|
| `calendar_tools.py` | Google Calendar booking and availability tools | `BookAppointmentTool`, `CheckAvailabilityTool` |
| `custom_tool.py` | Scaffold template for new tools | `MyCustomTool` — illustrative, not used in production |

---

## 1. calendar_tools.py

### Overview

Implements two CrewAI tools that wrap the Google Calendar API. Both tools authenticate via the shared OAuth client and operate on the `primary` calendar. All datetime handling is scoped to the Asia/Singapore timezone (UTC+8).

### Components

| Component | Purpose | Key Details |
|-----------|---------|-------------|
| `CheckAvailabilityArgs` | Input schema for availability checks | `date` (YYYY-MM-DD), `time` (HH:MM), `duration` (int, default 60) |
| `BookAppointmentArgs` | Input schema for booking | `date`, `time`, `patient_email`, `duration`, `notes` (optional) |
| `CheckAvailabilityTool` | Queries Google Calendar freebusy API | Returns JSON `{"status": "free"\|"busy", "message": str}` |
| `BookAppointmentTool` | Creates a Google Calendar event | Adds patient as attendee; returns event HTML link on success |

### Usage Examples

```python
from src.slotbot.tools.calendar_tools import CheckAvailabilityTool, BookAppointmentTool

# Check if a slot is free
availability_tool = CheckAvailabilityTool()
result = availability_tool._run(date="2025-07-15", time="17:00", duration=60)
# → '{"status": "free", "message": "The time slot is available."}'

# Book an appointment
booking_tool = BookAppointmentTool()
result = booking_tool._run(
    date="2025-07-15",
    time="17:00",
    patient_email="patient@example.com",
    duration=60,
    notes="Initial consultation",
)
# → 'Appointment booked successfully! You can view it at: https://...'
```

### Significance

Tools follow the Single Responsibility Principle — one class per calendar operation. Input validation is delegated to Pydantic schemas (`args_schema`), keeping `_run` focused on API interaction. Errors from the Google API (`HttpError`) are caught and returned as strings so agents can relay meaningful failure messages without raising exceptions.

---

## 2. custom_tool.py

### Overview

A minimal scaffold that demonstrates the structure required to add a new CrewAI tool. Not wired into any agent or crew; exists solely as a starting template.

### Components

| Component | Purpose | Key Details |
|-----------|---------|-------------|
| `MyCustomToolInput` | Example Pydantic input schema | Single `argument: str` field |
| `MyCustomTool` | Example `BaseTool` subclass | `_run` returns a placeholder string |

### Usage Examples

```python
# Copy this pattern to create a new tool:
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class MyNewToolInput(BaseModel):
    param: str = Field(..., description="What this param does")

class MyNewTool(BaseTool):
    name: str = "MyNewTool"
    description: str = "What this tool does (agents read this)."
    args_schema: type[BaseModel] = MyNewToolInput

    def _run(self, param: str) -> str:
        # Call external service here
        return "result"
```

### Significance

Keeping a scaffold file in the module signals the expected pattern for extending the toolset, lowering the barrier for contributors to add new calendar operations or third-party integrations without reading framework documentation.

---

## Module Significance

| Aspect | Value |
|--------|-------|
| **Architectural Layer** | Infrastructure / External Services |
| **Pattern** | Tool-based integration (CrewAI `BaseTool`) |
| **Dependencies** | `google-api-python-client`, `google-auth-oauthlib`, `crewai`, `pydantic` |
| **Consumed By** | `calendar_manager` agent in `src/slotbot/crew.py` |
| **Extension Point** | Add new tools by copying `custom_tool.py` and registering in `crew.py` |
