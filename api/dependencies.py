from src.slotbot.crew import CalendarBookingCrew
from typing import Dict, Any
import uuid

# In-memory store for session state (for demonstration)
# In a production app, this would be a database or cache
session_store: Dict[str, Any] = {}

def get_crew_instance(session_id: str) -> CalendarBookingCrew:
    """
    Retrieves or creates a CalendarBookingCrew instance for a given session ID.
    """
    if session_id not in session_store:
        # Initialize a new crew instance for the session
        # Note: The crew's internal state (like _session_state_output)
        # will be managed per instance. For a true multi-user/multi-session
        # scenario, more robust state management might be needed.
        session_store[session_id] = {"crew": CalendarBookingCrew()}
    return session_store[session_id]["crew"]

def create_new_session() -> str:
    """
    Generates a new unique session ID.
    """
    session_id = str(uuid.uuid4())
    # Initialize the crew instance for this new session
    session_store[session_id] = {"crew": CalendarBookingCrew()}
    return session_id
