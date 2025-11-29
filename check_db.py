import os
import sys

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hackathon_core'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackathon_core.settings')

import django
django.setup()

from core_db.models import SensorReading

print(f"Total sensor readings in DB: {SensorReading.objects.count()}")
print("\nLast 10 readings (newest first):")
for r in SensorReading.objects.order_by('-timestamp')[:10]:
    print(f"  ID={r.id}, machine={r.machine_id}, vib={r.vibration:.4f}, temp={r.temperature:.4f}, ts={r.timestamp}")

print("\n\nFirst 5 readings (oldest):")
for r in SensorReading.objects.order_by('timestamp')[:5]:
    print(f"  ID={r.id}, machine={r.machine_id}, vib={r.vibration:.4f}, temp={r.temperature:.4f}, ts={r.timestamp}")
