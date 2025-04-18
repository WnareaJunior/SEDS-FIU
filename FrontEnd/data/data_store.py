# data/data_store.py
import time
from collections import deque
from data.data_logger import DataLogger

class DataStore:
    def __init__(self, history_length=100):
        self.latest_telemetry = None
        self.history_length = history_length
        self.telemetry_history = deque(maxlen=history_length)
        self.connected = False
        self.last_update_time = 0
        self.data_logger = DataLogger()
        
    def update_telemetry(self, telemetry):
        self.latest_telemetry = telemetry
        self.telemetry_history.append(telemetry)
        self.last_update_time = time.time()
        self.connected = True
        
        # Log telemetry if recording is active
        if self.data_logger.is_recording():
            self.data_logger.log_telemetry(telemetry)
    
    def start_recording(self):
        """Start recording telemetry data."""
        return self.data_logger.start_recording()
    
    def stop_recording(self):
        """Stop recording telemetry data."""
        return self.data_logger.stop_recording()
    
    def is_recording(self):
        """Check if recording is active."""
        return self.data_logger.is_recording()
    
    def check_connection(self, timeout=2.0):
        # If no telemetry for 2 seconds, consider disconnected
        if time.time() - self.last_update_time > timeout:
            self.connected = False
        return self.connected