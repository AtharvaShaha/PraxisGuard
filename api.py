import os
import sys
import django
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

# 1. SETUP DJANGO INSIDE FASTAPI
# Detect the correct Django settings module depending on repo layout.
root = Path(__file__).resolve().parent

# Add hackathon_core to sys.path so Django can find core_db
hackathon_core_path = root / 'hackathon_core'
if hackathon_core_path.exists() and str(hackathon_core_path) not in sys.path:
    sys.path.insert(0, str(hackathon_core_path))

if (root / 'hackathon_core' / 'hackathon_core' / 'settings.py').exists():
    # layout: repo_root/hackathon_core/hackathon_core/settings.py
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackathon_core.settings')
elif (root / 'hackathon_core' / 'settings.py').exists():
    # layout: repo_root/hackathon_core/settings.py
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackathon_core.settings')
else:
    # fallback to original value
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackathon_core.settings')
django.setup()

from core_db.models import AgentLog, SensorReading
from agents import praxis_crew
import json
import requests
from fastapi import Query
from typing import Optional
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


# ============================================
# DATA API ENDPOINTS
# ============================================

@app.get('/api/sensor-readings')
def get_sensor_readings(
    machine_id: Optional[str] = None,
    limit: int = Query(default=100, le=10000),
    offset: int = Query(default=0, ge=0)
):
    """Get all sensor readings from the database.
    
    Query params:
      - machine_id: Filter by machine ID (optional)
      - limit: Number of records to return (default: 100, max: 10000)
      - offset: Number of records to skip (default: 0)
    """
    try:
        queryset = SensorReading.objects.all().order_by('-timestamp')
        
        if machine_id:
            queryset = queryset.filter(machine_id=machine_id)
        
        total_count = queryset.count()
        readings = queryset[offset:offset + limit]
        
        data = [{
            'id': r.id,
            'machine_id': r.machine_id,
            'vibration': r.vibration,
            'temperature': r.temperature,
            'timestamp': r.timestamp.isoformat()
        } for r in readings]
        
        return {
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'data': data
        }
    except Exception as e:
        return {"error": str(e)}


@app.get('/api/sensor-readings/{reading_id}')
def get_sensor_reading_by_id(reading_id: int):
    """Get a specific sensor reading by ID."""
    try:
        reading = SensorReading.objects.filter(id=reading_id).first()
        if not reading:
            return {"error": "Sensor reading not found"}
        
        return {
            'id': reading.id,
            'machine_id': reading.machine_id,
            'vibration': reading.vibration,
            'temperature': reading.temperature,
            'timestamp': reading.timestamp.isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


@app.get('/api/agent-logs')
def get_agent_logs(
    machine_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=10000),
    offset: int = Query(default=0, ge=0)
):
    """Get all agent logs from the database.
    
    Query params:
      - machine_id: Filter by machine ID (optional)
      - status: Filter by status (optional)
      - limit: Number of records to return (default: 100, max: 10000)
      - offset: Number of records to skip (default: 0)
    """
    try:
        queryset = AgentLog.objects.all().order_by('-timestamp')
        
        if machine_id:
            queryset = queryset.filter(machine_id=machine_id)
        if status:
            queryset = queryset.filter(status=status)
        
        total_count = queryset.count()
        logs = queryset[offset:offset + limit]
        
        data = [{
            'id': l.id,
            'machine_id': l.machine_id,
            'status': l.status,
            'risk_score': l.risk_score,
            'recommendation': l.recommendation,
            'timestamp': l.timestamp.isoformat()
        } for l in logs]
        
        return {
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'data': data
        }
    except Exception as e:
        return {"error": str(e)}


@app.get('/api/agent-logs/{log_id}')
def get_agent_log_by_id(log_id: int):
    """Get a specific agent log by ID."""
    try:
        log = AgentLog.objects.filter(id=log_id).first()
        if not log:
            return {"error": "Agent log not found"}
        
        return {
            'id': log.id,
            'machine_id': log.machine_id,
            'status': log.status,
            'risk_score': log.risk_score,
            'recommendation': log.recommendation,
            'timestamp': log.timestamp.isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


@app.get('/api/machines')
def get_machines():
    """Get list of all unique machine IDs with their latest readings."""
    try:
        # Get unique machine IDs
        machine_ids = SensorReading.objects.values_list('machine_id', flat=True).distinct()
        
        machines = []
        for machine_id in machine_ids:
            latest_reading = SensorReading.objects.filter(machine_id=machine_id).order_by('-timestamp').first()
            reading_count = SensorReading.objects.filter(machine_id=machine_id).count()
            
            machines.append({
                'machine_id': machine_id,
                'total_readings': reading_count,
                'latest_reading': {
                    'vibration': latest_reading.vibration,
                    'temperature': latest_reading.temperature,
                    'timestamp': latest_reading.timestamp.isoformat()
                } if latest_reading else None
            })
        
        return {
            'total_machines': len(machines),
            'machines': machines
        }
    except Exception as e:
        return {"error": str(e)}


@app.get('/api/stats')
def get_database_stats():
    """Get overall database statistics."""
    try:
        sensor_count = SensorReading.objects.count()
        agent_log_count = AgentLog.objects.count()
        
        # Get latest readings
        latest_sensor = SensorReading.objects.order_by('-timestamp').first()
        latest_log = AgentLog.objects.order_by('-timestamp').first()
        
        return {
            'sensor_readings': {
                'total_count': sensor_count,
                'latest_timestamp': latest_sensor.timestamp.isoformat() if latest_sensor else None
            },
            'agent_logs': {
                'total_count': agent_log_count,
                'latest_timestamp': latest_log.timestamp.isoformat() if latest_log else None
            }
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================
# N8N WORKFLOW ENDPOINTS
# ============================================

# Pydantic models for request bodies
class OrderPartsRequest(BaseModel):
    partId: str
    quantity: int = 1
    deviceId: str
    priority: str = "high"

class CrisisAlertRequest(BaseModel):
    deviceId: str
    equipmentType: str
    location: str
    failureType: Optional[str] = "unexpected"
    severity: Optional[str] = "critical"


@app.get('/api/iot/sensors')
def get_iot_sensor_data():
    """
    IoT Sensor Data Endpoint for n8n workflow.
    Returns latest sensor readings with calculated failure probability.
    Used by: "Fetch IoT Sensor Data" node
    """
    try:
        # Get unique machine IDs using a set
        all_readings = SensorReading.objects.all()
        machine_ids = list(set(r.machine_id for r in all_readings))
        
        devices = []
        for machine_id in machine_ids:
            # Get latest reading for each machine
            latest = SensorReading.objects.filter(machine_id=machine_id).order_by('-timestamp').first()
            
            if latest:
                # Get error codes (simulated based on sensor values)
                error_codes = []
                if latest.vibration > 80:
                    error_codes.append("VIB_HIGH")
                if latest.vibration > 90:
                    error_codes.append("VIB_CRITICAL")
                if latest.temperature > 90:
                    error_codes.append("TEMP_HIGH")
                if latest.temperature > 100:
                    error_codes.append("TEMP_CRITICAL")
                
                # Determine equipment type based on machine_id prefix
                equipment_type = "MRI Scanner"  # Default
                if "VEN" in machine_id:
                    equipment_type = "Ventilator"
                elif "XR" in machine_id:
                    equipment_type = "X-Ray Machine"
                elif "CT" in machine_id:
                    equipment_type = "CT Scanner"
                elif "US" in machine_id:
                    equipment_type = "Ultrasound"
                elif "MAC" in machine_id:
                    equipment_type = "Patient Monitor"
                
                devices.append({
                    "deviceId": machine_id,
                    "equipmentType": equipment_type,
                    "vibration": round(latest.vibration, 2),
                    "temperature": round(latest.temperature, 2),
                    "errorCodes": error_codes,
                    "timestamp": latest.timestamp.isoformat(),
                    "status": "operational" if len(error_codes) == 0 else "warning"
                })
        
        return devices
    except Exception as e:
        return {"error": str(e)}


@app.get('/api/inventory')
def check_inventory(deviceType: Optional[str] = None):
    """
    Inventory Check Endpoint for n8n workflow.
    Returns available parts for specified equipment type.
    Used by: "Check Inventory API Tool" node
    """
    # Simulated inventory data - in production, this would query an inventory database
    inventory = {
        "MRI Scanner": [
            {"partId": "MRI-COIL-001", "partName": "RF Coil", "quantity": 3, "minStock": 2, "status": "in_stock"},
            {"partId": "MRI-COOL-001", "partName": "Cooling Pump", "quantity": 1, "minStock": 2, "status": "low_stock"},
            {"partId": "MRI-MAG-001", "partName": "Gradient Magnet", "quantity": 2, "minStock": 1, "status": "in_stock"},
        ],
        "Ventilator": [
            {"partId": "VEN-FLTR-001", "partName": "HEPA Filter", "quantity": 15, "minStock": 10, "status": "in_stock"},
            {"partId": "VEN-TUBE-001", "partName": "Breathing Circuit", "quantity": 25, "minStock": 20, "status": "in_stock"},
            {"partId": "VEN-VALV-001", "partName": "Exhalation Valve", "quantity": 5, "minStock": 5, "status": "low_stock"},
        ],
        "CT Scanner": [
            {"partId": "CT-TUBE-001", "partName": "X-Ray Tube", "quantity": 1, "minStock": 1, "status": "low_stock"},
            {"partId": "CT-DET-001", "partName": "Detector Array", "quantity": 2, "minStock": 1, "status": "in_stock"},
        ],
        "Patient Monitor": [
            {"partId": "MON-SENS-001", "partName": "SpO2 Sensor", "quantity": 20, "minStock": 15, "status": "in_stock"},
            {"partId": "MON-CABL-001", "partName": "ECG Cable", "quantity": 30, "minStock": 20, "status": "in_stock"},
            {"partId": "MON-BATT-001", "partName": "Battery Pack", "quantity": 8, "minStock": 10, "status": "low_stock"},
        ],
        "X-Ray Machine": [
            {"partId": "XR-TUBE-001", "partName": "X-Ray Tube", "quantity": 2, "minStock": 2, "status": "in_stock"},
            {"partId": "XR-COLL-001", "partName": "Collimator", "quantity": 1, "minStock": 1, "status": "low_stock"},
        ],
        "Ultrasound": [
            {"partId": "US-PROB-001", "partName": "Linear Probe", "quantity": 4, "minStock": 3, "status": "in_stock"},
            {"partId": "US-PROB-002", "partName": "Curved Probe", "quantity": 3, "minStock": 2, "status": "in_stock"},
        ]
    }
    
    if deviceType and deviceType in inventory:
        return {
            "deviceType": deviceType,
            "parts": inventory[deviceType],
            "lastUpdated": "2025-11-29T10:00:00Z"
        }
    elif deviceType:
        return {
            "deviceType": deviceType,
            "parts": [],
            "message": f"No inventory data for device type: {deviceType}"
        }
    else:
        # Return all inventory
        return {
            "inventory": inventory,
            "lastUpdated": "2025-11-29T10:00:00Z"
        }


@app.post('/api/orders/parts')
def order_parts(order: OrderPartsRequest):
    """
    Parts Ordering Endpoint for n8n workflow.
    Creates an order for replacement parts.
    Used by: "Order Parts API Tool" node
    """
    import uuid
    from datetime import datetime, timedelta
    
    # Simulated order processing
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    
    # Estimate delivery based on priority
    delivery_days = 1 if order.priority == "critical" else (2 if order.priority == "high" else 5)
    estimated_delivery = (datetime.now() + timedelta(days=delivery_days)).isoformat()
    
    return {
        "orderId": order_id,
        "partId": order.partId,
        "quantity": order.quantity,
        "deviceId": order.deviceId,
        "priority": order.priority,
        "status": "confirmed",
        "estimatedDelivery": estimated_delivery,
        "message": f"Order {order_id} placed successfully. Estimated delivery: {delivery_days} day(s)."
    }


@app.get('/api/hospital-network')
def search_hospital_network(
    equipmentType: str = Query(...),
    location: str = Query(...),
    status: str = Query(default="operational")
):
    """
    Hospital Network Search Endpoint for n8n workflow.
    Searches affiliated hospitals for available backup equipment.
    Used by: "Search Hospital Network Tool" node
    """
    # Simulated hospital network data
    hospital_network = [
        {
            "hospitalId": "HOSP-001",
            "hospitalName": "City General Hospital",
            "location": "Downtown",
            "distance_km": 5.2,
            "equipment": [
                {"equipmentType": "MRI Scanner", "equipmentId": "MRI-CG-001", "status": "operational", "available": True},
                {"equipmentType": "CT Scanner", "equipmentId": "CT-CG-001", "status": "operational", "available": True},
                {"equipmentType": "Ventilator", "equipmentId": "VEN-CG-001", "status": "operational", "available": True},
                {"equipmentType": "Patient Monitor", "equipmentId": "MON-CG-001", "status": "operational", "available": True},
            ]
        },
        {
            "hospitalId": "HOSP-002",
            "hospitalName": "Regional Medical Center",
            "location": "North District",
            "distance_km": 12.8,
            "equipment": [
                {"equipmentType": "MRI Scanner", "equipmentId": "MRI-RM-001", "status": "operational", "available": True},
                {"equipmentType": "Ventilator", "equipmentId": "VEN-RM-001", "status": "operational", "available": True},
                {"equipmentType": "X-Ray Machine", "equipmentId": "XR-RM-001", "status": "maintenance", "available": False},
                {"equipmentType": "Ultrasound", "equipmentId": "US-RM-001", "status": "operational", "available": True},
            ]
        },
        {
            "hospitalId": "HOSP-003",
            "hospitalName": "University Medical Hospital",
            "location": "West Campus",
            "distance_km": 8.5,
            "equipment": [
                {"equipmentType": "MRI Scanner", "equipmentId": "MRI-UM-001", "status": "operational", "available": False},
                {"equipmentType": "CT Scanner", "equipmentId": "CT-UM-001", "status": "operational", "available": True},
                {"equipmentType": "Patient Monitor", "equipmentId": "MON-UM-001", "status": "operational", "available": True},
            ]
        },
        {
            "hospitalId": "HOSP-004",
            "hospitalName": "St. Mary's Medical Center",
            "location": "South District",
            "distance_km": 15.3,
            "equipment": [
                {"equipmentType": "Ventilator", "equipmentId": "VEN-SM-001", "status": "operational", "available": True},
                {"equipmentType": "Ventilator", "equipmentId": "VEN-SM-002", "status": "operational", "available": True},
                {"equipmentType": "Patient Monitor", "equipmentId": "MON-SM-001", "status": "operational", "available": True},
            ]
        }
    ]
    
    # Filter hospitals with matching available equipment
    results = []
    for hospital in hospital_network:
        matching_equipment = [
            eq for eq in hospital["equipment"]
            if eq["equipmentType"].lower() == equipmentType.lower()
            and eq["status"] == status
            and eq["available"] == True
        ]
        
        if matching_equipment:
            results.append({
                "hospitalId": hospital["hospitalId"],
                "hospitalName": hospital["hospitalName"],
                "location": hospital["location"],
                "distance_km": hospital["distance_km"],
                "availableEquipment": matching_equipment,
                "estimatedTransportTime_min": int(hospital["distance_km"] * 3)  # ~3 min per km
            })
    
    # Sort by distance
    results.sort(key=lambda x: x["distance_km"])
    
    return {
        "searchQuery": {
            "equipmentType": equipmentType,
            "location": location,
            "status": status
        },
        "resultsCount": len(results),
        "hospitals": results
    }


@app.post('/api/crisis-alert')
def trigger_crisis_alert(alert: CrisisAlertRequest):
    """
    Crisis Alert Endpoint for n8n workflow.
    Triggers emergency response for equipment failure.
    Used by: "Crisis Alert Webhook" node (can also be called directly)
    """
    import uuid
    from datetime import datetime
    
    alert_id = f"ALERT-{uuid.uuid4().hex[:8].upper()}"
    
    # Log the crisis alert
    try:
        AgentLog.objects.create(
            machine_id=alert.deviceId,
            status="CRISIS",
            risk_score=1.0,
            recommendation=f"CRITICAL FAILURE: {alert.equipmentType} at {alert.location}. Immediate backup required. Alert ID: {alert_id}"
        )
    except Exception as e:
        pass  # Continue even if logging fails
    
    return {
        "alertId": alert_id,
        "deviceId": alert.deviceId,
        "equipmentType": alert.equipmentType,
        "location": alert.location,
        "severity": alert.severity,
        "status": "alert_triggered",
        "timestamp": datetime.now().isoformat(),
        "message": f"Crisis alert {alert_id} triggered. Contingency agent activated."
    }


@app.get('/api/maintenance/schedule')
def get_maintenance_schedule(deviceId: Optional[str] = None):
    """
    Get maintenance schedule for equipment.
    """
    from datetime import datetime, timedelta
    
    # Simulated maintenance schedule
    schedule = [
        {
            "scheduleId": "MAINT-001",
            "deviceId": "MAC-101",
            "equipmentType": "Patient Monitor",
            "scheduledDate": (datetime.now() + timedelta(days=3)).isoformat(),
            "type": "preventive",
            "status": "scheduled",
            "estimatedDuration_hours": 2
        },
        {
            "scheduleId": "MAINT-002",
            "deviceId": "MRI-001",
            "equipmentType": "MRI Scanner",
            "scheduledDate": (datetime.now() + timedelta(days=7)).isoformat(),
            "type": "preventive",
            "status": "scheduled",
            "estimatedDuration_hours": 4
        }
    ]
    
    if deviceId:
        schedule = [s for s in schedule if s["deviceId"] == deviceId]
    
    return {
        "schedule": schedule,
        "count": len(schedule)
    }


@app.post('/api/maintenance/schedule')
def create_maintenance_schedule(
    deviceId: str,
    equipmentType: str,
    scheduledDate: str,
    maintenanceType: str = "preventive",
    estimatedDuration: int = 2
):
    """
    Create a new maintenance schedule entry.
    """
    import uuid
    
    schedule_id = f"MAINT-{uuid.uuid4().hex[:8].upper()}"
    
    return {
        "scheduleId": schedule_id,
        "deviceId": deviceId,
        "equipmentType": equipmentType,
        "scheduledDate": scheduledDate,
        "type": maintenanceType,
        "status": "scheduled",
        "estimatedDuration_hours": estimatedDuration,
        "message": f"Maintenance scheduled successfully. ID: {schedule_id}"
    }