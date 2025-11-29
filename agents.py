import pandas as pd
import os
import django
from dotenv import load_dotenv

# Optional, third-party AI/agent libs may not be installed in lightweight envs.
# Wrap imports with fallbacks so the repository can be inspected/run without them.
load_dotenv()

try:
    from crewai import Agent, Task, Crew
    from crewai_tools import tool
except Exception:
    # Minimal stubs so modules import during development / CI without the real libs.
    def tool(name):
        def decorator(f):
            return f
        return decorator

    class Agent:
        def __init__(self, role=None, goal=None, backstory=None, tools=None, llm=None, verbose=False):
            self.role = role
            self.goal = goal
            self.tools = tools or []
            self.llm = llm

    class Task:
        def __init__(self, description=None, expected_output=None, agent=None, context=None):
            self.description = description
            self.expected_output = expected_output
            self.agent = agent
            self.context = context or []

    class Crew:
        def __init__(self, agents=None, tasks=None):
            self.agents = agents or []
            self.tasks = tasks or []
            # provide a minimal kickoff implementation on the stub so callers
            # like the FastAPI background task can call `praxis_crew.kickoff()`
            # without raising AttributeError.
            def _stub_kickoff():
                # very small orchestration: run sensor tool, and if critical,
                # run save_to_db_tool for the machine
                try:
                    # find sensor tool on first agent that has one
                    sensor_output = None
                    for agent in self.agents:
                        for t in getattr(agent, 'tools', []) or []:
                            try:
                                # call tool assuming signature (machine_id)
                                sensor_output = t('MAC-101')
                            except TypeError:
                                # try without args
                                try:
                                    sensor_output = t()
                                except Exception:
                                    sensor_output = None
                            if sensor_output:
                                break
                        if sensor_output:
                            break

                    # parse sensor output for CRITICAL
                    is_critical = False
                    if isinstance(sensor_output, str) and 'CRITICAL' in sensor_output:
                        is_critical = True

                    if is_critical:
                        # call save tool
                        for agent in self.agents:
                            for t in getattr(agent, 'tools', []) or []:
                                # identify save_to_db_tool by name or behavior
                                try:
                                    res = t('MAC-101', 'CRITICAL', 0.95, 'Auto-detected critical readings')
                                    # we only need to save once
                                    return res
                                except TypeError:
                                    continue
                    return sensor_output
                except Exception:
                    return None

            self.kickoff = _stub_kickoff

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    # Only use real LLM if GOOGLE_API_KEY is set
    has_real_llm = bool(os.getenv("GOOGLE_API_KEY"))
except Exception:
    # Fallback LLM stub (non-functional, prevents import errors)
    has_real_llm = False

# Set up Django (required for DB model import)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackathon_core.settings')
django.setup()
from core_db.models import AgentLog

# Configure a real or stub LLM
if has_real_llm:
    gemini_llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        verbose=True,
        temperature=0.5,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
else:
    class _StubLLM:
        def __init__(self, *a, **kw):
            pass

        def generate(self, *a, **kw):
            return "[LLM stub]"

    gemini_llm = _StubLLM()

@tool("Check Sensors")
def read_sensor_data_tool(machine_id: str):
    """Reads the latest sensor data from the CSV file."""
    try:
        df = pd.read_csv('live_sensor_stream.csv').tail(5)
        latest = df.iloc[-1]
        vibration = latest['vibration']
        temp = latest['temperature']
        status = "Healthy"
        if vibration > 80 or temp > 90:
            status = "CRITICAL"
        return f"Current Readings -> Vib: {vibration:.1f}, Temp: {temp:.1f}. Status: {status}"
    except Exception:
        return "Error reading sensors."

@tool("Save Actions")
def save_to_db_tool(machine_id: str, status: str, risk_score: float, recommendation: str):
    """Saves to Django DB."""
    AgentLog.objects.create(machine_id=machine_id, status=status, risk_score=risk_score, recommendation=recommendation)
    return "Saved to DB."

sensor_agent = Agent(role='Sensor Analyst', goal='Report CRITICAL status.', backstory='You watch data.', tools=[read_sensor_data_tool], llm=gemini_llm, verbose=True)
logistics_agent = Agent(role='Logistics Manager', goal='Save log if CRITICAL.', backstory='You fix things.', tools=[save_to_db_tool], llm=gemini_llm, verbose=True)

sensor_task = Task(description='Check sensor data for MAC-101.', expected_output='Status Report.', agent=sensor_agent)
logistics_task = Task(description='If Critical, save to DB.', expected_output='Saved.', agent=logistics_agent, context=[sensor_task])

praxis_crew = Crew(agents=[sensor_agent, logistics_agent], tasks=[sensor_task, logistics_task])