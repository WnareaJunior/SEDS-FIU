# network/command_sender.py
import socket
import struct
import time
import threading

class CommandSender:
    def __init__(self, rocket_ip="192.168.1.10", command_port=5556):
        self.rocket_ip = rocket_ip
        self.command_port = command_port
        self.command_id = 0
        self.lock = threading.Lock()
    
    def send_command(self, command_type, device_id, command_value):
        # Create a TCP socket for this command
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(socket.timeout)  # Add timeout to prevent freezing
        
        try:
            # Connect to rocket
            sock.connect((self.rocket_ip, self.command_port))
            
            # Increment command ID atomically
            with self.lock:
                self.command_id = (self.command_id + 1) % 65536  # Keep within uint16 range
                current_id = self.command_id
            
            # Create command packet
            timestamp = int(time.time() * 1000)  # Current time in milliseconds
            verification_code = 0xABCD  # Simple verification code, could be more complex
            
            # Build packet (excluding checksum initially)
            packet = struct.pack("<IHHBB", 
                                timestamp, 
                                current_id,
                                command_type, 
                                device_id,
                                command_value)
            
            # Add verification code
            packet += struct.pack("<H", verification_code)
            
            # Calculate checksum on all preceding bytes
            checksum = self.calculate_crc32(packet)
            
            # Add checksum to packet
            packet += struct.pack("<I", checksum)
            
            # Send the command
            sock.sendall(packet)
            
            # Get acknowledgment
            ack_data = sock.recv(12)  # Acknowledgment packet is 12 bytes
            
            # Parse acknowledgment
            ack = self.parse_acknowledgment(ack_data)
            
            return ack
            
        except socket.timeout:
            print(f"Command timed out: Type={command_type}, Device={device_id}")
            return {"status": "ERROR", "message": "Connection timed out"}
        except ConnectionRefusedError:
            print(f"Connection refused: The simulator may not be running")
            return {"status": "ERROR", "message": "Connection refused"}
        except Exception as e:
            print(f"Error sending command: {e}")
            return {"status": "ERROR", "message": str(e)}
        finally:
            sock.close()
    
    def calculate_crc32(self, data):
        # Simple implementation (use a proper CRC32 in production)
        crc = 0
        for byte in data:
            crc = (crc + byte) & 0xFFFFFFFF
        return crc
    
    def parse_acknowledgment(self, data):
        if len(data) != 12:
            return {"status": "ERROR", "message": "Invalid acknowledgment size"}
        
        timestamp, command_id, status_code, checksum = struct.unpack("<IHHI", data)
        
        # Map status codes to readable messages
        status_messages = {
            0x00: "Success",
            0x01: "In progress",
            0x02: "Rejected (safety interlock)",
            0x03: "Invalid command",
            0x04: "Device not responding",
            0x05: "Execution timeout"
        }
        
        status_message = status_messages.get(status_code, f"Unknown status code: {status_code}")
        
        return {
            "timestamp": timestamp,
            "command_id": command_id,
            "status_code": status_code,
            "status": "OK" if status_code == 0x00 else "ERROR",
            "message": status_message
        }