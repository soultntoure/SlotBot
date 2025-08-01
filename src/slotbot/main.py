import warnings
from datetime import datetime

from slotbot.crew import CalendarBookingCrew
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the crew.
    """
    inputs = {
        'user_message': 'Hi clinician, I would like to book an appointment tuesday 5 pm, hamzakhaledlklk@gmail.com.',
        'current_date': datetime.now().isoformat()
    }
    
    try:
        result = CalendarBookingCrew().crew().kickoff(inputs=inputs)
        print(f"Crew execution completed successfully at {datetime.now()}.")
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
