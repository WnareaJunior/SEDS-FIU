# network/telemetry_receiver.py
import socket
import struct
import time

class TelemetryReceiver:
    def __init__(self, packet_parser, data_store, ip="0.0.0.0", port=5555):
        self.ip = ip
        self.port = port
        self.packet_parser = packet_parser
        self.data_store = data_store
        self.running = False
        self.socket = None
    
    def start_receiving(self):
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        print(f"Telemetry receiver listening on {self.ip}:{self.port}")
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(1024)
                telemetry = self.packet_parser.parse_telemetry(data)
                if telemetry:
                    self.data_store.update_telemetry(telemetry)
            except Exception as e:
                print(f"Error receiving telemetry: {e}")
    
    def stop_receiving(self):
        self.running = False
        if self.socket:
            self.socket.close()