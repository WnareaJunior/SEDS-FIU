# main.py
import sys
import threading
import socket
import struct
import time
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer

# Custom modules
from ui.main_window import MainWindow
from network.telemetry_receiver import TelemetryReceiver
from network.command_sender import CommandSender
from data.packet_parser import PacketParser
from data.data_store import DataStore
from PyQt5.QtGui import QPalette, QColor

class RocketMonitorApp:
    def __init__(self):
        # Create the Qt application
        self.app = QApplication(sys.argv)

        self.app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(255, 255, 255))
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Highlight, QColor(76, 163, 224))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        self.app.setPalette(palette)
        
        # Initialize data store
        self.data_store = DataStore()
        
        # Initialize packet parser
        self.packet_parser = PacketParser()
        
        # Initialize network components
        self.telemetry_receiver = TelemetryReceiver(self.packet_parser, self.data_store)
        self.command_sender = CommandSender()
        
        # Create main window
        self.main_window = MainWindow(self.command_sender, self.data_store)
        
        # Start the telemetry receiver thread
        self.telemetry_thread = threading.Thread(target=self.telemetry_receiver.start_receiving, daemon=True)
        self.telemetry_thread.start()
        
        # Setup UI update timer (20 Hz)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.main_window.update_ui)
        self.update_timer.start(50)  # 50ms = 20Hz

    def run(self):
        self.main_window.show()
        return self.app.exec_()

if __name__ == "__main__":
    app = RocketMonitorApp()
    sys.exit(app.run())