from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
import uuid

from api.schemas import ChatRequest, ChatResponse
from api.dependencies import get_crew_instance, session_store # Import session_store if needed directly

router = APIRouter()

@router.post("/start_chat", response_model=Dict[str, str])
async def start_chat():
    """
    Starts a new chat session and returns a session ID.
    """
    session_id = str(uuid.uuid4())
    # Initialize the crew instance for this new session and store it
    session_store[session_id] = {"crew": CalendarBookingCrew()}
    return {"session_id": session_id, "message": "Welcome to SlotBot! How can I help you today?"}

@router.post("/chat", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):
    """
    Handles incoming chat messages, processes them using the CalendarBookingCrew,
    and returns the chatbot's response.
    """
    session_id = request.session_id
    user_message = request.user_message

    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found. Please start a new chat.")

    crew_instance = session_store[session_id]["crew"]

    # Prepare inputs for the crew
    inputs = {
        'user_message': user_message,
        'current_date': datetime.now().isoformat()
    }

    try:
        # Execute the crew's workflow
        # The kickoff method returns a dictionary of task outputs.
        # We need to find the output of the 'format_user_response' task.
        crew_result = crew_instance.crew().kickoff(inputs=inputs)
        
        # The output of the last task (format_user_response) should be the chatbot's response.
        # We need to ensure that the crew.py is structured to return this.
        # Assuming the result is a dictionary where keys are task names.
        chatbot_response = crew_result.get('format_user_response', 'An error occurred during processing.')
        
        # If the crew's output is a TaskOutput object, we'd access its raw attribute.
        # For example:
        # if isinstance(crew_result, TaskOutput):
        #     chatbot_response = crew_result.raw
        # else:
        #     chatbot_response = "Unexpected output format from crew."

        return ChatResponse(session_id=session_id, chatbot_response=chatbot_response)

    except Exception as e:
        # Log the error for debugging
        print(f"Error during chat processing for session {session_id}: {e}")
        # In a real application, you'd want more sophisticated error logging and handling.
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
