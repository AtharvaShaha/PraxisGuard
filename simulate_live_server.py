import os
import sys
import django
import numpy as np
import time

# Setup Django settings - add hackathon_core to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hackathon_core'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackathon_core.settings')
django.setup()

from core_db.models import SensorReading

def simulate():
    print("LIVE DATA STREAMING... (Ctrl+C to stop)")
    count = 0
    while True:
        vib = np.random.normal(20, 2) if count < 10 else np.random.normal(85, 5)
        temp = np.random.normal(45, 1) if count < 10 else np.random.normal(95, 3)
        
        # Save to database
        SensorReading.objects.create(
            machine_id='MAC-101',
            vibration=vib,
            temperature=temp
        )
        print(f"Reading: Vib={vib:.1f}, Temp={temp:.1f} - Saved to DB")
        count += 1
        time.sleep(5)

if __name__ == "__main__":
    simulate()