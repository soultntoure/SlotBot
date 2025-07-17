from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from src.slotbot.crew import CalendarBookingCrew
from datetime import datetime
import uuid

# In-memory store for session state (for demonstration)
# In a production app, this would be a database or cache
session_store: Dict[str, Any] = {}

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define Pydantic models directly here or import from api/schemas.py
class ChatRequest(BaseModel):
    session_id: str
    user_message: str

class ChatResponse(BaseModel):
    session_id: str
    chatbot_response: str

# Import routes
from api.routes.chat import router as chat_router
from api.routes.health import router as health_router

app.include_router(chat_router)
app.include_router(health_router)

# Add a root endpoint for basic check
@app.get("/")
async def read_root():
    return {"message": "SlotBot API is running"}
