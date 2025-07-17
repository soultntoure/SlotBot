# Updated crew.py with None handling logic

import json
from crewai import Agent, Crew, Process, Task
from crewai.tools import BaseTool
from crewai.project import CrewBase, agent, crew, task
from crewai.tasks.conditional_task import ConditionalTask
from crewai.tasks.task_output import TaskOutput
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from .models import SessionState
from .models import BookAppointmentOutput
from .models import UserInputParsed
from .tools.calendar_tools import BookAppointmentTool, CheckAvailabilityTool 


@CrewBase
class CalendarBookingCrew():
    """Calendar booking crew with conditional task execution"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        self._session_state_output = None

    def _save_session_state(self, output: TaskOutput):
        """Callback function to save the output of the validation task."""
        print(f"\n--- [CALLBACK] Saving session state ---\nRaw output: {output.raw}\n------------------------------------")
        self._session_state_output = output

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

    @agent
    def calendar_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['calendar_manager'],
            verbose=True,
            tools=[BookAppointmentTool(), CheckAvailabilityTool()]
        )

    @agent
    def response_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['response_agent'],
            verbose=True
        )

    def _get_next_action(self) -> str:
        """Helper function to safely extract next_action from the stored session state."""
        print("\n--- [DEBUG] In _get_next_action ---")
        
        if not self._session_state_output:
            print("Stored session state is None. Returning 'default'.")
            return "default"
            
        raw_output = getattr(self._session_state_output, 'raw', None)
        print(f"Reading from stored raw output: '{raw_output}'")

        if not raw_output:
            print("Stored raw output is empty or None. Returning 'default'.")
            return "default"

        try:
            data = json.loads(raw_output)
            next_action = data.get('next_action', 'default')
            print(f"Successfully parsed next_action from stored state: '{next_action}'")
            return next_action
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError parsing stored raw output: {e}. Raw content was: '{raw_output}'")
            return "default"
        except Exception as e:
            print(f"An unexpected error occurred in _get_next_action: {e}")
            return "default"

    def should_collect_info(self, validation_output: TaskOutput) -> bool:
        """Condition to run the 'collect_missing_information' task."""
        # This function now ignores the validation_output and uses the stored state.
        next_action = self._get_next_action()
        print(f"[DEBUG] Condition for 'collect_info': next_action is '{next_action}'")
        return next_action == 'collect_info'

    def should_execute_action(self, validation_output: TaskOutput) -> bool:
        """Condition to run the main action task."""
        # This function now ignores the validation_output and uses the stored state.
        next_action = self._get_next_action()
        print(f"[DEBUG] Condition for 'execute_action': next_action is '{next_action}'")
        return next_action in ['check_availability', 'execute_operation']

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
            output_pydantic=SessionState,
            callback=self._save_session_state
        )

    @task
    def collect_missing_information(self) -> ConditionalTask:
        return ConditionalTask(
            config=self.tasks_config['collect_missing_information'],
            condition=self.should_collect_info,
            agent=self.response_agent()
        )

    @task
    def execute_calendar_action(self) -> ConditionalTask:
        return ConditionalTask(
            config=self.tasks_config['execute_calendar_action'],
            condition=self.should_execute_action,
            agent=self.calendar_manager(),
            context=[self.parse_user_input(), self.validate_session_state()]
        )

    @task
    def format_user_response(self) -> Task:
        return Task(
            config=self.tasks_config['format_user_response'],
            context=[
                self.collect_missing_information(),
                self.execute_calendar_action()
            ]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the calendar booking crew with conditional tasks"""
        return Crew(
            agents=self.agents,
            tasks=[
                self.parse_user_input(),
                self.validate_session_state(),
                self.collect_missing_information(),
                self.execute_calendar_action(),
                self.format_user_response()
            ],
            process=Process.sequential,
            verbose=True,
        )
