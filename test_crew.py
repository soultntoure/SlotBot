#!/usr/bin/env python3
"""Test script to verify CrewAI fix"""

import sys
import traceback
from datetime import datetime

def test_crew_import():
    """Test if CrewAI can be imported"""
    try:
        from src.slotbot.crew import CalendarBookingCrew
        print("✅ CrewAI import successful")
        return True
    except Exception as e:
        print(f"❌ CrewAI import failed: {e}")
        traceback.print_exc()
        return False

def test_crew_instantiation():
    """Test if CrewAI can be instantiated"""
    try:
        from src.slotbot.crew import CalendarBookingCrew
        crew = CalendarBookingCrew()
        print("✅ CrewAI instantiation successful")
        return True
    except Exception as e:
        print(f"❌ CrewAI instantiation failed: {e}")
        traceback.print_exc()
        return False

def test_crew_kickoff():
    """Test if CrewAI kickoff works"""
    try:
        from src.slotbot.crew import CalendarBookingCrew
        crew = CalendarBookingCrew()
        
        inputs = {
            'user_message': 'Hello, I want to book an appointment',
            'current_date': datetime.now().isoformat()
        }
        
        result = crew.crew().kickoff(inputs=inputs)
        print(f"✅ CrewAI kickoff successful")
        print(f"Result type: {type(result)}")
        print(f"Result attributes: {dir(result)}")
        
        # Try to access the result
        if hasattr(result, 'raw'):
            print(f"Result.raw: {result.raw}")
        elif hasattr(result, 'tasks_output'):
            print(f"Tasks output length: {len(result.tasks_output)}")
            if result.tasks_output:
                last_task = result.tasks_output[-1]
                print(f"Last task type: {type(last_task)}")
                if hasattr(last_task, 'raw'):
                    print(f"Last task raw: {last_task.raw}")
        
        return True
    except Exception as e:
        print(f"❌ CrewAI kickoff failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing CrewAI fixes...")
    print("=" * 50)
    
    tests = [
        test_crew_import,
        test_crew_instantiation,
        test_crew_kickoff
    ]
    
    results = []
    for test in tests:
        print(f"\nRunning {test.__name__}...")
        results.append(test())
    
    print("\n" + "=" * 50)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("🎉 All tests passed! Your CrewAI should work with FastAPI now.")
    else:
        print("❌ Some tests failed. Try the version downgrade approach.")