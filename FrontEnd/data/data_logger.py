import os
import time
import csv
import threading
from datetime import datetime

class DataLogger:
    def __init__(self, log_directory="logs"):
        self.log_directory = log_directory
        self.recording = False
        self.log_file = None
        self.csv_writer = None
        self.lock = threading.Lock()
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
    
    def start_recording(self):
        """Start recording telemetry data to a CSV file."""
        with self.lock:
            if self.recording:
                return False  # Already recording
            
            # Create a timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rocket_telemetry_{timestamp}.csv"
            filepath = os.path.join(self.log_directory, filename)
            
            try:
                self.log_file = open(filepath, 'w', newline='')
                self.csv_writer = csv.writer(self.log_file)
                
                # Write header row with column names
                header = [
                    "timestamp", "elapsed_time",
                    # Pressure sensors
                    "pt_o1_3", "pt_o2_2", "pt_p1_6", "pt_f2_4", "pt_f1_5", "pt_f2_4_engine",
                    # Load cells
                    "lc_1", "lc_2", "lc_3", "lc_4",
                    # Temperature
                    "tc_1",
                    # Valve states
                    "rvv_o", "mpv_p", "rvv_f",
                    # Servo positions
                    "dot_oxidizer", "mpf_f", "oxidizer_engine",
                    # System status
                    "armed", "error"
                ]
                self.csv_writer.writerow(header)
                self.recording = True
                self.start_time = time.time()
                return True
            except Exception as e:
                print(f"Error starting recording: {e}")
                if self.log_file:
                    self.log_file.close()
                    self.log_file = None
                return False
    
    def stop_recording(self):
        """Stop recording and close the file."""
        with self.lock:
            if not self.recording:
                return False  # Not recording
            
            try:
                if self.log_file:
                    self.log_file.close()
                self.log_file = None
                self.csv_writer = None
                self.recording = False
                return True
            except Exception as e:
                print(f"Error stopping recording: {e}")
                return False
    
    def log_telemetry(self, telemetry):
        """Write a telemetry data point to the CSV file."""
        with self.lock:
            if not self.recording or not self.csv_writer:
                return False
            
            try:
                # Get current timestamp and calculate elapsed time
                current_time = time.time()
                elapsed_time = current_time - self.start_time
                
                # Extract values from telemetry dictionary
                row = [
                    int(current_time * 1000),  # millisecond timestamp
                    elapsed_time,
                    # Pressure values
                    telemetry["pressure"]["pt_o1_3"],
                    telemetry["pressure"]["pt_o2_2"],
                    telemetry["pressure"]["pt_p1_6"],
                    telemetry["pressure"]["pt_f2_4"],
                    telemetry["pressure"]["pt_f1_5"],
                    telemetry["pressure"]["pt_f2_4_engine"],
                    # Load cell values
                    telemetry["load_cells"]["lc_1"],
                    telemetry["load_cells"]["lc_2"],
                    telemetry["load_cells"]["lc_3"],
                    telemetry["load_cells"]["lc_4"],
                    # Temperature
                    telemetry["temperature"]["tc_1"],
                    # Valve states
                    int(telemetry["solenoid_states"]["rvv_o"]),
                    int(telemetry["solenoid_states"]["mpv_p"]),
                    int(telemetry["solenoid_states"]["rvv_f"]),
                    # Servo positions
                    telemetry["servo_positions"]["dot_oxidizer"],
                    telemetry["servo_positions"]["mpf_f"],
                    telemetry["servo_positions"]["oxidizer_engine"],
                    # System status
                    int(telemetry["system_status"]["armed"]),
                    int(telemetry["system_status"]["error"])
                ]
                
                self.csv_writer.writerow(row)
                return True
            except Exception as e:
                print(f"Error logging telemetry: {e}")
                return False
    
    def is_recording(self):
        """Return whether recording is active."""
        return self.recording