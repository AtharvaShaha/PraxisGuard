# PraxisGuard — Local Dev Guide

This repository contains a small Django app, a FastAPI endpoint, a Streamlit dashboard, and a simple sensor simulator.

Quick features
- Live sensor simulator writes `live_sensor_stream.csv`.
- Streamlit dashboard visualizes `vibration` and `temperature` in real time.
- FastAPI endpoint `/api/run_agent` triggers the agent crew (saves `AgentLog`).
- Django admin shows saved `AgentLog` entries.

Running locally (Windows PowerShell)
1. Install dependencies:
```powershell
cd "D:\\Desktop\\Mumbai Hacks"
python -m pip install -r requirements.txt
```

2. Create `.env` (copy `.env.example` and fill real keys):
```powershell
copy .env.example .env
notepad .env
```

3. Run Django migrations and (optionally) create superuser:
```powershell
cd "D:\\Desktop\\Mumbai Hacks\\hackathon_core"
python manage.py migrate
python manage.py createsuperuser
cd ..
```

4. Start services (either individually or use the provided runner):
Individual commands (in separate terminals):
```powershell
# Start sensor simulator
python "D:\\Desktop\\Mumbai Hacks\\simulate_live_server.py"

# Start FastAPI (uvicorn)
python -m uvicorn hackathon_core.run_api:app --reload

# Start Django admin (on a different port if uvicorn uses 8000)
cd "D:\\Desktop\\Mumbai Hacks\\hackathon_core"
python manage.py runserver 8001

# Start Streamlit dashboard
python -m streamlit run "D:\\Desktop\\Mumbai Hacks\\dashboard.py"
```

Or use the one-command runner:
```powershell
cd "D:\\Desktop\\Mumbai Hacks"
.\\start_dev.ps1
```

Open these UIs in your browser:
- Streamlit dashboard: http://localhost:8501
- FastAPI (docs): http://127.0.0.1:8000/docs
- Django Admin: http://127.0.0.1:8001/admin

Pushing to GitHub
1. Create a repository on GitHub (either via website or `gh` CLI).

2a. If you have `gh` installed, from project root:
```powershell
gh repo create <username>/<repo-name> --public --source=. --remote=origin --push
```

2b. Otherwise, manual Git commands:
```powershell
cd "D:\\Desktop\\Mumbai Hacks"
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<username>/<repo-name>.git
git push -u origin main
```

Notes
- Make sure `.env` and `db.sqlite3` are not pushed (they are in `.gitignore`).
- If you use HTTPS push and Git prompts for username/password, create a GitHub Personal Access Token and use it as the password.
- If you prefer SSH, add your SSH key in GitHub account settings and use the SSH remote URL.

Need me to push?
- I can't push from here without your GitHub credentials/authorization. If you want, I can generate the exact commands and, if you have the `gh` CLI installed and authenticated, I can provide the single `gh repo create ...` command to run.
