# simulator.py
import socket
import struct
import time
import math
import random

class RocketSimulator:
    def __init__(self, ground_station_ip="127.0.0.1", telemetry_port=5555, command_port=5556):
        self.ground_station_ip = ground_station_ip
        self.telemetry_port = telemetry_port
        self.command_port = command_port
        
        # Create UDP socket for telemetry
        self.telemetry_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Create TCP socket for commands
        self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.command_socket.bind(("0.0.0.0", command_port))
        self.command_socket.listen(5)
        
        # Initial system state
        self.system_state = {
            "timestamp": 0,
            "packet_counter": 0,
            "armed": False,
            "recording": False,
            "error": False,
            "solenoids": {
                "rvv_o": False,
                "mpv_p": False,
                "rvv_f": False
            },
            "servos": {
                "dot_oxidizer": 0,
                "mpf_f": 0,
                "oxidizer_engine": 0
            },
            "actuators": {
                "in_1": 0,
                "ac_1": 0,
                "ac_2": 0
            }
        }
        
        # Start command listener thread
        import threading
        self.running = True
        self.command_thread = threading.Thread(target=self.listen_for_commands)
        self.command_thread.daemon = True
        self.command_thread.start()
    
    def listen_for_commands(self):
        while self.running:
            try:
                client_socket, address = self.command_socket.accept()
                print(f"Command connection from {address}")
                
                # Receive command
                command_data = client_socket.recv(16)
                if len(command_data) == 16:
                    self.process_command(command_data, client_socket)
                
                client_socket.close()
            except Exception as e:
                print(f"Command error: {e}")
    
    def process_command(self, command_data, client_socket):
        # Parse command
        timestamp, command_id, command_type, device_id, command_value, verification_code, checksum = struct.unpack("<IHHBBHI", command_data)
        
        print(f"Received command: ID={command_id}, Type={command_type}, Device={device_id}, Value={command_value}")
        
        # Process based on command type
        status_code = 0x00  # Success by default
        
        if command_type == 0x01:  # Solenoid valve
            if device_id == 0x01:  # RVV-O
                self.system_state["solenoids"]["rvv_o"] = bool(command_value)
            elif device_id == 0x02:  # MPV-P
                self.system_state["solenoids"]["mpv_p"] = bool(command_value)
            elif device_id == 0x03:  # RVV-F
                self.system_state["solenoids"]["rvv_f"] = bool(command_value)
            else:
                status_code = 0x03  # Invalid command
        
        elif command_type == 0x02:  # Servo valve
            if device_id == 0x04:  # DOT-Oxidizer
                self.system_state["servos"]["dot_oxidizer"] = command_value
            elif device_id == 0x05:  # MPF-F
                self.system_state["servos"]["mpf_f"] = command_value
            elif device_id == 0x06:  # Oxidizer-Engine
                self.system_state["servos"]["oxidizer_engine"] = command_value
            else:
                status_code = 0x03  # Invalid command
        
        elif command_type == 0x03:  # Actuator position
            if device_id == 0x07:  # IN-1
                self.system_state["actuators"]["in_1"] = command_value
            elif device_id == 0x08:  # AC-1
                self.system_state["actuators"]["ac_1"] = command_value
            elif device_id == 0x09:  # AC-2
                self.system_state["actuators"]["ac_2"] = command_value
            else:
                status_code = 0x03  # Invalid command
        
        elif command_type == 0x04:  # System control
            if device_id == 0xFF:  # System-wide
                self.system_state["armed"] = bool(command_value)
            else:
                status_code = 0x03  # Invalid command
        
        elif command_type == 0x05:  # Start sequence
            print("START SEQUENCE RECEIVED")
            # Would trigger sequence in real system
        
        elif command_type == 0x06:  # Abort sequence
            print("ABORT SEQUENCE RECEIVED")
            # Would abort sequence in real system
        
        else:
            status_code = 0x03  # Invalid command
        
        # Send acknowledgment
        ack_timestamp = int(time.time() * 1000)
        ack_data = struct.pack("<IHHI", ack_timestamp, command_id, status_code, 0)
        client_socket.sendall(ack_data)

    def generate_telemetry(self):
         # Use a relative timestamp instead of absolute milliseconds since epoch
        time_ms = int((time.time() % 3600) * 1000)  # Milliseconds within the last hour
        self.system_state["timestamp"] = time_ms
        self.system_state["packet_counter"] = (self.system_state["packet_counter"] + 1) % 65536

        # Get time in seconds for wave generation
        t = time.time()
        
        # Base pressures with oscillating components
        base_o1_3 = 450.0 + 40.0 * math.sin(t * 0.5)  # Slow wave
        base_o2_2 = 445.0 + 30.0 * math.sin(t * 0.7)  # Different frequency
        base_p1_6 = 950.0 + 50.0 * math.sin(t * 0.3)  # Very slow wave
        base_f2_4 = 420.0 + 35.0 * math.sin(t * 0.6)
        base_f1_5 = 425.0 + 25.0 * math.sin(t * 0.9)  # Faster wave
        base_engine = 300.0 + 60.0 * math.sin(t * 1.1)  # Fastest wave
        
        # Add noise and variations based on valve states
        noise_factor = 5.0
        
        # Adjust pressures based on valve states
        if self.system_state["solenoids"]["mpv_p"]:
            # When pressurant valve is open, pressure increases in tanks
            base_o1_3 += 50.0
            base_o2_2 += 50.0
            base_f2_4 += 50.0
            base_f1_5 += 50.0
            base_p1_6 -= 20.0  # Pressurant tank pressure decreases
        
        if self.system_state["servos"]["mpf_f"] > 0:
            # When fuel valve is open, pressure in engine increases
            valve_factor = self.system_state["servos"]["mpf_f"] / 255.0
            base_engine += 100.0 * valve_factor
            base_f2_4 -= 20.0 * valve_factor
            base_f1_5 -= 20.0 * valve_factor
        
        if self.system_state["solenoids"]["rvv_o"]:
            # When oxidizer vent is open, pressure decreases
            base_o1_3 -= 30.0
            base_o2_2 -= 30.0
        
        if self.system_state["solenoids"]["rvv_f"]:
            # When fuel vent is open, pressure decreases
            base_f2_4 -= 30.0
            base_f1_5 -= 30.0
        
        # Add some noise
        pt_o1_3 = base_o1_3 + random.uniform(-noise_factor, noise_factor)
        pt_o2_2 = base_o2_2 + random.uniform(-noise_factor, noise_factor)
        pt_p1_6 = base_p1_6 + random.uniform(-noise_factor, noise_factor)
        pt_f2_4 = base_f2_4 + random.uniform(-noise_factor, noise_factor)
        pt_f1_5 = base_f1_5 + random.uniform(-noise_factor, noise_factor)
        pt_f2_4_engine = base_engine + random.uniform(-noise_factor, noise_factor)
        
        # Load cells
        lc_1 = 2900.0 + random.uniform(-20, 20)
        lc_2 = 2950.0 + random.uniform(-20, 20)
        if self.system_state["servos"]["mpf_f"] > 0:
            # Thrust increases when fuel valve is open
            thrust_factor = self.system_state["servos"]["mpf_f"] / 255.0
            lc_1 += 500.0 * thrust_factor
            lc_2 += 500.0 * thrust_factor
        
        lc_3 = 950.0 + random.uniform(-10, 10)
        lc_4 = 900.0 + random.uniform(-10, 10)
        
        # Temperature
        tc_1 = 30.0  # Base temperature
        if self.system_state["servos"]["mpf_f"] > 0:
            # Engine heats up when fuel valve is open
            tc_1 += 200.0 * (self.system_state["servos"]["mpf_f"] / 255.0)
        
        # Create binary packet
        solenoid_states = 0
        if self.system_state["solenoids"]["rvv_o"]:
            solenoid_states |= 0x01
        if self.system_state["solenoids"]["mpv_p"]:
            solenoid_states |= 0x02
        if self.system_state["solenoids"]["rvv_f"]:
            solenoid_states |= 0x04
        
        system_status = 0
        if self.system_state["armed"]:
            system_status |= 0x01
        if self.system_state["recording"]:
            system_status |= 0x02
        if self.system_state["error"]:
            system_status |= 0x04
        
        try:
            # Format string: "<IH6f4f1fB3B3BBI"
            packet = struct.pack("<IH",
                              self.system_state["timestamp"],
                              self.system_state["packet_counter"])
            
            # Add pressure values
            packet += struct.pack("<6f", pt_o1_3, pt_o2_2, pt_p1_6, pt_f2_4, pt_f1_5, pt_f2_4_engine)
            
            # Add load cell values
            packet += struct.pack("<4f", lc_1, lc_2, lc_3, lc_4)
            
            # Add temperature
            packet += struct.pack("<f", tc_1)
            
            # Add solenoid states
            packet += struct.pack("<B", solenoid_states)
            
            # Add servo positions
            packet += struct.pack("<3B", 
                              self.system_state["servos"]["dot_oxidizer"],
                              self.system_state["servos"]["mpf_f"],
                              self.system_state["servos"]["oxidizer_engine"])
            
            # Add actuator positions
            packet += struct.pack("<3B",
                              self.system_state["actuators"]["in_1"],
                              self.system_state["actuators"]["ac_1"],
                              self.system_state["actuators"]["ac_2"])
            
            # Add system status
            packet += struct.pack("<B", system_status)
            
             # Calculate proper checksum - simple sum of all bytes
            checksum = sum(packet) & 0xFFFFFFFF
    
            # Add the checksum
            packet += struct.pack("<I", checksum)
    
            return packet
            
        except Exception as e:
            print(f"ERROR DURING PACKET GENERATION: {e}")
            import traceback
            traceback.print_exc()
            # Return a dummy packet to avoid crashing
            return b'\x00' * 62  # Return empty packet with correct size
    
    
    def start_telemetry(self, frequency=10):
        """Start sending telemetry at the specified frequency (Hz)"""
        interval = 1.0 / frequency
        
        while self.running:
            try:
                # Generate and send telemetry packet
                packet = self.generate_telemetry()
                self.telemetry_socket.sendto(packet, (self.ground_station_ip, self.telemetry_port))
                
                # Wait for next interval
                time.sleep(interval)
            except Exception as e:
                print(f"Error sending telemetry: {e}")
    
    def stop(self):
        self.running = False

if __name__ == "__main__":
    # Create simulator
    simulator = RocketSimulator()
    
    try:
        print("Starting rocket simulator...")
        print("Press Ctrl+C to stop")
        simulator.start_telemetry()
    except KeyboardInterrupt:
        print("Stopping simulator...")
    finally:
        simulator.stop()