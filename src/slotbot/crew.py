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
from .tools.calendar_tools import BookAppointmentTool 


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
            tools=[BookAppointmentTool()]
        )

    @agent
    def response_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['response_agent'],
            verbose=True
        )

    def is_information_missing(self, validation_output: TaskOutput) -> bool:
        """
        Check if information is missing from the session validation.
        Returns True if information is missing (task should execute),
        False if all information is complete (task should be skipped).
        """
        print("--- DEBUGGING VALIDATION OUTPUT ---")
        print(f"Type of validation_output: {type(validation_output)}")
        print(f"Raw output: '{validation_output.raw}'")
        if hasattr(validation_output, 'pydantic') and validation_output.pydantic:
            print(f"Pydantic output: {validation_output.pydantic.dict()}")
        else:
            print("Pydantic output: None")
        print("---------------------------------")
        try:
            # Check if this is a None/empty output (from a skipped task)
            if not validation_output or not hasattr(validation_output, 'raw') or not validation_output.raw:
                print("[DEBUG] is_information_missing: Empty/None output detected, assuming info is complete")
                return False  # Don't collect info if previous task was skipped
            
            # Parse the validation output
            if hasattr(validation_output, 'raw') and validation_output.raw:
                result = json.loads(validation_output.raw)
            elif hasattr(validation_output, 'pydantic') and validation_output.pydantic:
                result = validation_output.pydantic.dict()
            else:
                print("[DEBUG] is_information_missing: No parseable output, defaulting to collect info")
                return True
            
            required_info_status = result.get('info_completeness_status', 'incomplete')
            next_action = result.get('next_action', 'collect_info')
            
            # Execute the task if information is incomplete or action is to collect info
            should_execute = (required_info_status == 'incomplete' or 
                             next_action == 'collect_info')
            
            print(f"[DEBUG] is_information_missing: {should_execute} (status: {required_info_status}, action: {next_action})")
            return should_execute
                    
        except Exception as e:
            print(f"Error checking information status: {e}")
            return True  # Default to collecting info if there's an error
        
    def is_information_complete(self, validation_output: TaskOutput) -> bool:
        """
        Check if information is complete for booking operations.
        Returns True if information is complete (task should execute),
        False if information is missing (task should be skipped).
        
        Key Logic: If validation_output is None/empty (from skipped collect_missing_information task),
        this means the info was complete, so we should proceed with booking.
        """
        print("--- DEBUGGING VALIDATION OUTPUT ---")
        print(f"Type of validation_output: {type(validation_output)}")
        print(f"Raw output: '{validation_output.raw}'")
        if hasattr(validation_output, 'pydantic') and validation_output.pydantic:
            print(f"Pydantic output: {validation_output.pydantic.dict()}")
        else:
            print("Pydantic output: None")
        print("---------------------------------")
        try:
            # CRITICAL: If this is a None/empty output from a skipped task,
            # it means collect_missing_information was skipped because info was complete
            if not validation_output or not hasattr(validation_output, 'raw') or not validation_output.raw:
                print("[DEBUG] is_information_complete: Empty/None output detected - info must be complete!")
                return True  # Proceed with booking since collect_missing_information was skipped
            
            # If we have actual validation output, parse it
            if hasattr(validation_output, 'raw') and validation_output.raw:
                result = json.loads(validation_output.raw)
            elif hasattr(validation_output, 'pydantic') and validation_output.pydantic:
                result = validation_output.pydantic.dict()
            else:
                print("[DEBUG] is_information_complete: No parseable output, assuming incomplete")
                return False
            
            required_info_status = result.get('info_completeness_status', 'incomplete')
            next_action = result.get('next_action', 'collect_info')
            
            # Execute the task if information is complete AND action is to execute operation
            should_execute = (required_info_status == 'complete' and 
                             next_action == 'execute_operation')
            
            print(f"[DEBUG] is_information_complete: {should_execute} (status: {required_info_status}, action: {next_action})")
            return should_execute
                    
        except Exception as e:
            print(f"Error checking information completeness: {e}")
            return False  # Default to not booking if there's an error

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
            condition=self.is_information_missing,
            agent=self.response_agent()
        )

    @task
    def book_appointment(self) -> ConditionalTask:
        return ConditionalTask(
            config=self.tasks_config['book_appointment'],
            condition=self.is_information_complete,
            agent=self.calendar_manager(),
            output_pydantic=BookAppointmentOutput
        )

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
                self.collect_missing_information(),
                self.book_appointment(),
                self.format_user_response()
            ],
            process=Process.sequential,
            verbose=True,
        )