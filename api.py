import os
import django
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

# 1. SETUP DJANGO INSIDE FASTAPI
# Detect the correct Django settings module depending on repo layout.
root = Path(__file__).resolve().parent
if (root / 'hackathon_core' / 'settings.py').exists():
    # layout: repo_root/hackathon_core/settings.py
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackathon_core.settings')
elif (root / 'hackathon_core' / 'hackathon_core' / 'settings.py').exists():
    # layout: repo_root/hackathon_core/hackathon_core/settings.py
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackathon_core.hackathon_core.settings')
else:
    # fallback to original value
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackathon_core.settings')
django.setup()

from core_db.models import AgentLog 
from agents import praxis_crew
import json
import requests
from fastapi import Query
import pdm

app = FastAPI()

@app.post("/api/run_agent")
async def run_agent(background_tasks: BackgroundTasks):
    background_tasks.add_task(praxis_crew.kickoff)
    return {"status": "Agents Dispatched! Check Django Admin."}

@app.get("/")
def read_root():
    return {"Hello": "PraxisGuard AI System is Online"}


@app.post("/api/forward_to_n8n")
async def forward_to_n8n():
    """Read latest CSV row and forward JSON to configured N8N webhook URL (via env).
    The webhook URL should be set in `N8N_WEBHOOK_URL` environment variable.
    """
    n8n_url = os.getenv('N8N_WEBHOOK_URL')
    if not n8n_url:
        return {"error": "N8N webhook not configured (set N8N_WEBHOOK_URL)."}
    try:
        import pandas as _pd
        if not os.path.exists('live_sensor_stream.csv'):
            return {"error": "no_sensor_data"}
        df = _pd.read_csv('live_sensor_stream.csv')
        if df.empty:
            return {"error": "no_sensor_data"}
        latest = df.tail(1).iloc[0].to_dict()
        payload = {"event": "sensor_reading", "data": latest}
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(n8n_url, data=json.dumps(payload), headers=headers, timeout=5)
        return {"status": "forwarded", "n8n_status": resp.status_code, "n8n_text": resp.text}
    except Exception as e:
        return {"error": str(e)}


@app.get('/api/compute_pof')
def compute_pof_endpoint(machine_id: str = Query(...), window: int = 5):
    """Compute PoF for a given machine by reading recent CSV data.

    Query params:
      - machine_id: ID of machine (required)
      - window: how many recent rows to use
    """
    try:
        result = pdm.compute_pof_for_machine(machine_id, window=window)
        return result
    except Exception as e:
        return {"error": str(e)}