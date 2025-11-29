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
    print("Generating HIGH vibration/temperature values to trigger alerts!")
    count = 0
    while True:
        # Always generate HIGH values to trigger failure detection
        # Vibration: 85 +/- 10 (threshold in n8n is 40-60)
        # Temperature: 95 +/- 5 (threshold in n8n is 70-90)
        vib = np.random.normal(85, 10)
        temp = np.random.normal(95, 5)
        
        # Save to database
        SensorReading.objects.create(
            machine_id='MAC-101',
            vibration=vib,
            temperature=temp
        )
        print(f"[HIGH ALERT] Reading: Vib={vib:.1f}, Temp={temp:.1f} - Saved to DB")
        count += 1
        time.sleep(5)

if __name__ == "__main__":
    simulate()