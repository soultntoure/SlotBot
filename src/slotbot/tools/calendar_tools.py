from crewai.tools import BaseTool
import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ..google_api.Oauth_client import get_calendar_service
from pydantic import BaseModel, Field


class CheckAvailabilityArgs(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    time: str = Field(..., description="Time in HH:MM format (24-hour)")
    duration: int = Field(60, description="Duration in minutes to check (default: 60)")


class BookAppointmentArgs(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    time: str = Field(..., description="Time in HH:MM format (24-hour)")
    patient_email: str = Field(..., description="Patient's email address")
    duration: int = Field(60, description="Duration in minutes (default: 60)")
    notes: Optional[str] = Field("General appointment", description="Additional notes for the appointment (optional)")

class BookAppointmentTool(BaseTool):
    name: str = "BookAppointmentTool"
    description: str = """
    Book an appointment in Google Calendar.
    
    Required parameters:
    - date: Date in YYYY-MM-DD format
    - time: Time in HH:MM format (24-hour)
    - duration: Duration in minutes (default: 60)
    - patient_email: Patient's email address
    
    Optional parameters:
    - notes: Additional notes for the appointment
    """
    args_schema: type[BaseModel] = BookAppointmentArgs

    def _run(self, date: str, time: str, patient_email: str, duration: int, notes: Optional[str] = None) -> str:
        """
        Books an appointment in Google Calendar.
        """
        try:
            service = get_calendar_service()

            # Combine date and time strings and parse into datetime objects
            start_datetime_str = f"{date}T{time}"
            start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%dT%H:%M")
            end_datetime = start_datetime + timedelta(minutes=duration)

            # Format datetimes for Google Calendar API (ISO 8601 format)
            # Assuming a default timezone, e.g., 'Asia/Singapore' based on environment details.
            # This might need to be made configurable if users are in different timezones.
            timezone = 'Asia/Singapore' 
            start_iso = start_datetime.isoformat()
            end_iso = end_datetime.isoformat()

            event_body = {
                'summary': 'Appointment', # Generic summary as appointment_type is removed
                'description': notes if notes else 'General appointment',
                'start': {
                    'dateTime': start_iso,
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_iso,
                    'timeZone': timezone,
                },
                'attendees': [
                    {'email': patient_email},
                ],
            }

            created_event = service.events().insert(calendarId='primary', body=event_body).execute()
            
            return f"Appointment booked successfully! You can view it at: {created_event.get('htmlLink')}"

        except HttpError as error:
            return f"An error occurred while booking the appointment: {error}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"


class CheckAvailabilityTool(BaseTool):
    name: str = "CheckAvailabilityTool"
    description: str = """
    Check if a specific time slot is available in the Google Calendar.

    Required parameters:
    - date: Date in YYYY-MM-DD format
    - time: Time in HH:MM format (24-hour)
    
    Optional parameters:
    - duration: Duration in minutes to check (default: 60)
    """
    args_schema: type[BaseModel] = CheckAvailabilityArgs

    def _run(self, date: str, time: str, duration: int = 60) -> str:
        """
        Checks for conflicting events in the Google Calendar for a given time slot using the freebusy API.
        """
        try:
            service = get_calendar_service()

            # Define the timezone for Singapore (UTC+8)
            sgt = timezone(timedelta(hours=8))

            # Combine date and time and parse into a naive datetime object
            start_datetime_str = f"{date}T{time}"
            naive_start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%dT%H:%M")

            # Make the datetime object timezone-aware using the Singapore timezone
            start_datetime_aware = naive_start_datetime.replace(tzinfo=sgt)
            end_datetime_aware = start_datetime_aware + timedelta(minutes=duration)

            # Format for Google Calendar API (RFC3339 format)
            time_min = start_datetime_aware.isoformat()
            time_max = end_datetime_aware.isoformat()

            freebusy_query = {
                "timeMin": time_min,
                "timeMax": time_max,
                "items": [{"id": "primary"}]
            }

            freebusy_result = service.freebusy().query(body=freebusy_query).execute()
            busy_slots = freebusy_result.get('calendars', {}).get('primary', {}).get('busy', [])

            if not busy_slots:
                return json.dumps({"status": "free", "message": "The time slot is available."})
            else:
                return json.dumps({"status": "busy", "message": "The time slot is not available."})

        except Exception as e:
            return json.dumps({"status": "error", "message": f"An unexpected error occurred: {e}"})
