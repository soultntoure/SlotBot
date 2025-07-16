# models.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# src/slotbot/tools/models.py

from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional, List
from datetime import datetime

class UserInputParsed(BaseModel):
    """
    Analyzes and structures a user's query about calendar appointments.
    It captures the user's intent and extracts relevant details for any
    downstream processing, whether it's booking, canceling, or checking availability.
    """

    intent: Literal['book', 'cancel', 'check_availability', 'general_query'] = Field(
        ...,
        description="The user's primary goal. Is it to book, cancel, check for open slots, or something else?"
    )

    patient_email: Optional[EmailStr] = Field(
        None,
        description="The patient's email address, if provided. This is the primary identifier for booking/canceling."
    )

    start_time: Optional[datetime] = Field(
        None,
        description="The specific start time for a 'book' or 'cancel' request, converted to an absolute ISO 8601 format."
    )

    end_time: Optional[datetime] = Field(
        None,
        description="The specific end time for a 'book' or 'cancel' request, in ISO 8601 format. Should be calculated from start_time if not specified with a duration of 60 minutes."
    )
    
    temporal_expression: Optional[str] = Field(
        None,
        description="If the user asks a general question about time (e.g., 'next week in the evening', 'sometime on Friday'), store that raw text here. This is used for 'check_availability' intents."
    )

    missing_info: List[str] = Field(
        default_factory=list,
        description="A list of critical information that is missing to fulfill the user's specific intent (e.g., 'patient_email' is missing for a 'book' intent)."
    )
    
    
class SessionState(BaseModel):
    """
    Provides a structured report on the current state of the user interaction,
    determining if identity is known and if the request is complete enough to proceed.
    """
    identity_status: Literal['known', 'unknown'] = Field(
        ...,
        description="Indicates if the user's identity (email) has been captured."
    )
    info_completeness_status: Literal['complete', 'incomplete'] = Field(
        ...,
        description="Indicates if all necessary data for the user's intent (e.g., date/time for booking) has been provided."
    )
    missing_info: List[str]
    next_action: Literal['collect_info', 'execute_operation']