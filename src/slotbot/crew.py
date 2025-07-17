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

    def _get_next_action(self, validation_output: TaskOutput) -> str:
        """Helper function to safely extract next_action from task output."""
        print("\n--- [DEBUG] In _get_next_action ---")
        print(f"Received validation_output type: {type(validation_output)}")
        
        if not validation_output:
            print("Validation output is None. Returning 'default'.")
            return "default"
            
        raw_output = getattr(validation_output, 'raw', None)
        pydantic_output = getattr(validation_output, 'pydantic', None)
        
        print(f"Raw output: '{raw_output}'")
        print(f"Pydantic output: {pydantic_output}")

        if not raw_output:
            print("Raw output is empty or None. Returning 'default'.")
            return "default"

        try:
            data = json.loads(raw_output)
            next_action = data.get('next_action', 'default')
            print(f"Successfully parsed next_action: '{next_action}'")
            return next_action
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError parsing raw output: {e}. Raw content was: '{raw_output}'")
            return "default"
        except Exception as e:
            print(f"An unexpected error occurred in _get_next_action: {e}")
            return "default"

    def should_collect_info(self, validation_output: TaskOutput) -> bool:
        """Condition to run the 'collect_missing_information' task."""
        next_action = self._get_next_action(validation_output)
        print(f"[DEBUG] Condition for 'collect_info': next_action is '{next_action}'")
        return next_action == 'collect_info'

    def should_check_availability(self, validation_output: TaskOutput) -> bool:
        """Condition to run the 'check_availability' task."""
        next_action = self._get_next_action(validation_output)
        print(f"[DEBUG] Condition for 'check_availability': next_action is '{next_action}'")
        return next_action == 'check_availability'

    def should_book_appointment(self, validation_output: TaskOutput) -> bool:
        """Condition to run the 'book_appointment' task."""
        next_action = self._get_next_action(validation_output)
        print(f"[DEBUG] Condition for 'book_appointment': next_action is '{next_action}'")
        return next_action == 'execute_operation'

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
            output_pydantic=SessionState
        )

    @task
    def collect_missing_information(self) -> ConditionalTask:
        return ConditionalTask(
            config=self.tasks_config['collect_missing_information'],
            condition=self.should_collect_info,
            agent=self.response_agent(),
            context=[self.validate_session_state()]
        )

    @task
    def check_availability(self) -> ConditionalTask:
        return ConditionalTask(
            config=self.tasks_config['check_availability'],
            condition=self.should_check_availability,
            agent=self.calendar_manager(),
            context=[self.validate_session_state()]
        )

    @task
    def book_appointment(self) -> ConditionalTask:
        return ConditionalTask(
            config=self.tasks_config['book_appointment'],
            condition=self.should_book_appointment,
            agent=self.calendar_manager(),
            output_pydantic=BookAppointmentOutput,
            context=[self.validate_session_state()]
        )

    @task
    def format_user_response(self) -> Task:
        return Task(
            config=self.tasks_config['format_user_response'],
            context=[
                self.validate_session_state(),
                self.collect_missing_information(),
                self.check_availability(),
                self.book_appointment()
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
                self.check_availability(),
                self.book_appointment(),
                self.format_user_response()
            ],
            process=Process.sequential,
            verbose=True,
        )
