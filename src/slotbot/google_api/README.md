# google_api

## Overview
The `google_api` module handles OAuth 2.0 authentication and service initialization for the Google Calendar API. It abstracts the credential lifecycle — loading, refreshing, and persisting tokens — so the rest of the application can obtain an authenticated Calendar client with a single call.

## Purpose
- Manage OAuth 2.0 credentials for Google Calendar access
- Automatically refresh expired tokens without user interaction
- Persist tokens locally to avoid repeated browser-based authentication
- Return a ready-to-use Google Calendar API service instance

## Module Components

| Component | Purpose | Key Details |
|-----------|---------|-------------|
| `Oauth_client.py` | OAuth flow and Calendar service factory | Handles token load, refresh, and `build()` call |

---

## 1. Oauth_client.py

### Overview
Implements the full Google OAuth 2.0 installed-application flow. On first run it launches a local browser redirect on port `8080` to obtain user consent. On subsequent runs it loads the saved `token.json` and refreshes it silently if expired.

### Components

| Component | Purpose | Key Details |
|-----------|---------|-------------|
| `SCOPES` | Defines required API permissions | `https://www.googleapis.com/auth/calendar` (full read/write access) |
| `get_calendar_service()` | Authenticates and returns a Calendar API client | Loads `token.json`, refreshes if expired, runs local OAuth flow if missing, saves credentials, returns `build('calendar', 'v3', ...)` |

### Usage Examples

```python
from slotbot.google_api.Oauth_client import get_calendar_service

# Obtain an authenticated service object
service = get_calendar_service()

# List upcoming events
events_result = service.events().list(
    calendarId='primary',
    maxResults=10,
    singleEvents=True,
    orderBy='startTime'
).execute()

events = events_result.get('items', [])
```

> **Prerequisites**:
> - `credentials.json` (downloaded from Google Cloud Console) must be present in the working directory.
> - On first run, a browser window opens for consent. `token.json` is written afterward.

### Significance
Follows the **Single Responsibility Principle** — authentication concerns are fully isolated here, keeping Calendar business logic in other modules clean. The token-persistence pattern avoids forcing re-authentication on every application start, which is essential for an automated scheduling agent like slotbot.

---

## Module Significance

| Aspect | Value |
|--------|-------|
| **Architectural Layer** | Infrastructure / External API adapter |
| **Authentication Protocol** | OAuth 2.0 (InstalledAppFlow) |
| **Token Storage** | `token.json` (local filesystem) |
| **Required Files** | `credentials.json` (Google Cloud OAuth client secrets) |
| **Consumed By** | CrewAI tools that interact with Google Calendar |
| **Google API Scope** | Full Calendar read/write (`auth/calendar`) |
