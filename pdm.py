"""Predictive maintenance helper (PoF estimator) for PraxisGuard.

This module provides a simple, explainable PoF estimator for the MVP.
Replace or extend with a trained model later.
"""
import pandas as pd
import os


def compute_pof_from_values(vibration: float, temperature: float, vib_thresh=80.0, temp_thresh=90.0) -> float:
    """Compute a simple PoF (0..1) from latest vibration and temperature readings.

    This uses a weighted normalized exceedance heuristic. It's intentionally simple
    so the system is interpretable in the MVP.
    """
    vib_score = max(0.0, (vibration - vib_thresh) / max(1.0, (200 - vib_thresh)))
    temp_score = max(0.0, (temperature - temp_thresh) / max(1.0, (200 - temp_thresh)))
    pof = min(1.0, 0.7 * vib_score + 0.3 * temp_score)
    return round(float(pof), 3)


def compute_pof_for_machine(machine_id: str, csv_path: str = 'live_sensor_stream.csv', window: int = 5,
                           vib_thresh: float = 80.0, temp_thresh: float = 90.0) -> dict:
    """Read the last `window` rows for `machine_id` from the CSV and return PoF and metadata.

    Returns a dict: { 'machine_id', 'pof', 'latest', 'window_count' }
    """
    if not os.path.exists(csv_path):
        return {'machine_id': machine_id, 'pof': 0.0, 'latest': None, 'window_count': 0}

    df = pd.read_csv(csv_path)
    if df.empty or 'machine_id' not in df.columns:
        return {'machine_id': machine_id, 'pof': 0.0, 'latest': None, 'window_count': 0}

    mdf = df[df['machine_id'] == machine_id].tail(window)
    if mdf.empty:
        return {'machine_id': machine_id, 'pof': 0.0, 'latest': None, 'window_count': 0}

    latest = mdf.iloc[-1]
    vib = float(latest.get('vibration', 0.0))
    temp = float(latest.get('temperature', 0.0))
    pof = compute_pof_from_values(vib, temp, vib_thresh=vib_thresh, temp_thresh=temp_thresh)

    return {
        'machine_id': machine_id,
        'pof': pof,
        'latest': {'timestamp': str(latest.get('timestamp')), 'vibration': vib, 'temperature': temp},
        'window_count': len(mdf),
    }


if __name__ == '__main__':
    # quick smoke test
    print(compute_pof_for_machine('MAC-101'))
