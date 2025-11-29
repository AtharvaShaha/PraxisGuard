# MySQL Database Migration Summary

## What Changed

Your PraxisGuard application has been migrated from CSV file storage to MySQL database storage.

### 1. Database Model Created
- **New Model**: `SensorReading` in `hackathon_core/core_db/models.py`
  - Fields: `machine_id`, `vibration`, `temperature`, `timestamp`
  - Indexed for fast queries
  - Registered in Django admin panel

### 2. Simulator Updated (`simulate_live_server.py`)
- **Before**: Wrote sensor data to `live_sensor_stream.csv`
- **After**: Saves sensor data directly to MySQL database
- Now shows "Saved to DB" confirmation

### 3. Dashboard Updated (`dashboard.py`)
- **Before**: Read from CSV file using `load_data()`
- **After**: Reads from MySQL using `load_data_from_db()`
- Loads last 1000 records for performance
- Real-time updates from database

### 4. Dependencies Added
- `mysqlclient>=2.2.0` - MySQL connector for Django

## MySQL Configuration

Your MySQL database settings (in `hackathon_core/settings.py`):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'agentic',
        'USER': 'root',
        'PASSWORD': 'Achukuchu@123',
        'HOST': 'localhost',
        'PORT': '3306'
    }
}
```

## Database Tables Created

The following tables were created in your MySQL database (`agentic`):
1. `core_db_sensorreading` - Stores live sensor readings
2. `core_db_agentlog` - Stores AI agent analysis logs
3. Django system tables (auth, sessions, etc.)

## How to View Data

### Via Django Admin
1. Start Django admin server:
   ```powershell
   cd hackathon_core
   python manage.py runserver 8001
   ```
2. Visit: http://127.0.0.1:8001/admin
3. Login with your superuser credentials
4. View "Sensor readings" and "Agent logs"

### Via MySQL Client
```sql
USE agentic;
SELECT * FROM core_db_sensorreading ORDER BY timestamp DESC LIMIT 10;
```

## How to Run

Same as before:
```powershell
.\start_dev.ps1
```

This will:
- ✅ Simulator → Writes to MySQL
- ✅ Dashboard → Reads from MySQL  
- ✅ API → Uses MySQL for agent logs

## Benefits

1. **Better Performance**: Database queries are faster than CSV parsing
2. **Data Integrity**: ACID compliance, no file corruption
3. **Scalability**: Can handle millions of records
4. **Concurrent Access**: Multiple services can access data simultaneously
5. **Query Flexibility**: Can filter, aggregate, and analyze data easily
6. **Admin Interface**: Built-in Django admin to view/manage data

## Rollback (if needed)

To go back to CSV storage, you can revert the changes to:
- `simulate_live_server.py`
- `dashboard.py`

The CSV backup still exists in `live_sensor_stream.csv` if needed.
