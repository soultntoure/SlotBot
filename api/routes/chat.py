from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
import uuid

from api.schemas import ChatRequest, ChatResponse
from src.slotbot.crew import CalendarBookingCrew
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
        # The kickoff method returns the output of the final task.
        # This output can be a TaskOutput object, a CrewOutput object, a string, or a dictionary.
        crew_result = crew_instance.crew().kickoff(inputs=inputs)
        
        chatbot_response = "An error occurred during processing." # Default error message

        # --- Robustly extract chatbot_response ---

        # Check if the result is a TaskOutput object (common in CrewAI)
        # We need to import TaskOutput or check for its common attributes if not directly importable.
        # Let's assume TaskOutput has a 'raw' attribute for the string output.
        # If TaskOutput is not directly importable, you might need to duck-type it by checking for 'raw'.
        # For example, check if it has a 'raw' attribute and if that attribute is a string.
        
        if hasattr(crew_result, 'raw') and isinstance(crew_result.raw, str):
            # This covers cases where kickoff returns a TaskOutput object
            chatbot_response = crew_result.raw
            print(f"DEBUG: Extracted response from TaskOutput.raw: {chatbot_response}")
        elif isinstance(crew_result, str):
            # If the result is directly a string
            chatbot_response = crew_result
            print(f"DEBUG: Crew result is a string: {chatbot_response}")
        elif isinstance(crew_result, dict):
            # If the result is a dictionary, try to find the response.
            # The 'format_user_response' task description implies it returns a friendly message,
            # which might be directly in a dict key or the dict itself.
            if 'response' in crew_result:
                chatbot_response = crew_result['response']
                print(f"DEBUG: Extracted response from dict['response']: {chatbot_response}")
            elif 'chatbot_response' in crew_result: # Another common key
                chatbot_response = crew_result['chatbot_response']
                print(f"DEBUG: Extracted response from dict['chatbot_response']: {chatbot_response}")
            else:
                # If it's a dict but doesn't contain a recognized response key,
                # try to stringify it, or assume it's an error.
                # The Crew Completion message you showed is a string that might be formatted.
                # If the whole dict represents the output, converting it to string might be an option.
                chatbot_response = str(crew_result) # Attempt to stringify the whole dictionary
                print(f"DEBUG: Crew result is a dict, but no known keys found. Stringified result: {chatbot_response}")
        elif hasattr(crew_result, 'dict') and callable(crew_result.dict):
            # This might be relevant if CrewOutput has a method to get its dict representation
            dict_representation = crew_result.dict()
            if 'response' in dict_representation:
                 chatbot_response = dict_representation['response']
                 print(f"DEBUG: Extracted response from CrewOutput.dict()['response']: {chatbot_response}")
            elif 'chatbot_response' in dict_representation:
                 chatbot_response = dict_representation['chatbot_response']
                 print(f"DEBUG: Extracted response from CrewOutput.dict()['chatbot_response']: {chatbot_response}")
            else:
                 # If it's a dict-like object but doesn't have known keys, stringify it.
                 chatbot_response = str(dict_representation)
                 print(f"DEBUG: CrewOutput.dict() has no known keys. Stringified: {chatbot_response}")
        else:
            # Fallback for any other unexpected format, including the literal 'CrewOutput' object
            # If it's an object that doesn't have 'raw', 'get', or dict-like methods,
            # we can try to get its string representation.
            chatbot_response = str(crew_result)
            print(f"DEBUG: Unexpected crew result type: {type(crew_result)}. Stringified: {chatbot_response}")


        # Ensure the response is always a string
        if not isinstance(chatbot_response, str):
            chatbot_response = str(chatbot_response)

        return ChatResponse(session_id=session_id, chatbot_response=chatbot_response)

    except Exception as e:
        import traceback
        print(f"Error during chat processing for session {session_id}: {e}")
        traceback.print_exc() # Print the full traceback
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")