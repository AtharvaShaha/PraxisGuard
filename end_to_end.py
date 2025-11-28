"""End-to-end sample that writes a critical sensor reading, calls the API,
and prints the latest AgentLog entry from the Django DB.

Run from project root after installing requirements and starting the API:
  python end_to_end.py
"""
import os
import time
import requests
import django
from pathlib import Path

# Ensure Django settings are available. Detect nested layout like other entrypoints.
root = Path(__file__).resolve().parent
# Try to locate the Django settings file. If the repository uses a nested
# layout (hackathon_core/hackathon_core/settings.py), load that file as a
# module and tell Django to use it; otherwise rely on the simple module name.
settings_path = None
if (root / 'hackathon_core' / 'settings.py').exists():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackathon_core.settings')
    settings_path = root / 'hackathon_core' / 'settings.py'
elif (root / 'hackathon_core' / 'hackathon_core' / 'settings.py').exists():
    # Load the inner settings.py as an explicit module to avoid package-name
    # conflicts (top-level folder may not be a Python package).
    settings_path = root / 'hackathon_core' / 'hackathon_core' / 'settings.py'
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackathon_core.settings')

# Ensure import paths include the top-level `hackathon_core` directory so
# packages like `core_db` import correctly when run from repo root.
PROJECT_ROOT = root
TOP_LEVEL = PROJECT_ROOT / 'hackathon_core'
import sys
if TOP_LEVEL.exists() and str(TOP_LEVEL) not in sys.path:
    sys.path.insert(0, str(TOP_LEVEL))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# If we found a nested settings.py path and the module name would be ambiguous,
# load it directly into sys.modules under a stable name and set DJANGO_SETTINGS_MODULE
if settings_path and 'hackathon_core' in str(settings_path) and settings_path.exists():
    # When nested, top-level path-importing can be ambiguous; register as 'project_settings'
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location('project_settings', str(settings_path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules['project_settings'] = module
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_settings')
    except Exception:
        # fallback to default env var; django.setup() will attempt normal import
        pass

django.setup()
from core_db.models import AgentLog
import pandas as pd


def write_critical_reading(path='live_sensor_stream.csv'):
    df = pd.DataFrame([{
        'timestamp': pd.Timestamp.now(),
        'machine_id': 'MAC-101',
        'vibration': 85.0,
        'temperature': 95.0
    }])
    # append or create
    if os.path.exists(path):
        df.to_csv(path, mode='a', header=False, index=False)
    else:
        df.to_csv(path, index=False)


def call_api():
    try:
        resp = requests.post('http://127.0.0.1:8000/api/run_agent')
        print('API response:', resp.status_code, resp.text)
    except Exception as e:
        print('Failed to call API:', e)


def print_latest_log():
    try:
        last = AgentLog.objects.order_by('-timestamp').first()
        if last:
            print('Latest AgentLog ->', last.machine_id, last.status, last.risk_score, last.recommendation, last.timestamp)
        else:
            print('No AgentLog entries yet.')
    except Exception as e:
        print('Error reading AgentLog:', e)


def main():
    write_critical_reading()
    print('Wrote critical reading, calling API...')
    call_api()
    print('Waiting 3s for background task...')
    time.sleep(3)
    print_latest_log()


if __name__ == '__main__':
    main()
