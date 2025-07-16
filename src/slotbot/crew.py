# crew.py
import json
from crewai import Agent, Crew, Process, Task
from crewai.tools import BaseTool
from crewai.project import CrewBase, agent, crew, task
from crewai.tasks.conditional_task import ConditionalTask
from crewai.tasks.task_output import TaskOutput
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from .models import SessionState
from .models import UserInputParsed
from .tools.calendar_tools import BookAppointmentTool  # Import the actual tool



@CrewBase
class CalendarBookingCrew():
    """Calendar booking crew with conditional task execution"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def nlp_parser(self) -> Agent:
        return Agent(
            config=self.agents_config['nlp_parser'],
            verbose=True
        )

    @agent
    def session_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['session_manager'],
            verbose=True
        )

    # @agent
    # def calendar_manager(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['calendar_manager'],
    #         verbose=True,
    #         tools=[BookAppointmentTool()]
    #     )

    @agent
    def response_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['response_agent'],
            verbose=True
        )

    # # Condition function for the conditional task
    def is_information_missing(self, output: TaskOutput) -> bool:
        """
        Check if information is missing from the session validation.
        Returns True if information is missing (task should execute),
        False if all information is complete (task should be skipped).
        """
        try:
            # Parse the output from validate_session_state
            if hasattr(output, 'raw'):
                result = json.loads(output.raw)
            elif hasattr(output, 'pydantic'):
                result = output.pydantic.dict()
            else:
                # Fallback: assume information is missing if we can't parse
                return True
            
            # Check if required information status indicates missing data
            required_info_status = result.get('info_completeness_status', 'incomplete')
            next_action = result.get('next_action', 'collect_info')
            
            # Execute the task if information is incomplete or action is to collect info
            return (required_info_status == 'incomplete' or 
                    next_action == 'collect_info')
                    
        except Exception as e:
            # If we can't determine the status, assume information is missing
            print(f"Error checking information status: {e}")
            return True

    def is_information_complete(self, output: TaskOutput) -> bool:
        """
        Check if all information is complete for calendar operations.
        Returns True if information is complete (task should execute),
        False if information is missing (task should be skipped).
        """
        try:
            if hasattr(output, 'raw'):
                result = json.loads(output.raw)
            elif hasattr(output, 'pydantic'):
                result = output.pydantic.dict()
            else:
                return False
            
            required_info_status = result.get('required_info_status', 'incomplete')
            next_action = result.get('next_action', 'collect_info')
            
            # Execute the task if information is complete and action is to execute operation
            return (required_info_status == 'complete' and 
                    next_action == 'execute_operation')
                    
        except Exception as e:
            print(f"Error checking completion status: {e}")
            return False

    @task
    def parse_user_input(self) -> Task:
        return Task(
            config=self.tasks_config['parse_user_input'],
            output_pydantic=UserInputParsed,
        )

    @task
    def validate_session_state(self) -> Task:
        return Task(
            config=self.tasks_config['validate_session_state'],
            output_pydantic=SessionState  # Define this Pydantic model
        )

    # # CONDITIONAL TASK - Only executes if information is missing
    @task
    def collect_missing_information_task(self) -> ConditionalTask:
        return ConditionalTask(
            config=self.tasks_config['collect_missing_information'],
            condition=self.is_information_missing,  # This determines if task executes
            agent=self.response_agent()
        )

    
    # # CONDITIONAL TASK - Only executes if information is complete
    # @task
    # def book_appointment(self) -> ConditionalTask:
    #     return ConditionalTask(
    #         config=self.tasks_config['book_appointment'],
    #         condition=self.is_information_complete,  # This determines if task executes
    #         agent=self.calendar_manager()
    #     )

    @task
    def format_user_response(self) -> Task:
        return Task(
            config=self.tasks_config['format_user_response']
        )

    @crew
    def crew(self) -> Crew:
        """Creates the calendar booking crew with conditional tasks"""
        return Crew(
            agents=self.agents,
            tasks=[
                self.parse_user_input(),
                self.validate_session_state(),
                self.collect_missing_information_task(),  # Conditional
                # self.book_appointment(),   # Conditional
                self.format_user_response()
            ],
            process=Process.sequential,
            verbose=True,
        )
