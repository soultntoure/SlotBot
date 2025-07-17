from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    session_id: str
    user_message: str

class ChatResponse(BaseModel):
    session_id: str
    chatbot_response: str

# We might also want to expose internal models if needed by the frontend for state management
# For now, we'll keep it simple with just request/response for the chat endpoint.
# If the frontend needs to know the next action or missing info, we can add those fields here.

# Example of exposing internal state if needed:
# class SessionStateAPI(BaseModel):
#     identity_status: str
#     info_completeness_status: str
#     missing_info: List[str]
#     next_action: str

# class UserInputParsedAPI(BaseModel):
#     intent: str
#     patient_email: Optional[EmailStr] = None
#     start_time: Optional[datetime] = None
#     end_time: Optional[datetime] = None
#     temporal_expression: Optional[str] = None
#     missing_info: List[str] = []
