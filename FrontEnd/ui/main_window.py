# ui/main_window.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTabWidget, QGridLayout,
                            QGroupBox, QProgressBar, QSlider, QSpinBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette

import pyqtgraph as pg
import numpy as np
import time
import threading

class MainWindow(QMainWindow):
    def __init__(self, command_sender, data_store):
        super().__init__()
        self.command_sender = command_sender
        self.data_store = data_store
        
        # Window properties
        self.setWindowTitle("Rocket Monitoring System")
        self.setMinimumSize(1200, 800)
        
        # Create main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create status bar at top
        self.setup_status_bar()
        
        # Create tab widget for different views
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Initialize data structures for plots
        self.time_data = []
        self.pressure_data = {
            "pt_o1_3": [], "pt_o2_2": [], "pt_p1_6": [], 
            "pt_f2_4": [], "pt_f1_5": [], "pt_f2_4_engine": []
        }
        
        # Add tabs
        self.setup_overview_tab()
        self.setup_oxidizer_tab()
        self.setup_fuel_tab()
        self.setup_engine_tab()
        self.setup_control_tab()
        
        # Setup plots
        
        # Start a timer to regularly update connection status
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.update_connection_status)
        self.connection_timer.start(500)  # Check every 500ms
    
    def setup_status_bar(self):
        status_layout = QHBoxLayout()
        self.main_layout.addLayout(status_layout)
        
        # System status indicators
        self.connection_status = QLabel("NOT CONNECTED")
        self.connection_status.setStyleSheet("background-color: red; padding: 5px; border-radius: 5px;")
        status_layout.addWidget(self.connection_status)
        
        self.armed_status = QLabel("SAFE")
        self.armed_status.setStyleSheet("background-color: green; padding: 5px; border-radius: 5px;")
        status_layout.addWidget(self.armed_status)
        
        # Spacer
        status_layout.addStretch()
        
        # Recording button
        self.record_button = QPushButton("Start Recording")
        self.record_button.setCheckable(True)
        self.record_button.toggled.connect(self.toggle_recording)
        status_layout.addWidget(self.record_button)
        
        # Emergency stop button
        self.estop_button = QPushButton("EMERGENCY STOP")
        self.estop_button.setStyleSheet("background-color: red; color: white; font-weight: bold; min-height: 40px;")
        self.estop_button.clicked.connect(self.emergency_stop)
        status_layout.addWidget(self.estop_button)
    
    def setup_overview_tab(self):
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        
        # Pressure graphs
        pressure_plot = pg.PlotWidget(title="Pressure Readings")
        pressure_plot.setBackground('w')  # Set white background
        pressure_plot.addLegend()
        pressure_plot.setLabel('left', "Pressure", units='PSI')
        pressure_plot.setLabel('bottom', "Time", units='s')
        pressure_plot.getAxis('left').setPen('k')  # Black axis lines
        pressure_plot.getAxis('bottom').setPen('k')
        pressure_plot.getAxis('left').setTextPen('k')  # Black text
        pressure_plot.getAxis('bottom').setTextPen('k')
        self.pressure_plot = pressure_plot
        
        # Create plot lines with different colors
        self.pressure_curves = {}
        colors = ['r', 'g', 'b', 'c', 'm', 'k']
        for i, name in enumerate(self.pressure_data.keys()):
            pen = pg.mkPen(color=colors[i % len(colors)], width=2)
            self.pressure_curves[name] = pressure_plot.plot(
                [], [], name=name, pen=pen
            )
        
        overview_layout.addWidget(pressure_plot)
        
        # System status grid
        status_group = QGroupBox("System Status")
        status_layout = QGridLayout(status_group)
        
        # Add status indicators for each component
        self.status_indicators = {}
        
        # Oxidizer system indicators
        status_layout.addWidget(QLabel("Oxidizer System:"), 0, 0)
        self.status_indicators["oxidizer"] = QLabel("Unknown")
        status_layout.addWidget(self.status_indicators["oxidizer"], 0, 1)
        
        # Fuel system indicators
        status_layout.addWidget(QLabel("Fuel System:"), 1, 0)
        self.status_indicators["fuel"] = QLabel("Unknown")
        status_layout.addWidget(self.status_indicators["fuel"], 1, 1)
        
        # Engine indicators
        status_layout.addWidget(QLabel("Engine:"), 2, 0)
        self.status_indicators["engine"] = QLabel("Unknown")
        status_layout.addWidget(self.status_indicators["engine"], 2, 1)
        
        overview_layout.addWidget(status_group)
        
        self.tabs.addTab(overview_widget, "Overview")
    
    def setup_oxidizer_tab(self):
        """Set up the tank systems tab with monitoring for all tanks"""
        # Rename to reflect broader focus
        tank_widget = QWidget()
        layout = QGridLayout(tank_widget)
        
        # Create data display panel at the top
        data_group = QGroupBox("Tank Readings")
        data_layout = QGridLayout(data_group)
        
        # --- Oxidizer Tank Section ---
        data_layout.addWidget(QLabel("Oxidizer Tank:", styleSheet="font-weight: bold;"), 0, 0)
        
        # Pressure readings
        data_layout.addWidget(QLabel("Pressure (PSI):"), 1, 0)
        self.ox_pressure_value = QLabel("0.0")
        self.ox_pressure_value.setStyleSheet("font-size: 18px; font-weight: bold;")
        data_layout.addWidget(self.ox_pressure_value, 1, 1)
        
        # Load cell readings
        data_layout.addWidget(QLabel("Load (N):"), 2, 0)
        self.ox_load_value = QLabel("0.0")
        self.ox_load_value.setStyleSheet("font-size: 18px; font-weight: bold;")
        data_layout.addWidget(self.ox_load_value, 2, 1)
        
        # --- Fuel Tank Section ---
        data_layout.addWidget(QLabel("Fuel Tank:", styleSheet="font-weight: bold;"), 0, 2)
        
        # Pressure readings
        data_layout.addWidget(QLabel("Pressure (PSI):"), 1, 2)
        self.fuel_pressure_value = QLabel("0.0")
        self.fuel_pressure_value.setStyleSheet("font-size: 18px; font-weight: bold;")
        data_layout.addWidget(self.fuel_pressure_value, 1, 3)
        
        # --- Pressurant Tank Section ---
        data_layout.addWidget(QLabel("Pressurant Tank:", styleSheet="font-weight: bold;"), 0, 4)
        
        # Pressure readings
        data_layout.addWidget(QLabel("Pressure (PSI):"), 1, 4)
        self.press_pressure_value = QLabel("0.0")
        self.press_pressure_value.setStyleSheet("font-size: 18px; font-weight: bold;")
        data_layout.addWidget(self.press_pressure_value, 1, 5)
        
        # Add data group to main layout
        layout.addWidget(data_group, 0, 0, 1, 2)
        
        # Create plots
        # 1. Oxidizer Tank Pressure
        ox_pressure_plot = pg.PlotWidget(title="Oxidizer Tank Pressure")
        ox_pressure_plot.setBackground('w')  # Set white background
        ox_pressure_plot.setLabel('left', "Pressure", units='PSI')
        ox_pressure_plot.setLabel('bottom', "Time", units='s')
        ox_pressure_plot.getAxis('left').setPen('k')  # Black axis lines
        ox_pressure_plot.getAxis('bottom').setPen('k')
        ox_pressure_plot.getAxis('left').setTextPen('k')  # Black text
        ox_pressure_plot.getAxis('bottom').setTextPen('k')
        ox_pressure_plot.setMinimumHeight(200)
        self.ox_pressure_plot = ox_pressure_plot
        self.ox_pressure_curve = ox_pressure_plot.plot([], [], pen=pg.mkPen(color='k', width=2))
        
        # 2. Oxidizer Tank Load
        ox_load_plot = pg.PlotWidget(title="Oxidizer Tank Weight")
        ox_load_plot.setBackground('w')  # Set white background
        ox_load_plot.setLabel('left', "Mass", units='kg')
        ox_load_plot.setLabel('bottom', "Time", units='s')
        ox_load_plot.getAxis('left').setPen('k')  # Black axis lines
        ox_load_plot.getAxis('bottom').setPen('k')
        ox_load_plot.getAxis('left').setTextPen('k')  # Black text
        ox_load_plot.getAxis('bottom').setTextPen('k')
        ox_load_plot.setMinimumHeight(200)
        self.ox_load_plot = ox_load_plot
        self.ox_load_curve = ox_load_plot.plot([], [], pen=pg.mkPen(color='k', width=2))
        
        # 3. Fuel Tank Pressure
        fuel_pressure_plot = pg.PlotWidget(title="Fuel Tank Pressure")
        fuel_pressure_plot.setBackground('w')  # Set white background
        fuel_pressure_plot.setLabel('left', "Pressure", units='PSI')
        fuel_pressure_plot.setLabel('bottom', "Time", units='s')
        fuel_pressure_plot.getAxis('left').setPen('k')  # Black axis lines
        fuel_pressure_plot.getAxis('bottom').setPen('k')
        fuel_pressure_plot.getAxis('left').setTextPen('k')  # Black text
        fuel_pressure_plot.getAxis('bottom').setTextPen('k')
        fuel_pressure_plot.setMinimumHeight(200)
        self.fuel_pressure_plot = fuel_pressure_plot
        self.fuel_pressure_curve = fuel_pressure_plot.plot([], [], pen=pg.mkPen(color='k', width=2))
        
        # 4. Pressurant Tank Pressure
        press_pressure_plot = pg.PlotWidget(title="Pressurant Tank Pressure")
        press_pressure_plot.setBackground('w')  # Set white background
        press_pressure_plot.setLabel('left', "Pressure", units='PSI')
        press_pressure_plot.setLabel('bottom', "Time", units='s')
        press_pressure_plot.getAxis('left').setPen('k')  # Black axis lines
        press_pressure_plot.getAxis('bottom').setPen('k')
        press_pressure_plot.getAxis('left').setTextPen('k')  # Black text
        press_pressure_plot.getAxis('bottom').setTextPen('k')
        press_pressure_plot.setMinimumHeight(200)
        self.press_pressure_plot = press_pressure_plot
        self.press_pressure_curve = press_pressure_plot.plot([], [], pen=pg.mkPen(color='k', width=2))
        
        # Add plots to layout
        layout.addWidget(ox_pressure_plot, 1, 0)
        layout.addWidget(ox_load_plot, 1, 1)
        layout.addWidget(fuel_pressure_plot, 2, 0)
        layout.addWidget(press_pressure_plot, 2, 1)
        
        # Initialize data arrays for tank tab plots
        self.tank_data = {
            "ox_pressure": [],
            "ox_load": [],
            "fuel_pressure": [],
            "press_pressure": []
        }
        
        # Rename the tab
        self.tabs.addTab(tank_widget, "Tank Systems")
    
    def setup_fuel_tab(self):
        # Placeholder - you would expand this with specific fuel system widgets
        fuel_widget = QWidget()
        layout = QVBoxLayout(fuel_widget)
        layout.addWidget(QLabel("Fuel System Details"))
        
        self.tabs.addTab(fuel_widget, "Fuel System")
    
    def setup_engine_tab(self):
        engine_widget = QWidget()
        layout = QVBoxLayout(engine_widget)
        
        # Create top section with live numerical data
        data_group = QGroupBox("Engine Sensor Readings")
        data_layout = QGridLayout(data_group)
        
        # Pressure sensors section
        data_layout.addWidget(QLabel("Pressure Sensors (PSI):", styleSheet="font-weight: bold;"), 0, 0)
        self.pressure_labels = {}
        
        # Create labels for each pressure sensor
        pressure_sensors = ["pt_f2_4_engine"]
        for i, sensor in enumerate(pressure_sensors):
            data_layout.addWidget(QLabel(f"{sensor.upper()}:"), 1, i)
            self.pressure_labels[sensor] = QLabel("0.0")
            self.pressure_labels[sensor].setStyleSheet("font-size: 18px; font-weight: bold;")
            data_layout.addWidget(self.pressure_labels[sensor], 2, i)
        
        # Add average pressure label
        data_layout.addWidget(QLabel("Average:"), 1, len(pressure_sensors))
        self.avg_pressure_label = QLabel("0.0")
        self.avg_pressure_label.setStyleSheet("font-size: 18px; font-weight: bold; color: blue;")
        data_layout.addWidget(self.avg_pressure_label, 2, len(pressure_sensors))
        
        # Load cell sensors section
        data_layout.addWidget(QLabel("Load Cells (N):", styleSheet="font-weight: bold;"), 3, 0)
        self.load_labels = {}
        
        # Create labels for each load cell
        load_sensors = ["lc_1", "lc_2"]
        for i, sensor in enumerate(load_sensors):
            data_layout.addWidget(QLabel(f"{sensor.upper()}:"), 4, i)
            self.load_labels[sensor] = QLabel("0.0")
            self.load_labels[sensor].setStyleSheet("font-size: 18px; font-weight: bold;")
            data_layout.addWidget(self.load_labels[sensor], 5, i)
        
        # Add average load label
        data_layout.addWidget(QLabel("Average:"), 4, len(load_sensors))
        self.avg_load_label = QLabel("0.0")
        self.avg_load_label.setStyleSheet("font-size: 18px; font-weight: bold; color: blue;")
        data_layout.addWidget(self.avg_load_label, 5, len(load_sensors))
        
        # Temperature sensors section
        data_layout.addWidget(QLabel("Temperature Sensors (°C):", styleSheet="font-weight: bold;"), 6, 0)
        self.temp_labels = {}
        
        # Create labels for each temperature sensor
        temp_sensors = ["tc_1"]
        for i, sensor in enumerate(temp_sensors):
            data_layout.addWidget(QLabel(f"{sensor.upper()}:"), 7, i)
            self.temp_labels[sensor] = QLabel("0.0")
            self.temp_labels[sensor].setStyleSheet("font-size: 18px; font-weight: bold;")
            data_layout.addWidget(self.temp_labels[sensor], 8, i)
        
        # Add average temperature label (just for consistency in this case)
        data_layout.addWidget(QLabel("Average:"), 7, len(temp_sensors))
        self.avg_temp_label = QLabel("0.0")
        self.avg_temp_label.setStyleSheet("font-size: 18px; font-weight: bold; color: blue;")
        data_layout.addWidget(self.avg_temp_label, 8, len(temp_sensors))
        
        # Add the data group to the main layout
        layout.addWidget(data_group)
        
        # Create the three graph sections
        # 1. Pressure Graph
        pressure_plot = pg.PlotWidget(title="Engine Pressure")
        pressure_plot.setBackground('w')  # Set white background
        pressure_plot.setLabel('left', "Pressure", units='PSI')
        pressure_plot.setLabel('bottom', "Time", units='s')
        pressure_plot.getAxis('left').setPen('k')  # Black axis lines
        pressure_plot.getAxis('bottom').setPen('k')
        pressure_plot.getAxis('left').setTextPen('k')  # Black text
        pressure_plot.getAxis('bottom').setTextPen('k')
        self.engine_pressure_plot = pressure_plot
        self.engine_pressure_curve = pressure_plot.plot([], [], pen=pg.mkPen(color='k', width=2))
        
        # 2. Load Cell Graph
        load_plot = pg.PlotWidget(title="Engine Thrust")
        load_plot.setBackground('w')  # Set white background
        load_plot.setLabel('left', "Force", units='N')
        load_plot.setLabel('bottom', "Time", units='s')
        load_plot.getAxis('left').setPen('k')  # Black axis lines
        load_plot.getAxis('bottom').setPen('k')
        load_plot.getAxis('left').setTextPen('k')  # Black text
        load_plot.getAxis('bottom').setTextPen('k')
        self.engine_load_plot = load_plot
        self.engine_load_curves = {}
        for i, sensor in enumerate(load_sensors):
            pen = pg.mkPen(color=['b', 'g'][i % 2], width=2)
            self.engine_load_curves[sensor] = load_plot.plot([], [], name=sensor, pen=pen)
        
        # 3. Temperature Graph
        temp_plot = pg.PlotWidget(title="Engine Temperature")
        temp_plot.setBackground('w')  # Set white background
        temp_plot.setLabel('left', "Temperature", units='°C')
        temp_plot.setLabel('bottom', "Time", units='s')
        temp_plot.getAxis('left').setPen('k')  # Black axis lines
        temp_plot.getAxis('bottom').setPen('k')
        temp_plot.getAxis('left').setTextPen('k')  # Black text
        temp_plot.getAxis('bottom').setTextPen('k')
        self.engine_temp_plot = temp_plot
        self.engine_temp_curve = temp_plot.plot([], [], pen=pg.mkPen(color='k', width=2))
        
        # Add plots to main layout
        layout.addWidget(pressure_plot)
        layout.addWidget(load_plot)
        layout.addWidget(temp_plot)
        
        # Initialize data structures for engine tab plots
        self.engine_data = {
            "pressure": [],
            "load": {sensor: [] for sensor in load_sensors},
            "temp": []
        }
        
        self.tabs.addTab(engine_widget, "Engine")
    
    def setup_control_tab(self):
        control_widget = QWidget()
        layout = QGridLayout(control_widget)
        
        # Solenoid valve controls
        solenoid_group = QGroupBox("Solenoid Valves")
        solenoid_layout = QGridLayout(solenoid_group)
        
        # RVV-O valve
        solenoid_layout.addWidget(QLabel("RVV-O:"), 0, 0)
        self.rvv_o_button = QPushButton("CLOSED")
        self.rvv_o_button.setCheckable(True)
        self.rvv_o_button.toggled.connect(lambda checked: self.toggle_solenoid(1, 0x01, checked))
        solenoid_layout.addWidget(self.rvv_o_button, 0, 1)
        
        # MPV-P valve
        solenoid_layout.addWidget(QLabel("MPV-P:"), 1, 0)
        self.mpv_p_button = QPushButton("CLOSED")
        self.mpv_p_button.setCheckable(True)
        self.mpv_p_button.toggled.connect(lambda checked: self.toggle_solenoid(2, 0x02, checked))
        solenoid_layout.addWidget(self.mpv_p_button, 1, 1)
        
        # RVV-F valve
        solenoid_layout.addWidget(QLabel("RVV-F:"), 2, 0)
        self.rvv_f_button = QPushButton("CLOSED")
        self.rvv_f_button.setCheckable(True)
        self.rvv_f_button.toggled.connect(lambda checked: self.toggle_solenoid(3, 0x03, checked))
        solenoid_layout.addWidget(self.rvv_f_button, 2, 1)
        
        layout.addWidget(solenoid_group, 0, 0)
        
        # Servo valve controls
        servo_group = QGroupBox("Servo Valves")
        servo_layout = QGridLayout(servo_group)
        
        # DOT-to-Oxidizer Servo
        servo_layout.addWidget(QLabel("DOT-to-Oxidizer:"), 0, 0)
        self.dot_ox_slider = QSlider(Qt.Horizontal)
        self.dot_ox_slider.setMinimum(0)
        self.dot_ox_slider.setMaximum(255)
        self.dot_ox_slider.valueChanged.connect(lambda val: self.update_servo_value(4, val))
        servo_layout.addWidget(self.dot_ox_slider, 0, 1)
        self.dot_ox_value = QSpinBox()
        self.dot_ox_value.setMinimum(0)
        self.dot_ox_value.setMaximum(255)
        self.dot_ox_value.valueChanged.connect(self.dot_ox_slider.setValue)
        servo_layout.addWidget(self.dot_ox_value, 0, 2)
        
        # MPF-F Servo
        servo_layout.addWidget(QLabel("MPF-F:"), 1, 0)
        self.mpf_f_slider = QSlider(Qt.Horizontal)
        self.mpf_f_slider.setMinimum(0)
        self.mpf_f_slider.setMaximum(255)
        self.mpf_f_slider.valueChanged.connect(lambda val: self.update_servo_value(5, val))
        servo_layout.addWidget(self.mpf_f_slider, 1, 1)
        self.mpf_f_value = QSpinBox()
        self.mpf_f_value.setMinimum(0)
        self.mpf_f_value.setMaximum(255)
        self.mpf_f_value.valueChanged.connect(self.mpf_f_slider.setValue)
        servo_layout.addWidget(self.mpf_f_value, 1, 2)
        
        # Oxidizer-to-Engine Servo
        servo_layout.addWidget(QLabel("Oxidizer-to-Engine:"), 2, 0)
        self.ox_engine_slider = QSlider(Qt.Horizontal)
        self.ox_engine_slider.setMinimum(0)
        self.ox_engine_slider.setMaximum(255)
        self.ox_engine_slider.valueChanged.connect(lambda val: self.update_servo_value(6, val))
        servo_layout.addWidget(self.ox_engine_slider, 2, 1)
        self.ox_engine_value = QSpinBox()
        self.ox_engine_value.setMinimum(0)
        self.ox_engine_value.setMaximum(255)
        self.ox_engine_value.valueChanged.connect(self.ox_engine_slider.setValue)
        servo_layout.addWidget(self.ox_engine_value, 2, 2)
        
        layout.addWidget(servo_group, 0, 1)
        
        # Actuator controls
        actuator_group = QGroupBox("Actuators & Injectors")
        actuator_layout = QGridLayout(actuator_group)
        
        # Setup similar sliders for actuators...
        
        layout.addWidget(actuator_group, 1, 0, 1, 2)
        
        # System control buttons
        system_group = QGroupBox("System Control")
        system_layout = QHBoxLayout(system_group)
        
        # Arm button
        self.arm_button = QPushButton("ARM SYSTEM")
        self.arm_button.setCheckable(True)
        self.arm_button.toggled.connect(self.toggle_arm)
        system_layout.addWidget(self.arm_button)
        
        # Start sequence button
        self.start_button = QPushButton("START SEQUENCE")
        self.start_button.clicked.connect(self.start_sequence)
        self.start_button.setEnabled(False)  # Disabled until armed
        system_layout.addWidget(self.start_button)
        
        # Abort button
        self.abort_button = QPushButton("ABORT")
        self.abort_button.clicked.connect(self.abort_sequence)
        system_layout.addWidget(self.abort_button)
        
        layout.addWidget(system_group, 2, 0, 1, 2)
        
        self.tabs.addTab(control_widget, "Control Panel")
    
    def update_ui(self):
        """Update UI with latest telemetry data"""
        if not self.data_store.latest_telemetry:
            print("No telemetry received.")
            return
        
        # Prevent plotting until UI is fully ready
        if not hasattr(self, 'engine_data'):
            return
        
        telemetry = self.data_store.latest_telemetry
        
        # Update time data for plots
        current_time = time.time()
        
        # Set the max data points to keep
        MAX_POINTS = 500
        
        if not hasattr(self, 'start_time'):
            # First point, initialize start time
            self.start_time = current_time
            self.time_data = [0]
            
            # Initialize all data arrays with the first point
            for key in self.pressure_data:
                self.pressure_data[key] = [telemetry["pressure"][key]]
                
            # Initialize engine data arrays
            self.engine_data["pressure"] = [telemetry["pressure"]["pt_f2_4_engine"]]
            for sensor in ["lc_1", "lc_2"]:
                self.engine_data["load"][sensor] = [telemetry["load_cells"][sensor]]
            self.engine_data["temp"] = [telemetry["temperature"]["tc_1"]]
            
            # Initialize tank data arrays
            if hasattr(self, 'tank_data'):
                ox_pressure = (telemetry["pressure"]["pt_o1_3"] + telemetry["pressure"]["pt_o2_2"]) / 2
                ox_load = (telemetry["load_cells"]["lc_3"] + telemetry["load_cells"]["lc_4"]) / 2
                fuel_pressure = (telemetry["pressure"]["pt_f2_4"] + telemetry["pressure"]["pt_f1_5"]) / 2
                press_pressure = telemetry["pressure"]["pt_p1_6"]
                
                self.tank_data["ox_pressure"] = [ox_pressure]
                self.tank_data["ox_load"] = [ox_load]
                self.tank_data["fuel_pressure"] = [fuel_pressure]
                self.tank_data["press_pressure"] = [press_pressure]
        else:
            # Add new data point
            elapsed_seconds = current_time - self.start_time
            self.time_data.append(elapsed_seconds)
            
            # Add new data to all arrays
            for key in self.pressure_data:
                self.pressure_data[key].append(telemetry["pressure"][key])
                
            self.engine_data["pressure"].append(telemetry["pressure"]["pt_f2_4_engine"])
            for sensor in ["lc_1", "lc_2"]:
                self.engine_data["load"][sensor].append(telemetry["load_cells"][sensor])
            self.engine_data["temp"].append(telemetry["temperature"]["tc_1"])
            
            # Add new data to tank data arrays
            if hasattr(self, 'tank_data'):
                ox_pressure = (telemetry["pressure"]["pt_o1_3"] + telemetry["pressure"]["pt_o2_2"]) / 2
                ox_load = (telemetry["load_cells"]["lc_3"] + telemetry["load_cells"]["lc_4"]) / 2
                fuel_pressure = (telemetry["pressure"]["pt_f2_4"] + telemetry["pressure"]["pt_f1_5"]) / 2
                press_pressure = telemetry["pressure"]["pt_p1_6"]
                
                self.tank_data["ox_pressure"].append(ox_pressure)
                self.tank_data["ox_load"].append(ox_load)
                self.tank_data["fuel_pressure"].append(fuel_pressure)
                self.tank_data["press_pressure"].append(press_pressure)
        
        # Trim all arrays to MAX_POINTS
        if len(self.time_data) > MAX_POINTS:
            self.time_data = self.time_data[-MAX_POINTS:]
            
            for key in self.pressure_data:
                self.pressure_data[key] = self.pressure_data[key][-MAX_POINTS:]
                
            self.engine_data["pressure"] = self.engine_data["pressure"][-MAX_POINTS:]
            for sensor in ["lc_1", "lc_2"]:
                self.engine_data["load"][sensor] = self.engine_data["load"][sensor][-MAX_POINTS:]
            self.engine_data["temp"] = self.engine_data["temp"][-MAX_POINTS:]
            
            # Trim tank data arrays
            if hasattr(self, 'tank_data'):
                self.tank_data["ox_pressure"] = self.tank_data["ox_pressure"][-MAX_POINTS:]
                self.tank_data["ox_load"] = self.tank_data["ox_load"][-MAX_POINTS:]
                self.tank_data["fuel_pressure"] = self.tank_data["fuel_pressure"][-MAX_POINTS:]
                self.tank_data["press_pressure"] = self.tank_data["press_pressure"][-MAX_POINTS:]
        
        # Update overview pressure plots
        for key, curve in self.pressure_curves.items():
            curve.setData(self.time_data, self.pressure_data[key])
        
        # Update engine plots
        try:
            self.engine_pressure_curve.setData(self.time_data, self.engine_data["pressure"])
            
            for sensor in ["lc_1", "lc_2"]:
                self.engine_load_curves[sensor].setData(self.time_data, self.engine_data["load"][sensor])
            
            self.engine_temp_curve.setData(self.time_data, self.engine_data["temp"])
        except Exception as e:
            print(f"Engine plot error: {e}")
        
        # Update tank systems tab data and plots
        if hasattr(self, 'tank_data'):
            # Update numerical displays
            ox_pressure = (telemetry["pressure"]["pt_o1_3"] + telemetry["pressure"]["pt_o2_2"]) / 2
            self.ox_pressure_value.setText(f"{ox_pressure:.1f}")
            
            ox_load = (telemetry["load_cells"]["lc_3"] + telemetry["load_cells"]["lc_4"]) / 2
            self.ox_load_value.setText(f"{ox_load:.1f}")
            
            fuel_pressure = (telemetry["pressure"]["pt_f2_4"] + telemetry["pressure"]["pt_f1_5"]) / 2
            self.fuel_pressure_value.setText(f"{fuel_pressure:.1f}")
            
            press_pressure = telemetry["pressure"]["pt_p1_6"]
            self.press_pressure_value.setText(f"{press_pressure:.1f}")
            
            # Update plots
            try:
                # Make sure we're using the same time array for all plots
                self.ox_pressure_curve.setData(self.time_data, self.tank_data["ox_pressure"])
                self.ox_load_curve.setData(self.time_data, self.tank_data["ox_load"])
                self.fuel_pressure_curve.setData(self.time_data, self.tank_data["fuel_pressure"])
                self.press_pressure_curve.setData(self.time_data, self.tank_data["press_pressure"])
            except Exception as e:
                print(f"Tank plot error: {e}")
            
            # Set x-axis range for all tank plots
            if len(self.time_data) > 1:
                current_end = self.time_data[-1]
                x_min = current_end - 30
                x_max = current_end
                self.ox_pressure_plot.setXRange(x_min, x_max)
                self.ox_load_plot.setXRange(x_min, x_max)
                self.fuel_pressure_plot.setXRange(x_min, x_max)
                self.press_pressure_plot.setXRange(x_min, x_max)
        
        # Update X-axis range for all other plots
        if len(self.time_data) > 1:
            current_end = self.time_data[-1]
            x_min = current_end - 30
            x_max = current_end
            
            self.pressure_plot.setXRange(x_min, x_max)
            self.engine_pressure_plot.setXRange(x_min, x_max)
            self.engine_load_plot.setXRange(x_min, x_max)
            self.engine_temp_plot.setXRange(x_min, x_max)
        
        # Update sensor readings display
        if hasattr(self, 'pressure_labels'):
            engine_pressure = telemetry["pressure"]["pt_f2_4_engine"]
            self.pressure_labels["pt_f2_4_engine"].setText(f"{engine_pressure:.1f}")
            self.avg_pressure_label.setText(f"{engine_pressure:.1f}")
            
            load_values = []
            for sensor in ["lc_1", "lc_2"]:
                value = telemetry["load_cells"][sensor]
                self.load_labels[sensor].setText(f"{value:.1f}")
                load_values.append(value)
                
            avg_load = sum(load_values) / len(load_values) if load_values else 0
            self.avg_load_label.setText(f"{avg_load:.1f}")
            
            engine_temp = telemetry["temperature"]["tc_1"]
            self.temp_labels["tc_1"].setText(f"{engine_temp:.1f}")
            self.avg_temp_label.setText(f"{engine_temp:.1f}")
        
        # Update status indicators and other UI elements
        if telemetry["system_status"]["armed"]:
            self.armed_status.setText("ARMED")
            self.armed_status.setStyleSheet("background-color: red; padding: 5px; border-radius: 5px;")
            self.arm_button.setChecked(True)
            self.start_button.setEnabled(True)
        else:
            self.armed_status.setText("SAFE")
            self.armed_status.setStyleSheet("background-color: green; padding: 5px; border-radius: 5px;")
            self.arm_button.setChecked(False)
            self.start_button.setEnabled(False)
        
        # Update valve state indicators
        self.rvv_o_button.setChecked(telemetry["solenoid_states"]["rvv_o"])
        self.mpv_p_button.setChecked(telemetry["solenoid_states"]["mpv_p"])
        self.rvv_f_button.setChecked(telemetry["solenoid_states"]["rvv_f"])
        
        # Update servo position indicators
        self.dot_ox_value.setValue(telemetry["servo_positions"]["dot_oxidizer"])
        self.mpf_f_value.setValue(telemetry["servo_positions"]["mpf_f"])
        self.ox_engine_value.setValue(telemetry["servo_positions"]["oxidizer_engine"])
        
        # Update system status text
        ox_pressure = telemetry["pressure"]["pt_o1_3"]
        if ox_pressure < 100:
            self.status_indicators["oxidizer"].setText("LOW PRESSURE")
            self.status_indicators["oxidizer"].setStyleSheet("color: red;")
        elif ox_pressure > 700:
            self.status_indicators["oxidizer"].setText("HIGH PRESSURE")
            self.status_indicators["oxidizer"].setStyleSheet("color: red;")
        else:
            self.status_indicators["oxidizer"].setText("NOMINAL")
            self.status_indicators["oxidizer"].setStyleSheet("color: green;")
    
    def update_connection_status(self):
        connected = self.data_store.check_connection()
        if connected:
            self.connection_status.setText("CONNECTED")
            self.connection_status.setStyleSheet("background-color: green; padding: 5px; border-radius: 5px;")
        else:
            self.connection_status.setText("NOT CONNECTED")
            self.connection_status.setStyleSheet("background-color: red; padding: 5px; border-radius: 5px;")
    
    def toggle_recording(self, checked):
        """Handle recording button toggle"""
        if checked:
            success = self.data_store.start_recording()
            if success:
                self.record_button.setText("Stop Recording")
                print("Recording started")
            else:
                # If it fails, revert the button state
                self.record_button.setChecked(False)
                print("Failed to start recording")
        else:
            success = self.data_store.stop_recording()
            if success:
                self.record_button.setText("Start Recording")
                print("Recording stopped")
            else:
                # If it fails, revert the button state
                self.record_button.setChecked(True)
                print("Failed to stop recording")
    
    def emergency_stop(self):
        # Implement emergency stop procedure
        # This should close all valves and safe the system
        print("EMERGENCY STOP ACTIVATED")
        # Close all valves
        self.command_sender.send_command(0x01, 0x01, 0)  # Close RVV-O
        self.command_sender.send_command(0x01, 0x02, 0)  # Close MPV-P
        self.command_sender.send_command(0x01, 0x03, 0)  # Close RVV-F
        # Set servos to safe position
        self.command_sender.send_command(0x02, 0x04, 0)  # Close DOT-Oxidizer Servo
        self.command_sender.send_command(0x02, 0x05, 0)  # Close MPF-F Servo
        self.command_sender.send_command(0x02, 0x06, 0)  # Close Oxidizer-Engine Servo
        # Disarm system
        self.command_sender.send_command(0x04, 0xFF, 0)  # Disarm system
    
    def toggle_solenoid(self, device_id, bit_mask, state):
        # Send command to toggle solenoid valve in a separate thread
        command_value = 1 if state else 0
        
        # Update button text immediately - don't wait for response
        button = self.sender()
        if button:
            button.setText("OPEN" if state else "CLOSED")
            button.setStyleSheet("background-color: green;" if state else "")
        
        # Send command in background thread to prevent UI freezing
        threading.Thread(
            target=lambda: self.command_sender.send_command(0x01, device_id, command_value),
            daemon=True
        ).start()
    
    def update_servo_value(self, device_id, value):
        # Send command to update servo position
        # Don't send on every value change - only when user releases slider
        sender = self.sender()
        if isinstance(sender, QSlider) and sender.isSliderDown():
            return
        
        response = self.command_sender.send_command(0x02, device_id, value)
        print(f"Servo {device_id} command sent: {value}, Response: {response}")
    
    def toggle_arm(self, armed):
        # Send arm/disarm command
        command_value = 1 if armed else 0
        response = self.command_sender.send_command(0x04, 0xFF, command_value)
        
        if armed:
            self.arm_button.setText("DISARM SYSTEM")
            self.start_button.setEnabled(True)
        else:
            self.arm_button.setText("ARM SYSTEM")
            self.start_button.setEnabled(False)
        
        print(f"Arm command sent: {command_value}, Response: {response}")
    
    def start_sequence(self):
        # Send start sequence command
        response = self.command_sender.send_command(0x05, 0xFF, 1)
        print(f"Start sequence command sent, Response: {response}")
    
    def abort_sequence(self):
        # Send abort sequence command
        response = self.command_sender.send_command(0x06, 0xFF, 1)
        print(f"Abort sequence command sent, Response: {response}")