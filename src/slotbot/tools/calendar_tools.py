from crewai.tools import BaseTool
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Assuming get_calendar_service is in a local module
# If it's not, you might need to adjust the import path
# For example, if it's in the same directory:
# from .oauth_client import get_calendar_service
# Or if it's in a subdirectory:
# from ..google_api.oauth_client import get_calendar_service
# Based on the provided file structure, it seems to be in a sibling directory 'google_api'
# Let's assume the import path is correct as provided in the original file.
from ..google_api.Oauth_client import get_calendar_service

from pydantic import BaseModel, Field


class BookAppointmentTool(BaseTool):
    name: str = "BookAppointmentTool"
    description: str = """
    Book an appointment in Google Calendar.
    
    Required parameters:
    - patient_name: Name of the patient
    - date: Date in YYYY-MM-DD format
    - time: Time in HH:MM format (24-hour)
    - duration: Duration in minutes (default: 60)
    - appointment_type: Type of appointment (e.g., 'Consultation', 'Follow-up')
    - patient_email: Patient's email address (optional)
    - notes: Additional notes for the appointment (optional)
    """
    
    def __init__(self):
        super().__init__()
        # The get_calendar_service function should handle authentication and return the service object
        self._calendar_service = get_calendar_service() # Changed to private attribute
    
    def _run(
        self,
        patient_name: str,
        date: str,
        time: str,
        duration: int = 60,
        appointment_type: str = "Consultation",
        patient_email: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        try:
            # Parse date and time
            # Google Calendar API expects ISO format with timezone.
            # We'll use UTC for simplicity here, assuming the input time is local and needs conversion or the timezone is handled by the service.
            # For a more robust solution, timezone handling would be crucial.
            start_datetime_naive = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            
            # Assuming the input time is local and we want to represent it in UTC for the API
            # A more robust solution would involve knowing the user's timezone.
            # For now, let's assume naive datetime and convert to UTC.
            
            # A better approach would be to get the timezone from the user or config.
            # For now, let's use a fixed timezone and convert to ISO format.
            # The test_calendar_access.py uses datetime.utcnow().isoformat() + 'Z'
            # Let's try to mimic that for the start time.
            
            # Let's try to parse the date and time and then format it for Google Calendar API
            # The API expects ISO 8601 format, e.g., '2023-10-27T10:00:00-07:00' or '2023-10-27T10:00:00Z' for UTC.
            
            # Let's try to combine date and time and then convert to ISO format with UTC 'Z'
            start_datetime_utc = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            
            # If the datetime object is naive, assume it's local and convert to UTC.
            # A more robust solution would involve timezone awareness.
            # For now, let's assume naive datetime and append 'Z' for UTC.
            start_iso = start_datetime_utc.isoformat() + 'Z'
            
            end_datetime_utc = start_datetime_utc + timedelta(minutes=duration)
            end_iso = end_datetime_utc.isoformat() + 'Z'

            # Create event
            event = {
                'summary': f"{appointment_type} - {patient_name}",
                'description': f"Patient: {patient_name}\nType: {appointment_type}",
                'start': {
                    'dateTime': start_iso,
                    'timeZone': 'UTC',  # Google Calendar API often prefers UTC or a specific timezone
                },
                'end': {
                    'dateTime': end_iso,
                    'timeZone': 'UTC',  # Google Calendar API often prefers UTC or a specific timezone
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 hours before
                        {'method': 'popup', 'minutes': 30},       # 30 minutes before
                    ],
                },
            }
            
            # Add attendees if email provided
            if patient_email:
                event['attendees'] = [
                    {'email': patient_email}
                ]
            
            # Add notes if provided
            if notes:
                event['description'] += f"\n\nNotes: {notes}"
            
            # Insert the event
            service = self._calendar_service # Use the private attribute
            event = service.events().insert(calendarId='primary', body=event).execute()
            
            return f"✅ Appointment booked successfully!\nEvent ID: {event.get('id', 'N/A')}\nLink: {event.get('htmlLink', 'N/A')}\nDate: {date} at {time}\nPatient: {patient_name}\nType: {appointment_type}"
            
        except HttpError as error:
            return f"❌ Error booking appointment: {error}"
        except ValueError as error:
            return f"❌ Invalid date/time format: {error}"
        except Exception as error:
            return f"❌ Unexpected error: {error}"
