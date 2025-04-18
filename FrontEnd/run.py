# run.py
import sys
import argparse
import subprocess
import time

def main():
    parser = argparse.ArgumentParser(description="Launch Rocket Monitoring System")
    parser.add_argument("--simulator", action="store_true", help="Run with simulator")
    args = parser.parse_args()
    
    try:
        if args.simulator:
            print("Starting simulator...")
            sim_process = subprocess.Popen([sys.executable, "simulator.py"])
            time.sleep(1)  # Give simulator time to start
        
        print("Starting main application...")
        subprocess.call([sys.executable, "main.py"])
    
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        if args.simulator and 'sim_process' in locals():
            sim_process.terminate()

if __name__ == "__main__":
    main()