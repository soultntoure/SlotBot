from crewai.tools import BaseTool
import json
import random

class DummyCalendarTool(BaseTool):
    name: str = "Dummy Calendar Tool"
    description: str = "Simulates calendar operations (booking, checking availability)"

    def _run(self, input: str) -> str:
        try:
            data = json.loads(input)
            intent = data.get("intent", "")
            user_id = data.get("user_id", "")
            time = data.get("datetime", "")

            if intent == "book":
                return self.book_appointment(user_id, time)
            elif intent == "check":
                return self.get_appointment(user_id)
            elif intent == "availability":
                return self.check_availability()
            else:
                return "❓ Unknown intent received."
        except Exception as e:
            return f"⚠️ Error processing input: {str(e)}"

    def book_appointment(self, user_id: str, datetime: str) -> str:
        return f"📅 Simulated: Appointment booked for user {user_id} at {datetime}"

    def get_appointment(self, user_id: str) -> str:
        return f"🔍 Simulated: User {user_id} has an appointment on Wednesday at 4 PM."

    def check_availability(self) -> str:
        slots = ["Monday 10am–12pm", "Tuesday 3pm–5pm", "Friday 1pm–3pm"]
        return f"✅ Simulated available slots: {random.choice(slots)}"