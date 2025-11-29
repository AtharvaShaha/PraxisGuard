"""
MySQL to PostgreSQL (NeonDB) Migration Script

This script migrates all data from local MySQL database 'agentic' 
to a PostgreSQL NeonDB instance.

Usage:
    python migrate_mysql_to_postgres.py
"""

import mysql.connector
import psycopg2
from psycopg2 import sql
from datetime import datetime

# ============================================
# MySQL Configuration (Source)
# ============================================
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'Achukuchu@123',
    'database': 'agentic'
}

# ============================================
# PostgreSQL NeonDB Configuration (Target)
# REPLACE THESE WITH YOUR NEONDB CREDENTIALS
# ============================================
POSTGRES_CONFIG = {
    'host': 'ep-calm-math-a1vvkyrp-pooler.ap-southeast-1.aws.neon.tech',       # e.g., 'ep-xxx-xxx-123456.us-east-2.aws.neon.tech'
    'port': 5432,
    'user': 'neondb_owner',                  # e.g., 'neondb_owner'
    'password': 'npg_UtnlcBap4h9G',          # Your NeonDB password
    'database': 'neondb',          # e.g., 'neondb'
    'sslmode': 'require'                         # NeonDB requires SSL
}


def get_mysql_connection():
    """Create MySQL connection"""
    print("Connecting to MySQL...")
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    print("✓ Connected to MySQL")
    return conn


def get_postgres_connection():
    """Create PostgreSQL connection"""
    print("Connecting to PostgreSQL NeonDB...")
    conn = psycopg2.connect(
        host=POSTGRES_CONFIG['host'],
        port=POSTGRES_CONFIG['port'],
        user=POSTGRES_CONFIG['user'],
        password=POSTGRES_CONFIG['password'],
        database=POSTGRES_CONFIG['database'],
        sslmode=POSTGRES_CONFIG['sslmode']
    )
    print("✓ Connected to PostgreSQL NeonDB")
    return conn


def create_postgres_tables(pg_conn):
    """Create tables in PostgreSQL matching MySQL schema"""
    cursor = pg_conn.cursor()
    
    # Create AgentLog table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS core_db_agentlog (
            id SERIAL PRIMARY KEY,
            machine_id VARCHAR(100) NOT NULL,
            status VARCHAR(50) NOT NULL,
            risk_score FLOAT NOT NULL,
            recommendation TEXT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Create SensorReading table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS core_db_sensorreading (
            id SERIAL PRIMARY KEY,
            machine_id VARCHAR(100) NOT NULL,
            vibration FLOAT NOT NULL,
            temperature FLOAT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Create indexes for SensorReading (matching Django model)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sensorreading_machine_id 
        ON core_db_sensorreading(machine_id);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sensorreading_timestamp 
        ON core_db_sensorreading(timestamp);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sensorreading_machine_timestamp 
        ON core_db_sensorreading(machine_id, timestamp DESC);
    """)
    
    pg_conn.commit()
    print("✓ PostgreSQL tables created")


def migrate_agentlog(mysql_conn, pg_conn):
    """Migrate AgentLog data"""
    mysql_cursor = mysql_conn.cursor(dictionary=True)
    pg_cursor = pg_conn.cursor()
    
    # Fetch all data from MySQL
    mysql_cursor.execute("SELECT * FROM core_db_agentlog")
    rows = mysql_cursor.fetchall()
    
    if not rows:
        print("  No AgentLog records to migrate")
        return 0
    
    # Insert into PostgreSQL
    insert_query = """
        INSERT INTO core_db_agentlog (id, machine_id, status, risk_score, recommendation, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            machine_id = EXCLUDED.machine_id,
            status = EXCLUDED.status,
            risk_score = EXCLUDED.risk_score,
            recommendation = EXCLUDED.recommendation,
            timestamp = EXCLUDED.timestamp;
    """
    
    count = 0
    for row in rows:
        pg_cursor.execute(insert_query, (
            row['id'],
            row['machine_id'],
            row['status'],
            row['risk_score'],
            row['recommendation'],
            row['timestamp']
        ))
        count += 1
    
    # Update sequence to continue from max id
    pg_cursor.execute("""
        SELECT setval('core_db_agentlog_id_seq', COALESCE((SELECT MAX(id) FROM core_db_agentlog), 1), true);
    """)
    
    pg_conn.commit()
    print(f"  ✓ Migrated {count} AgentLog records")
    return count


def migrate_sensorreading(mysql_conn, pg_conn):
    """Migrate SensorReading data"""
    mysql_cursor = mysql_conn.cursor(dictionary=True)
    pg_cursor = pg_conn.cursor()
    
    # Fetch all data from MySQL
    mysql_cursor.execute("SELECT * FROM core_db_sensorreading")
    rows = mysql_cursor.fetchall()
    
    if not rows:
        print("  No SensorReading records to migrate")
        return 0
    
    # Insert into PostgreSQL in batches
    insert_query = """
        INSERT INTO core_db_sensorreading (id, machine_id, vibration, temperature, timestamp)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            machine_id = EXCLUDED.machine_id,
            vibration = EXCLUDED.vibration,
            temperature = EXCLUDED.temperature,
            timestamp = EXCLUDED.timestamp;
    """
    
    count = 0
    batch_size = 100
    
    for i, row in enumerate(rows):
        pg_cursor.execute(insert_query, (
            row['id'],
            row['machine_id'],
            row['vibration'],
            row['temperature'],
            row['timestamp']
        ))
        count += 1
        
        # Commit in batches
        if (i + 1) % batch_size == 0:
            pg_conn.commit()
            print(f"    Migrated {count} records...")
    
    # Update sequence to continue from max id
    pg_cursor.execute("""
        SELECT setval('core_db_sensorreading_id_seq', COALESCE((SELECT MAX(id) FROM core_db_sensorreading), 1), true);
    """)
    
    pg_conn.commit()
    print(f"  ✓ Migrated {count} SensorReading records")
    return count


def migrate_django_tables(mysql_conn, pg_conn):
    """Migrate Django system tables if they exist"""
    mysql_cursor = mysql_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # List of Django system tables to check
    django_tables = [
        'django_migrations',
        'django_content_type',
        'auth_group',
        'auth_permission',
        'auth_group_permissions',
        'auth_user',
        'auth_user_groups',
        'auth_user_user_permissions',
        'django_admin_log',
        'django_session'
    ]
    
    # Get list of tables in MySQL
    mysql_cursor.execute("SHOW TABLES")
    existing_tables = [row[0] for row in mysql_cursor.fetchall()]
    
    print("\n  Available MySQL tables:", existing_tables)
    
    # For Django tables, it's better to run migrations on the new DB
    # rather than copying system tables
    print("  Note: Django system tables should be recreated via 'python manage.py migrate'")
    print("        Only application data (AgentLog, SensorReading) is migrated.")


def main():
    print("=" * 60)
    print("MySQL to PostgreSQL (NeonDB) Migration")
    print("=" * 60)
    print()
    
    # Validate PostgreSQL config
    if 'YOUR_NEONDB' in POSTGRES_CONFIG['host']:
        print("ERROR: Please update POSTGRES_CONFIG with your NeonDB credentials!")
        print("\nEdit the script and replace:")
        print("  - YOUR_NEONDB_HOST.neon.tech")
        print("  - YOUR_NEONDB_USER")
        print("  - YOUR_NEONDB_PASSWORD")
        print("  - YOUR_NEONDB_DATABASE")
        return
    
    mysql_conn = None
    pg_conn = None
    
    try:
        # Connect to databases
        mysql_conn = get_mysql_connection()
        pg_conn = get_postgres_connection()
        
        print()
        print("Creating PostgreSQL tables...")
        create_postgres_tables(pg_conn)
        
        print()
        print("Migrating data...")
        
        print("\n[1/2] AgentLog table:")
        agentlog_count = migrate_agentlog(mysql_conn, pg_conn)
        
        print("\n[2/2] SensorReading table:")
        sensorreading_count = migrate_sensorreading(mysql_conn, pg_conn)
        
        print()
        print("=" * 60)
        print("Migration Complete!")
        print("=" * 60)
        print(f"  AgentLog records:      {agentlog_count}")
        print(f"  SensorReading records: {sensorreading_count}")
        print(f"  Total records:         {agentlog_count + sensorreading_count}")
        print()
        print("Next steps:")
        print("  1. Update your Django settings.py to use PostgreSQL")
        print("  2. Run 'python manage.py migrate' to create Django system tables")
        print()
        
    except mysql.connector.Error as e:
        print(f"\nMySQL Error: {e}")
    except psycopg2.Error as e:
        print(f"\nPostgreSQL Error: {e}")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        if mysql_conn:
            mysql_conn.close()
            print("MySQL connection closed")
        if pg_conn:
            pg_conn.close()
            print("PostgreSQL connection closed")


if __name__ == "__main__":
    main()
