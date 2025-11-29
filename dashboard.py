import streamlit as st
import pandas as pd
import requests
import time
import os
import sys
import django
from dotenv import load_dotenv

load_dotenv()

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hackathon_core'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackathon_core.settings')
django.setup()

from core_db.models import SensorReading

# Page config and styling
st.set_page_config(page_title="PraxisGuard Dashboard", layout="wide")
st.markdown(
    """
    <style>
    /* background */
    .stApp {
        background: linear-gradient(180deg, #0f172a 0%, #071229 100%);
        color: #e6eef8;
        font-family: 'Inter', sans-serif;
    }
    /* card like panels */
    .card { background: rgba(255,255,255,0.03); padding: 18px; border-radius: 8px; }
    .small { font-size: 0.9rem; color: #bcd3f5 }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛡️ PraxisGuard: Hospital Defense")

# Utility functions
def load_data_from_db(limit=1000):
    """Load sensor data from MySQL database"""
    try:
        readings = SensorReading.objects.all().order_by('-timestamp')[:limit]
        if not readings:
            return pd.DataFrame(columns=["timestamp", "machine_id", "vibration", "temperature"])
        
        data = [{
            'timestamp': r.timestamp,
            'machine_id': r.machine_id,
            'vibration': r.vibration,
            'temperature': r.temperature
        } for r in readings]
        
        df = pd.DataFrame(data)
        df = df.sort_values('timestamp', ascending=True).reset_index(drop=True)
        return df
    except Exception as e:
        print(f"Error loading data from DB: {e}")
        return pd.DataFrame(columns=["timestamp", "machine_id", "vibration", "temperature"])

def machines_from_df(df):
    if df.empty:
        return []
    return sorted(df['machine_id'].unique())

def compute_pof(vibration, temperature, vib_thresh=80.0, temp_thresh=90.0):
    # Simple heuristic PoF: normalized exceedance with soft cap
    vib_score = max(0.0, (vibration - vib_thresh) / (200 - vib_thresh))
    temp_score = max(0.0, (temperature - temp_thresh) / (200 - temp_thresh))
    pof = min(1.0, 0.7 * vib_score + 0.3 * temp_score)
    return round(pof, 3)


df = load_data_from_db()

col_left, col_right = st.columns([3, 1])

with col_right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("Controls")
    vib_threshold = st.number_input("Vibration alert threshold", value=80.0, step=0.1)
    temp_threshold = st.number_input("Temperature alert threshold", value=90.0, step=0.1)
    auto_trigger = st.checkbox("Auto-trigger AI when PoF > threshold", value=False)
    n8n_url = st.text_input("n8n Webhook URL (optional)", value=os.getenv("N8N_WEBHOOK_URL", ""))
    if st.button("🚨 TRIGGER AI TEAM"):
        try:
            requests.post("http://127.0.0.1:8000/api/run_agent", timeout=3)
            st.success("Agents Dispatched! Check Django Admin.")
        except Exception as e:
            st.error(f"Failed to contact API: {e}")

    if st.button("Forward Latest to n8n"):
        try:
            resp = requests.post("http://127.0.0.1:8000/api/forward_to_n8n", timeout=5)
            if resp.status_code == 200:
                st.success("Forwarded to n8n")
            else:
                st.error(f"n8n forward failed: {resp.status_code} {resp.text}")
        except Exception as e:
            st.error(f"Failed to forward: {e}")

    if st.button("Simulate CRITICAL now"):
        # append a critical reading for demo
        demo = pd.DataFrame([{
            'timestamp': pd.Timestamp.now(),
            'machine_id': 'MAC-101',
            'vibration': vib_threshold + 30,
            'temperature': temp_threshold + 10
        }])
        demo.to_csv("live_sensor_stream.csv", mode='a', header=not os.path.exists("live_sensor_stream.csv"), index=False)
        st.success("Simulated critical reading appended.")

    st.markdown('</div>', unsafe_allow_html=True)

with col_left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.header("Live Sensor Stream & Machine Risk")
    if df.empty:
        st.info("Waiting for data stream...")
    else:
        # Show overview table of machines with PoF
        machines = machines_from_df(df)
        rows = []
        for m in machines:
            sub = df[df['machine_id'] == m].tail(5)
            latest = sub.iloc[-1]
            pof = compute_pof(latest['vibration'], latest['temperature'], vib_threshold, temp_threshold)
            rows.append({
                'machine_id': m,
                'last_seen': latest['timestamp'],
                'vibration': round(latest['vibration'],1),
                'temperature': round(latest['temperature'],1),
                'PoF': pof,
            })
        overview = pd.DataFrame(rows)
        st.dataframe(overview.sort_values('PoF', ascending=False).reset_index(drop=True))

        sel = st.selectbox("Select machine to inspect", options=machines)
        if sel:
                sel_df = df[df['machine_id']==sel].sort_values('timestamp')
                st.line_chart(sel_df.set_index('timestamp')[['vibration','temperature']])
                st.subheader("Recent readings")
                st.table(sel_df.tail(10).reset_index(drop=True))
                # compute latest PoF via API (preferred) with local fallback
                latest = sel_df.tail(1).iloc[0]
                pof = None
                try:
                    resp = requests.get('http://127.0.0.1:8000/api/compute_pof', params={'machine_id': sel, 'window': 5}, timeout=2)
                    if resp.status_code == 200:
                        j = resp.json()
                        if 'pof' in j:
                            pof = j['pof']
                except Exception:
                    pof = None

                if pof is None:
                    # fallback to local compute
                    pof = compute_pof(latest['vibration'], latest['temperature'], vib_threshold, temp_threshold)

                st.markdown(f"**Computed PoF:** {pof}")
                if pof > 0.5:
                    st.warning("High PoF detected — consider dispatching Logistics Agent.")
                    if auto_trigger:
                        try:
                            requests.post("http://127.0.0.1:8000/api/run_agent", timeout=3)
                            st.success("Auto-triggered AI team for selected machine.")
                        except Exception as e:
                            st.error(f"Auto-trigger failed: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# Export / download section
st.markdown("---")
st.header("Export & Logs")
try:
    logs_available = False
    import django
    django.setup()
    from core_db.models import AgentLog
    logs = AgentLog.objects.order_by('-timestamp')[:200]
    if logs:
        logs_available = True
        df_logs = pd.DataFrame([{
            'timestamp': l.timestamp,
            'machine_id': l.machine_id,
            'status': l.status,
            'risk_score': l.risk_score,
            'recommendation': l.recommendation,
        } for l in logs])
        st.download_button("Download AgentLogs CSV", df_logs.to_csv(index=False).encode('utf-8'), file_name='agentlogs.csv')
    else:
        st.write("No AgentLog entries yet.")
except Exception:
    st.info("AgentLog view unavailable (Django not configured in this environment).")
