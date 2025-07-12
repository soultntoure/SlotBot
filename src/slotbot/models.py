# models.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ParsedInputOutput(BaseModel):
    intent: str
    entities: Dict[str, Any]
    user_info: Optional[Dict[str, str]]
    context: Optional[Dict[str, Any]]
    missing_info: List[str]
    confidence: float
    parsed_start_time: Optional[datetime]
    
    
class SessionStateOutput(BaseModel):
    identity_status: str  # known/unknown/partial
    required_info_status: str  # complete/incomplete
    missing_fields: List[str]
    next_action: str  # collect_info/execute_operation/clarify_intent
    prepared_data: Optional[Dict[str, Any]]
    parsed_start_time: Optional[datetime]