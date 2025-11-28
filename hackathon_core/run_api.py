from pathlib import Path
import sys

# Ensure project root is on sys.path so imports like `import api` work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Add the inner Django project package directory first so imports like
# `import hackathon_core.settings` resolve to the inner package.
INNER = PROJECT_ROOT / 'hackathon_core'
if INNER.exists() and str(INNER) not in sys.path:
    sys.path.insert(0, str(INNER))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the FastAPI `app` defined at repository root `api.py`
from api import app  # exposes `app` variable for uvicorn
