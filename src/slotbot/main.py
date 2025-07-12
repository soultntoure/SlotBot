import warnings
from datetime import datetime

from slotbot.crew import CalendarBookingCrew
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the crew.
    """
    inputs = {
        'user_message': 'I want to book tomorrow at 6pm. My ID is 12111.'
    }
    
    try:
        result = CalendarBookingCrew().crew().kickoff(inputs=inputs)
        print(f"Crew execution completed successfully at {datetime.now()}.")
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
