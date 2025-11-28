import pandas as pd
import numpy as np
import time
import os

def simulate():
    file_path = 'live_sensor_stream.csv'
    if not os.path.exists(file_path):
        pd.DataFrame(columns=['timestamp','machine_id','vibration','temperature']).to_csv(file_path, index=False)
    
    print("🔴 LIVE DATA STREAMING... (Ctrl+C to stop)")
    count = 0
    while True:
        vib = np.random.normal(20, 2) if count < 10 else np.random.normal(85, 5)
        temp = np.random.normal(45, 1) if count < 10 else np.random.normal(95, 3)
        
        new_row = pd.DataFrame([{'timestamp': pd.Timestamp.now(), 'machine_id': 'MAC-101', 'vibration': vib, 'temperature': temp}])
        new_row.to_csv(file_path, mode='a', header=False, index=False)
        print(f"Reading: Vib={vib:.1f}")
        count += 1
        time.sleep(2)

if __name__ == "__main__":
    simulate()