"""Dev runner to start simulator, FastAPI (uvicorn), and Streamlit concurrently.

Run from project root:
    python dev_runner.py

This script spawns three subprocesses, forwards their output with prefixes,
and attempts a graceful shutdown on Ctrl+C.
"""
import subprocess
import threading
import sys
import os
import time


def stream_output(pipe, prefix):
    try:
        for line in iter(pipe.readline, ''):
            if not line:
                break
            print(f"[{prefix}] {line.rstrip()}")
    except Exception:
        pass


def start_process(name, cmd, cwd=None):
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    t_out = threading.Thread(target=stream_output, args=(proc.stdout, name), daemon=True)
    t_err = threading.Thread(target=stream_output, args=(proc.stderr, name+":ERR"), daemon=True)
    t_out.start()
    t_err.start()
    return proc


def main():
    root = os.path.dirname(__file__)
    python = sys.executable

    commands = [
        ("SIM", [python, "simulate_live_server.py"], root),
        ("API", [python, "-m", "uvicorn", "api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"], root),
        ("UI", [python, "-m", "streamlit", "run", "dashboard.py"], root),
    ]

    procs = []
    try:
        for name, cmd, cwd in commands:
            print(f"Starting {name}: {' '.join(cmd)} (cwd={cwd})")
            procs.append(start_process(name, cmd, cwd=cwd))

        # Wait until processes exit or user presses Ctrl+C
        while True:
            alive = any(p.poll() is None for p in procs)
            if not alive:
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Shutting down processes...")
    finally:
        for p in procs:
            try:
                if p.poll() is None:
                    p.terminate()
            except Exception:
                pass

        # Give them a moment, then kill if needed
        time.sleep(1)
        for p in procs:
            try:
                if p.poll() is None:
                    p.kill()
            except Exception:
                pass


if __name__ == '__main__':
    main()
