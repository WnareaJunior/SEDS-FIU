# data/packet_parser.py
import struct

class PacketParser:
    def __init__(self):
        # Format string for telemetry packet
        # "<IH6f4f1fB3B3BBI" = 
        # I (uint32) timestamp
        # H (uint16) packet_counter
        # 6f (6 floats) pressure transducers
        # 4f (4 floats) load cells
        # 1f (1 float) temperature sensor
        # B (uint8) solenoid states
        # 3B (3 uint8) servo positions
        # 3B (3 uint8) injector/actuator positions
        # B (uint8) system status
        # I (uint32) checksum
        self.telemetry_format = "<IH6f4f1fB3B3BBI"
        self.telemetry_size = struct.calcsize(self.telemetry_format)
    
    def parse_telemetry(self, data):
        if len(data) != self.telemetry_size:
            print(f"Invalid packet size: {len(data)} (expected {self.telemetry_size})")
            return None
        
        # Verify checksum before unpacking
        packet_data = data[:-4]
        received_checksum = struct.unpack("<I", data[-4:])[0]
        calculated_checksum = self.calculate_crc32(packet_data)
        
        if received_checksum != calculated_checksum:
            print(f"Checksum mismatch: received {received_checksum}, calculated {calculated_checksum}")
            return None
        
        try:
            unpacked = struct.unpack(self.telemetry_format, data)
            
            # Create structured telemetry dictionary
            telemetry = {
                "timestamp": unpacked[0],
                "packet_counter": unpacked[1],
                
                "pressure": {
                    "pt_o1_3": unpacked[2],
                    "pt_o2_2": unpacked[3],
                    "pt_p1_6": unpacked[4],
                    "pt_f2_4": unpacked[5],
                    "pt_f1_5": unpacked[6],
                    "pt_f2_4_engine": unpacked[7]
                },
                
                "load_cells": {
                    "lc_1": unpacked[8],
                    "lc_2": unpacked[9],
                    "lc_3": unpacked[10],
                    "lc_4": unpacked[11]
                },
                
                "temperature": {
                    "tc_1": unpacked[12]
                },
                
                "solenoid_states": {
                    "rvv_o": bool(unpacked[13] & 0x01),
                    "mpv_p": bool(unpacked[13] & 0x02),
                    "rvv_f": bool(unpacked[13] & 0x04)
                },
                
                "servo_positions": {
                    "dot_oxidizer": unpacked[14],
                    "mpf_f": unpacked[15],
                    "oxidizer_engine": unpacked[16]
                },
                
                "actuator_positions": {
                    "in_1": unpacked[17],
                    "ac_1": unpacked[18],
                    "ac_2": unpacked[19]
                },
                
                "system_status": {
                    "armed": bool(unpacked[20] & 0x01),
                    "recording": bool(unpacked[20] & 0x02),
                    "error": bool(unpacked[20] & 0x04)
                },
                
                "checksum": unpacked[21]
            }
            
            return telemetry
            
        except Exception as e:
            print(f"Error parsing telemetry: {e}")
            return None
    
    def calculate_crc32(self, data):
        # Simple implementation (use a proper CRC32 in production)
        crc = 0
        for byte in data:
            crc = (crc + byte) & 0xFFFFFFFF
        return crc