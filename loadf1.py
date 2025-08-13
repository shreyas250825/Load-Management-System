import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from collections import deque
import pyttsx3
import winsound
import csv
import datetime
import json
import os
from threading import Thread
import time
import threading

# Constants
CONFIG_FILE = "load_config.json"
DATA_LOG_FILE = "load_data_log.csv"
MAX_DATA_POINTS = 200
UPDATE_INTERVAL = 500  # ms

# Initialize text-to-speech
try:
    tts_engine = pyttsx3.init()
    tts_engine.setProperty("rate", 150)
except:
    tts_engine = None

class LoadManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("MESCOM Certified Load Management System")
        self.root.geometry("1400x900")
        
        # System state
        self.running = False
        self.authenticated = False
        self.alert_history = []
        self.is_closing = False # New flag for graceful shutdown
        self.load_profiles = {
            "Lighting": {"active": True, "current": 50.0, "power_factor": 0.9},
            "HVAC": {"active": False, "current": 200.0, "power_factor": 0.85},
            "Computers": {"active": True, "current": 80.0, "power_factor": 0.95},
            "Industrial": {"active": False, "current": 400.0, "power_factor": 0.8}
        }
        
        # Data storage
        self.voltage_data = deque([0] * MAX_DATA_POINTS, maxlen=MAX_DATA_POINTS)
        self.current_data = deque([0] * MAX_DATA_POINTS, maxlen=MAX_DATA_POINTS)
        self.power_data = deque([0] * MAX_DATA_POINTS, maxlen=MAX_DATA_POINTS)
        self.energy_consumption = 0.0  # kWh
        self.start_time = datetime.datetime.now()
        
        # Thresholds
        self.voltage_threshold = 230.0
        self.current_threshold = 150.0  # Increased default threshold
        self.power_threshold = 30000.0 # Increased default threshold
        self.energy_budget = 1000.0  # Increased default budget (kWh)
        
        # Tariff rates (Rs./kWh)
        self.tariff_rates = {
            "peak": 5.75,
            "off_peak": 5.75,
            "shoulder": 5.75
        }
        
        # Load configuration
        # self.load_config() # This line was moved to create_main_interface
        
        # Initialize UI elements to None so hasattr can be used safely
        self.start_btn = None
        self.stop_btn = None
        self.monitoring_status = None
        self.alert_listbox = None
        self.status_var = None

        # Create UI
        self.create_login_screen()
        
        # Start data thread
        self.data_thread = None
    
    def create_login_screen(self):
        """Create authentication screen"""
        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(pady=100)
        
        tk.Label(self.login_frame, text="MESCOM Load Management System", 
                font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=20)
        
        tk.Label(self.login_frame, text="Username:", font=("Arial", 12)).grid(row=1, column=0, pady=5)
        self.username_entry = tk.Entry(self.login_frame, font=("Arial", 12))
        self.username_entry.grid(row=1, column=1, pady=5)
        
        tk.Label(self.login_frame, text="Password:", font=("Arial", 12)).grid(row=2, column=0, pady=5)
        self.password_entry = tk.Entry(self.login_frame, show="*", font=("Arial", 12))
        self.password_entry.grid(row=2, column=1, pady=5)
        
        login_btn = tk.Button(self.login_frame, text="Login", font=("Arial", 12), 
                            command=self.authenticate, bg="green", fg="white")
        login_btn.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Default credentials (in real system, use proper authentication)
        self.username_entry.insert(0, "mescom")
        self.password_entry.insert(0, "password")
    
    def authenticate(self):
        """Simple authentication check"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if username == "mescom" and password == "password":
            self.authenticated = True
            self.login_frame.destroy()
            self.create_main_interface()
        else:
            messagebox.showerror("Authentication Failed", "Invalid credentials")
    
    def create_main_interface(self):
        """Create main application interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_monitoring_tab()
        self.create_control_tab()
        self.create_energy_tab()
        self.create_alerts_tab()
        self.create_settings_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("System Ready | MESCOM Certified")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, 
                            relief=tk.SUNKEN, anchor=tk.W, font=("Arial", 10))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load configuration after UI elements are created
        self.load_config()
        
        # Start with monitoring stopped
        self.stop_monitoring()
    
    def create_monitoring_tab(self):
        """Create the monitoring tab with graphs and real-time data"""
        self.monitor_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.monitor_tab, text="Monitoring")
        
        # Monitoring Control Panel
        control_panel = tk.Frame(self.monitor_tab, bd=2, relief=tk.RIDGE, padx=10, pady=10)
        control_panel.pack(fill=tk.X, padx=10, pady=5)
        
        # Status indicator
        self.monitoring_status = tk.Label(control_panel, text="Monitoring: STOPPED", 
                                        font=("Arial", 12, "bold"), fg="red")
        self.monitoring_status.grid(row=0, column=0, padx=10)
        
        # Control buttons
        self.start_btn = tk.Button(control_panel, text="Start Monitoring", font=("Arial", 12), 
                                 bg="green", fg="white", command=self.start_monitoring,
                                 width=15, height=2)
        self.start_btn.grid(row=0, column=1, padx=10)
        
        self.stop_btn = tk.Button(control_panel, text="Stop Monitoring", font=("Arial", 12), 
                                bg="red", fg="white", command=self.stop_monitoring,
                                width=15, height=2, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2, padx=10)
        
        # Export and Clear buttons
        export_btn = tk.Button(control_panel, text="Export Data", font=("Arial", 12),
                             command=self.export_data, width=15, height=2)
        export_btn.grid(row=0, column=3, padx=10)
        
        clear_btn = tk.Button(control_panel, text="Clear Data", font=("Arial", 12),
                            command=self.clear_data, width=15, height=2)
        clear_btn.grid(row=0, column=4, padx=10)
        
        # Real-time data display
        data_frame = tk.Frame(self.monitor_tab, bd=2, relief=tk.GROOVE, padx=10, pady=10)
        data_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Voltage display
        tk.Label(data_frame, text="Voltage:", font=("Arial", 12)).grid(row=0, column=0, sticky="e")
        self.voltage_value = tk.Label(data_frame, text="-- V", font=("Arial", 12, "bold"), fg="blue")
        self.voltage_value.grid(row=0, column=1, sticky="w", padx=10)
        
        # Current display
        tk.Label(data_frame, text="Current:", font=("Arial", 12)).grid(row=1, column=0, sticky="e")
        self.current_value = tk.Label(data_frame, text="-- A", font=("Arial", 12, "bold"), fg="green")
        self.current_value.grid(row=1, column=1, sticky="w", padx=10)
        
        # Power display
        tk.Label(data_frame, text="Power:", font=("Arial", 12)).grid(row=2, column=0, sticky="e")
        self.power_value = tk.Label(data_frame, text="-- W", font=("Arial", 12, "bold"), fg="red")
        self.power_value.grid(row=2, column=1, sticky="w", padx=10)
        
        # Energy display
        tk.Label(data_frame, text="Energy:", font=("Arial", 12)).grid(row=3, column=0, sticky="e")
        self.energy_value = tk.Label(data_frame, text="-- kWh", font=("Arial", 12, "bold"), fg="purple")
        self.energy_value.grid(row=3, column=1, sticky="w", padx=10)
        
        # Cost display
        tk.Label(data_frame, text="Cost:", font=("Arial", 12)).grid(row=4, column=0, sticky="e")
        self.cost_value = tk.Label(data_frame, text="-- Rs.", font=("Arial", 12, "bold"), fg="orange")
        self.cost_value.grid(row=4, column=1, sticky="w", padx=10)
        
        # Create graphs
        self.create_graphs()
    
    def create_graphs(self):
        """Create the monitoring graphs"""
        self.fig, (self.voltage_ax, self.current_ax, self.power_ax) = plt.subplots(3, 1, figsize=(12, 8))
        self.fig.tight_layout(pad=3.0)
        
        # Voltage graph
        self.voltage_line, = self.voltage_ax.plot(self.voltage_data, label="Voltage (V)", color="blue")
        self.voltage_ax.set_title("Voltage Over Time")
        self.voltage_ax.set_ylabel("Voltage (V)")
        self.voltage_ax.legend()
        self.voltage_ax.grid(True)
        
        # Current graph
        self.current_line, = self.current_ax.plot(self.current_data, label="Current (A)", color="green")
        self.current_ax.set_title("Current Over Time")
        self.current_ax.set_ylabel("Current (A)")
        self.current_ax.legend()
        self.current_ax.grid(True)
        
        # Power graph
        self.power_line, = self.power_ax.plot(self.power_data, label="Power (W)", color="red")
        self.power_ax.set_title("Power Over Time")
        self.power_ax.set_ylabel("Power (W)")
        self.power_ax.legend()
        self.power_ax.grid(True)
        
        # Embed in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.monitor_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_control_tab(self):
        """Create the load control tab"""
        self.control_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.control_tab, text="Load Control")
        
        tk.Label(self.control_tab, text="Load Management Controls", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        # Create load control frame
        control_frame = tk.Frame(self.control_tab)
        control_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # Create load control widgets for each load profile
        self.load_controls = {}
        for i, (load_name, load_data) in enumerate(self.load_profiles.items()):
            frame = tk.Frame(control_frame, bd=2, relief=tk.GROOVE, padx=10, pady=5)
            frame.grid(row=i, column=0, sticky="ew", pady=5)
            
            # Load name and status
            tk.Label(frame, text=load_name, font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w")
            
            # Toggle button
            btn_text = "ON" if load_data["active"] else "OFF"
            btn_color = "green" if load_data["active"] else "red"
            btn = tk.Button(frame, text=btn_text, bg=btn_color, fg="white",
                           command=lambda n=load_name: self.toggle_load(n))
            btn.grid(row=0, column=1, padx=10)
            
            # Current setting
            tk.Label(frame, text="Current (A):").grid(row=1, column=0, sticky="w")
            current_entry = tk.Entry(frame, width=8)
            current_entry.insert(0, str(load_data["current"]))
            current_entry.grid(row=1, column=1, sticky="w")
            
            # Power factor
            tk.Label(frame, text="Power Factor:").grid(row=2, column=0, sticky="w")
            pf_entry = tk.Entry(frame, width=8)
            pf_entry.insert(0, str(load_data["power_factor"]))
            pf_entry.grid(row=2, column=1, sticky="w")
            
            # Store references
            self.load_controls[load_name] = {
                "button": btn,
                "current_entry": current_entry,
                "pf_entry": pf_entry
            }
        
        # Emergency shutdown button
        emergency_frame = tk.Frame(control_frame, bd=2, relief=tk.RIDGE, padx=10, pady=5)
        emergency_frame.grid(row=len(self.load_profiles), column=0, sticky="ew", pady=10)
        
        tk.Label(emergency_frame, text="Emergency Controls", font=("Arial", 12, "bold")).grid(row=0, column=0)
        tk.Button(emergency_frame, text="SHUTDOWN ALL", bg="red", fg="white",
                command=self.emergency_shutdown).grid(row=0, column=1, padx=10)
    
    def create_energy_tab(self):
        """Create the energy consumption and cost tab"""
        self.energy_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.energy_tab, text="Energy & Cost")
        
        tk.Label(self.energy_tab, text="Energy Consumption Analysis", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        # Energy summary frame
        summary_frame = tk.Frame(self.energy_tab, bd=2, relief=tk.GROOVE, padx=10, pady=10)
        summary_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Energy consumption
        tk.Label(summary_frame, text="Total Energy Consumed:", font=("Arial", 12)).grid(row=0, column=0, sticky="e")
        self.total_energy_label = tk.Label(summary_frame, text="0.0 kWh", font=("Arial", 12, "bold"))
        self.total_energy_label.grid(row=0, column=1, sticky="w", padx=10)
        
        # Cost calculation
        tk.Label(summary_frame, text="Estimated Cost:", font=("Arial", 12)).grid(row=1, column=0, sticky="e")
        self.total_cost_label = tk.Label(summary_frame, text="0.0 Rs.", font=("Arial", 12, "bold"))
        self.total_cost_label.grid(row=1, column=1, sticky="w", padx=10)
        
        # Budget remaining
        tk.Label(summary_frame, text="Energy Budget Remaining:", font=("Arial", 12)).grid(row=2, column=0, sticky="e")
        self.budget_remaining_label = tk.Label(summary_frame, text="100.0 kWh", font=("Arial", 12, "bold"))
        self.budget_remaining_label.grid(row=2, column=1, sticky="w", padx=10)
        
        # Time remaining at current rate
        tk.Label(summary_frame, text="Estimated Time Remaining:", font=("Arial", 12)).grid(row=3, column=0, sticky="e")
        self.time_remaining_label = tk.Label(summary_frame, text="--", font=("Arial", 12, "bold"))
        self.time_remaining_label.grid(row=3, column=1, sticky="w", padx=10)
        
        # Tariff settings
        tariff_frame = tk.Frame(self.energy_tab, bd=2, relief=tk.GROOVE, padx=10, pady=10)
        tariff_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(tariff_frame, text="Tariff Rates (Rs./kWh)", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2)
        
        tk.Label(tariff_frame, text="Peak Hours (8AM-8PM):").grid(row=1, column=0, sticky="e")
        self.peak_rate_entry = tk.Entry(tariff_frame, width=8)
        self.peak_rate_entry.insert(0, str(self.tariff_rates["peak"]))
        self.peak_rate_entry.grid(row=1, column=1, sticky="w", padx=10)
        
        tk.Label(tariff_frame, text="Off-Peak Hours (12AM-6AM):").grid(row=2, column=0, sticky="e")
        self.off_peak_rate_entry = tk.Entry(tariff_frame, width=8)
        self.off_peak_rate_entry.insert(0, str(self.tariff_rates["off_peak"]))
        self.off_peak_rate_entry.grid(row=2, column=1, sticky="w", padx=10)
        
        tk.Label(tariff_frame, text="Shoulder Hours (6AM-8AM, 8PM-12AM):").grid(row=3, column=0, sticky="e")
        self.shoulder_rate_entry = tk.Entry(tariff_frame, width=8)
        self.shoulder_rate_entry.insert(0, str(self.tariff_rates["shoulder"]))
        self.shoulder_rate_entry.grid(row=3, column=1, sticky="w", padx=10)
        
        # Update button
        tk.Button(tariff_frame, text="Update Tariff Rates", 
                 command=self.update_tariff_rates).grid(row=4, column=0, columnspan=2, pady=10)
        
        # Energy history graph
        self.energy_fig, self.energy_ax = plt.subplots(figsize=(10, 4))
        self.energy_line, = self.energy_ax.plot([], [], label="Energy Consumption (kWh)", color="purple")
        self.energy_ax.set_title("Energy Consumption Over Time")
        self.energy_ax.set_xlabel("Time (s)")
        self.energy_ax.set_ylabel("Energy (kWh)")
        self.energy_ax.legend()
        self.energy_ax.grid(True)
        
        # Initialize energy data storage
        self.energy_data = deque([0] * MAX_DATA_POINTS, maxlen=MAX_DATA_POINTS)
        
        self.energy_canvas = FigureCanvasTkAgg(self.energy_fig, master=self.energy_tab)
        self.energy_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    def create_alerts_tab(self):
        """Create the alerts history tab"""
        self.alerts_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.alerts_tab, text="Alerts")
        
        tk.Label(self.alerts_tab, text="Alert History", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        # Alert list
        self.alert_listbox = tk.Listbox(self.alerts_tab, width=120, height=20, font=("Courier", 10))
        self.alert_listbox.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Clear button
        tk.Button(self.alerts_tab, text="Clear Alerts", 
                 command=self.clear_alerts).pack(pady=10)
    
    def create_settings_tab(self):
        """Create the system settings tab"""
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")
        
        tk.Label(self.settings_tab, text="System Configuration", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        # Threshold settings
        threshold_frame = tk.Frame(self.settings_tab, bd=2, relief=tk.GROOVE, padx=10, pady=10)
        threshold_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(threshold_frame, text="Alert Thresholds", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2)
        
        tk.Label(threshold_frame, text="Voltage Threshold (V):").grid(row=1, column=0, sticky="e")
        self.voltage_threshold_entry = tk.Entry(threshold_frame, width=8)
        self.voltage_threshold_entry.grid(row=1, column=1, sticky="w", padx=10)
        
        tk.Label(threshold_frame, text="Current Threshold (A):").grid(row=2, column=0, sticky="e")
        self.current_threshold_entry = tk.Entry(threshold_frame, width=8)
        self.current_threshold_entry.grid(row=2, column=1, sticky="w", padx=10)
        
        tk.Label(threshold_frame, text="Power Threshold (W):").grid(row=3, column=0, sticky="e")
        self.power_threshold_entry = tk.Entry(threshold_frame, width=8)
        self.power_threshold_entry.grid(row=3, column=1, sticky="w", padx=10)
        
        tk.Label(threshold_frame, text="Energy Budget (kWh):").grid(row=4, column=0, sticky="e")
        self.energy_budget_entry = tk.Entry(threshold_frame, width=8)
        self.energy_budget_entry.grid(row=4, column=1, sticky="w", padx=10)
        
        # Update button
        tk.Button(threshold_frame, text="Update Thresholds", 
                 command=self.update_thresholds).grid(row=5, column=0, columnspan=2, pady=10)
        
        # System settings
        system_frame = tk.Frame(self.settings_tab, bd=2, relief=tk.GROOVE, padx=10, pady=10)
        system_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(system_frame, text="System Settings", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2)
        
        # Data logging
        self.logging_var = tk.IntVar(value=1)
        tk.Checkbutton(system_frame, text="Enable Data Logging", variable=self.logging_var).grid(row=1, column=0, sticky="w")
        
        # Alert sounds
        self.alert_sound_var = tk.IntVar(value=1)
        tk.Checkbutton(system_frame, text="Enable Alert Sounds", variable=self.alert_sound_var).grid(row=2, column=0, sticky="w")
        
        # Voice alerts
        self.voice_alerts_var = tk.IntVar(value=1)
        tk.Checkbutton(system_frame, text="Enable Voice Alerts", variable=self.voice_alerts_var).grid(row=3, column=0, sticky="w")
        
        # Save/load buttons
        tk.Button(system_frame, text="Save Configuration", 
                 command=self.save_config).grid(row=4, column=0, pady=10, sticky="w")
        
        tk.Button(system_frame, text="Load Configuration", 
                 command=self.load_config).grid(row=4, column=1, pady=10, sticky="e")
    
    def start_monitoring(self):
        """Start the monitoring process"""
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.monitoring_status.config(text="Monitoring: RUNNING", fg="green")
        self.data_thread = threading.Thread(target=self.data_collection_loop)
        self.data_thread.daemon = True
        self.data_thread.start()
        self.log_alert("Monitoring started", "info")
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.running = False
        
        if hasattr(self, 'start_btn') and self.start_btn and self.start_btn.winfo_exists():
            self.start_btn.config(state=tk.NORMAL)
        if hasattr(self, 'stop_btn') and self.stop_btn and self.stop_btn.winfo_exists():
            self.stop_btn.config(state=tk.DISABLED)
        if hasattr(self, 'monitoring_status') and self.monitoring_status and self.monitoring_status.winfo_exists():
            self.monitoring_status.config(text="Monitoring: STOPPED", fg="red")
        
        # Only log alert if not in the process of full application shutdown
        if not self.is_closing:
            self.log_alert("Monitoring stopped", "info")
    
    def data_collection_loop(self):
        """Main data collection loop"""
        last_update = time.time()
        
        while self.running:
            try:
                # Simulate more realistic data based on active loads
                data = self.simulate_realistic_data()
                
                # Update data storage
                self.voltage_data.append(data["voltage"])
                self.current_data.append(data["current"])
                self.power_data.append(data["power"])
                
                # Calculate energy consumption (kWh) - accumulate energy per update interval
                # Power is in Watts, convert to kW: data["power"] / 1000
                # Time interval is in ms, convert to hours: UPDATE_INTERVAL / 1000 / 3600
                energy_this_interval = (data["power"] / 1000) * (UPDATE_INTERVAL / 3600000)
                self.energy_consumption += energy_this_interval
                
                # Update UI in main thread
                self.root.after(0, self.update_ui, data)
                
                # Log data if enabled
                if self.logging_var.get():
                    self.log_data(data)
                
                # Check for alerts
                self.check_alerts(data)
                
                # Throttle update rate
                time.sleep(UPDATE_INTERVAL / 1000)
                
            except Exception as e:
                self.log_alert(f"System Error: {str(e)}", "error")
                time.sleep(1)
    
    def simulate_realistic_data(self):
        """Generate more realistic load data with occasional errors and spikes"""
        # Base values
        base_voltage = 230.0  # Base voltage
        voltage_variation = random.uniform(-10, 10)  # Larger voltage fluctuations
        
        # Calculate total current based on active loads
        total_current = 0.0
        total_power = 0.0
        
        # Simulate occasional voltage spikes or drops (5% chance)
        if random.random() < 0.05:
            voltage_spike_or_drop_raw = random.uniform(-50, 50)  # Even larger voltage variation
            voltage_spike_or_drop_amount = round(voltage_spike_or_drop_raw, 1) # Round for display
            voltage_variation += voltage_spike_or_drop_raw # Apply the spike/drop to the base variation
            print(f"DEBUG: Voltage fluctuation magnitude to be logged: {voltage_spike_or_drop_amount:.1f}") # Debug print
            self.log_alert(f"Voltage fluctuation detected: {voltage_spike_or_drop_amount:.1f}V fluctuation", "warning")
        
        for load_name, load_data in self.load_profiles.items():
            if load_data["active"]:
                # Add some random variation to each active load
                current_base_variation = random.uniform(-10.0, 10.0) * load_data["current"] / 10 # Scale up variation
                
                # Simulate occasional current spikes (3% chance per load)
                current_spike_magnitude_raw = 0.0
                current_spike_magnitude = 0.0
                if random.random() < 0.03:
                    current_spike_magnitude_raw = random.uniform(20.0, 50.0) # Larger current spikes
                    current_spike_magnitude = round(current_spike_magnitude_raw, 1) # Round for display
                    current_base_variation += current_spike_magnitude_raw # Apply the spike to the base variation
                    print(f"DEBUG: Current spike magnitude to be logged for {load_name}: {current_spike_magnitude:.1f}") # Debug print
                    self.log_alert(f"Current spike detected in {load_name}: {current_spike_magnitude:.1f}A spike", "warning")
                
                load_current = load_data["current"] + current_base_variation
                total_current += load_current
                
                # Calculate power for this load (P = V*I*PF)
                load_power = (base_voltage + voltage_variation) * load_current * load_data["power_factor"]
                total_power += load_power
        
        # Add some small background load (always present)
        background_current = random.uniform(5.0, 10.0) # Increased background current
        total_current += background_current
        background_power = (base_voltage + voltage_variation) * background_current * 0.9
        total_power += background_power
        
        # Simulate occasional power measurement errors (2% chance)
        if random.random() < 0.02:
            power_error_magnitude_raw = random.uniform(-0.1, 0.1) * total_power # Error proportional to new total power
            power_error_magnitude = round(power_error_magnitude_raw, 1) # Round for display
            total_power += power_error_magnitude_raw
            print(f"DEBUG: Power error magnitude to be logged: {power_error_magnitude:.1f}") # Debug print
            self.log_alert(f"Power measurement error detected: {power_error_magnitude:.1f}W error", "warning")
        
        # Ensure values stay within realistic bounds
        voltage = max(150, min(280, base_voltage + voltage_variation)) # Adjust voltage bounds
        current = max(0, min(800, total_current)) # Adjust current bounds for higher loads
        power = max(0, min(200000, total_power)) # Adjust power bounds for higher loads
        
        return {
            "voltage": round(voltage, 2),
            "current": round(current, 2),
            "power": round(power, 2),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def update_ui(self, data):
        """Update all UI elements with current data"""
        # Update real-time values
        self.voltage_value.config(text=f"{data['voltage']} V")
        self.current_value.config(text=f"{data['current']} A")
        self.power_value.config(text=f"{data['power']} W")
        print(f"DEBUG: Energy consumption: {self.energy_consumption:.5f} kWh") # Added debug print
        self.energy_value.config(text=f"{self.energy_consumption:.5f} kWh")
        
        # Update cost
        current_hour = datetime.datetime.now().hour
        if 8 <= current_hour < 20:  # Peak hours
            rate = self.tariff_rates["peak"]
        elif 0 <= current_hour < 6:  # Off-peak hours
            rate = self.tariff_rates["off_peak"]
        else:  # Shoulder hours
            rate = self.tariff_rates["shoulder"]
        
        cost = self.energy_consumption * rate
        self.cost_value.config(text=f"{cost:.5f} Rs.")
        
        # Update budget remaining
        budget_remaining = max(0, self.energy_budget - self.energy_consumption)
        self.budget_remaining_label.config(text=f"{budget_remaining:.2f} kWh")
        
        # Update time remaining estimate
        if self.energy_consumption > 0 and budget_remaining > 0:
            consumption_rate = self.energy_consumption / ((datetime.datetime.now() - self.start_time).total_seconds() / 3600)
            if consumption_rate > 0:
                hours_remaining = budget_remaining / consumption_rate
                self.time_remaining_label.config(text=f"{hours_remaining:.1f} hours at current rate")
        
        # Update graphs with matching x and y data lengths
        x_data = range(len(self.voltage_data))
        self.voltage_line.set_data(x_data, list(self.voltage_data))
        self.current_line.set_data(x_data, list(self.current_data))
        self.power_line.set_data(x_data, list(self.power_data))
        
        # Update energy consumption
        self.energy_data.append(self.energy_consumption)
        self.energy_line.set_data(x_data, list(self.energy_data))
        
        # Update all axes
        self.voltage_ax.relim()
        self.voltage_ax.autoscale_view()
        self.current_ax.relim()
        self.current_ax.autoscale_view()
        self.power_ax.relim()
        self.power_ax.autoscale_view()
        self.energy_ax.relim()
        self.energy_ax.autoscale_view()
        
        # Redraw canvases
        self.canvas.draw()
        self.energy_canvas.draw()
    
    def check_alerts(self, data):
        """Check for threshold violations and trigger alerts"""
        # Get current thresholds from internal variables, not UI entries
        voltage_threshold = self.voltage_threshold
        current_threshold = self.current_threshold
        power_threshold = self.power_threshold
        energy_budget = self.energy_budget
        
        print(f"DEBUG ALERT: Checking alerts with V_thresh={voltage_threshold}, C_thresh={current_threshold}, P_thresh={power_threshold}, E_budget={energy_budget}") # Debug print

        # Check voltage - both high and low thresholds
        if data["voltage"] > voltage_threshold:
            self.log_alert(f"High Voltage Alert! {data['voltage']} V (Threshold: {voltage_threshold} V)", "warning")
            self.trigger_alert(f"High voltage warning: {data['voltage']} V")
        elif data["voltage"] < 180:  # Low voltage threshold
            self.log_alert(f"Low Voltage Alert! {data['voltage']} V (Minimum: 180 V)", "warning")
            self.trigger_alert(f"Low voltage warning: {data['voltage']} V")
        
        # Check current - both high and low thresholds
        if data["current"] > current_threshold:
            self.log_alert(f"High Current Alert! {data['current']} A (Threshold: {current_threshold} A)", "warning")
            self.trigger_alert(f"High current warning: {data['current']} A")
        elif data["current"] < 0.1 and any(load["active"] for load in self.load_profiles.values()):  # Low current when loads are active
            self.log_alert(f"Low Current Alert! {data['current']} A (Expected higher with active loads)", "warning")
            self.trigger_alert(f"Low current warning: {data['current']} A")
        
        # Check power - both high and low thresholds
        if data["power"] > power_threshold:
            self.log_alert(f"High Power Alert! {data['power']} W (Threshold: {power_threshold} W)", "warning")
            self.trigger_alert(f"High power warning: {data['power']} W")
        elif data["power"] < 50 and any(load["active"] for load in self.load_profiles.values()):  # Low power when loads are active
            self.log_alert(f"Low Power Alert! {data['power']} W (Expected higher with active loads)", "warning")
            self.trigger_alert(f"Low power warning: {data['power']} W")
        
        # Check energy budget
        if self.energy_consumption >= energy_budget * 0.9:  # 90% of budget
            if self.energy_consumption >= energy_budget:
                self.log_alert(f"Energy Budget Exceeded! {self.energy_consumption:.2f}/{energy_budget} kWh", "error")
                self.trigger_alert("Energy budget exceeded!")
            else:
                self.log_alert(f"Energy Budget Warning! {self.energy_consumption:.2f}/{energy_budget} kWh (90% threshold)", "warning")
                self.trigger_alert("Energy budget nearly exceeded!")
    
    def trigger_alert(self, message):
        """Trigger visual and audible alerts"""
        if self.alert_sound_var.get():
            try:
                winsound.Beep(1000, 1000)
            except:
                pass
        
        if self.voice_alerts_var.get() and tts_engine:
            try:
                tts_engine.say(message)
                tts_engine.runAndWait()
            except:
                pass
    
    def log_alert(self, message, level="info"):
        """Log an alert message"""
        if self.is_closing: # Do not log alerts if application is closing
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"
        self.alert_history.append(log_entry)
        
        # Schedule UI updates to run in the main thread only if root window exists
        if self.root.winfo_exists():
            try:
                self.root.after(0, self._update_alert_listbox, log_entry, level)
            except tk.TclError as e:
                # This error can occur if self.root has been destroyed before scheduling
                print(f"DEBUG: TclError when scheduling alert update: {e}")

    def _update_alert_listbox(self, log_entry, level):
        try:
            if self.root.winfo_exists() and hasattr(self, 'alert_listbox') and self.alert_listbox and self.alert_listbox.winfo_exists():
                self.alert_listbox.insert(tk.END, log_entry)
                self.alert_listbox.see(tk.END)
                
                # Update status bar for critical alerts
                if level == "error" and hasattr(self, 'status_var') and self.status_var and self.status_var.winfo_exists():
                    self.status_var.set(f"ALERT: {log_entry}")
        except tk.TclError as e:
            # This error can occur during application shutdown if widgets are destroyed
            # while a scheduled UI update is pending. Log it internally but don't crash.
            print(f"DEBUG: TclError during alert listbox update: {e}")
    
    def clear_alerts(self):
        """Clear the alert history"""
        self.alert_listbox.delete(0, tk.END)
    
    def toggle_load(self, load_name):
        """Toggle a load on/off"""
        load_data = self.load_profiles[load_name]
        load_data["active"] = not load_data["active"]
        
        # Update button appearance
        btn = self.load_controls[load_name]["button"]
        if btn.winfo_exists(): # Check if the button widget still exists
            if load_data["active"]:
                btn.config(text="ON", bg="green")
            else:
                btn.config(text="OFF", bg="red")
        
        self.log_alert(f"Load '{load_name}' turned {'ON' if load_data['active'] else 'OFF'}")
    
    def emergency_shutdown(self):
        """Turn off all loads"""
        for load_name in self.load_profiles:
            if self.load_profiles[load_name]["active"]:
                self.toggle_load(load_name)
        
        self.log_alert("EMERGENCY SHUTDOWN ACTIVATED", "error")
        self.trigger_alert("Emergency shutdown activated!")
    
    def update_thresholds(self):
        """Update alert thresholds from UI"""
        try:
            new_voltage_threshold = float(self.voltage_threshold_entry.get())
            new_current_threshold = float(self.current_threshold_entry.get())
            new_power_threshold = float(self.power_threshold_entry.get())
            new_energy_budget = float(self.energy_budget_entry.get())

            print(f"DEBUG: UI input for thresholds: V={new_voltage_threshold}, A={new_current_threshold}, W={new_power_threshold}, E={new_energy_budget}") # Debug print

            self.voltage_threshold = new_voltage_threshold
            self.current_threshold = new_current_threshold
            self.power_threshold = new_power_threshold
            self.energy_budget = new_energy_budget
            
            print(f"DEBUG: Internal thresholds after update: V={self.voltage_threshold}, A={self.current_threshold}, W={self.power_threshold}, E={self.energy_budget}") # Debug print

            self.log_alert("Alert thresholds updated")
            self.save_config() # Save configuration immediately after updating thresholds
        except ValueError:
            self.log_alert("Invalid threshold values", "error")
    
    def update_tariff_rates(self):
        """Update tariff rates from UI"""
        try:
            self.tariff_rates["peak"] = float(self.peak_rate_entry.get())
            self.tariff_rates["off_peak"] = float(self.off_peak_rate_entry.get())
            self.tariff_rates["shoulder"] = float(self.shoulder_rate_entry.get())
            self.log_alert("Tariff rates updated")
        except ValueError:
            self.log_alert("Invalid tariff rates", "error")
    
    def log_data(self, data):
        """Log data to CSV file"""
        try:
            file_exists = os.path.isfile(DATA_LOG_FILE)
            
            with open(DATA_LOG_FILE, mode='a', newline='') as file:
                writer = csv.writer(file)
                
                if not file_exists:
                    writer.writerow(["timestamp", "voltage", "current", "power", "energy"])
                
                writer.writerow([
                    data["timestamp"],
                    data["voltage"],
                    data["current"],
                    data["power"],
                    self.energy_consumption
                ])
        except Exception as e:
            self.log_alert(f"Failed to log data: {str(e)}", "error")
    
    def export_data(self):
        """Export data to a CSV file"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Save Data As"
            )
            
            if filename:
                with open(filename, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["timestamp", "voltage", "current", "power", "energy"])
                    
                    # Generate timestamp for each data point
                    time_step = UPDATE_INTERVAL / 1000  # seconds
                    start_time = datetime.datetime.now() - datetime.timedelta(
                        seconds=len(self.voltage_data) * time_step)
                    
                    for i in range(len(self.voltage_data)):
                        timestamp = (start_time + datetime.timedelta(seconds=i * time_step)).strftime("%Y-%m-%d %H:%M:%S")
                        energy = sum(list(self.power_data)[:i+1]) / 1000 * (time_step / 3600)  # kWh

                        print(f"DEBUG EXPORT: Row data to write: Timestamp={timestamp}, Voltage={list(self.voltage_data)[i]}, Current={list(self.current_data)[i]}, Power={list(self.power_data)[i]}, Energy={energy}") # Debug print

                        writer.writerow([
                            timestamp,
                            list(self.voltage_data)[i],
                            list(self.current_data)[i],
                            list(self.power_data)[i],
                            energy
                        ])
                
                self.log_alert(f"Data exported to {filename}")
        except Exception as e:
            self.log_alert(f"Export failed: {str(e)}", "error")
    
    def save_config(self):
        """Save system configuration to file"""
        config = {
            "voltage_threshold": self.voltage_threshold,
            "current_threshold": self.current_threshold,
            "power_threshold": self.power_threshold,
            "energy_budget": self.energy_budget,
            "tariff_rates": self.tariff_rates,
            "load_profiles": self.load_profiles,
            "logging_enabled": bool(self.logging_var.get()),
            "alert_sounds": bool(self.alert_sound_var.get()),
            "voice_alerts": bool(self.voice_alerts_var.get())
        }
        
        print(f"DEBUG: Configuration being saved to {CONFIG_FILE}: {config}") # Debug print

        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            self.log_alert("Configuration saved")
        except Exception as e:
            self.log_alert(f"Save failed: {str(e)}", "error")
                        
    
    def load_config(self):
        """Load system configuration from file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                
                print(f"DEBUG: Configuration loaded from {CONFIG_FILE}: {config}") # Debug print

                # Update thresholds
                self.voltage_threshold = config.get("voltage_threshold", 230.0)
                self.current_threshold = config.get("current_threshold", 150.0)
                self.power_threshold = config.get("power_threshold", 30000.0)
                self.energy_budget = config.get("energy_budget", 1000.0)
                
                print(f"DEBUG: Loaded thresholds: V={self.voltage_threshold}, A={self.current_threshold}, W={self.power_threshold}, E={self.energy_budget}") # Debug print

                # Update UI elements
                self.voltage_threshold_entry.delete(0, tk.END)
                self.voltage_threshold_entry.insert(0, str(self.voltage_threshold))
                
                self.current_threshold_entry.delete(0, tk.END)
                self.current_threshold_entry.insert(0, str(self.current_threshold))
                
                self.power_threshold_entry.delete(0, tk.END)
                self.power_threshold_entry.insert(0, str(self.power_threshold))
                
                self.energy_budget_entry.delete(0, tk.END)
                self.energy_budget_entry.insert(0, str(self.energy_budget))
                
                # Update tariff rates
                self.tariff_rates = config.get("tariff_rates", self.tariff_rates)
                print(f"DEBUG: Loaded tariff rates: {self.tariff_rates}") # Debug print
                self.peak_rate_entry.delete(0, tk.END)
                self.peak_rate_entry.insert(0, str(self.tariff_rates["peak"]))
                
                self.off_peak_rate_entry.delete(0, tk.END)
                self.off_peak_rate_entry.insert(0, str(self.tariff_rates["off_peak"]))
                
                self.shoulder_rate_entry.delete(0, tk.END)
                self.shoulder_rate_entry.insert(0, str(self.tariff_rates["shoulder"]))
                
                # Update load profiles
                self.load_profiles = config.get("load_profiles", self.load_profiles)
                self.update_load_controls()
                
                # Update settings
                self.logging_var.set(int(config.get("logging_enabled", True)))
                self.alert_sound_var.set(int(config.get("alert_sounds", True)))
                self.voice_alerts_var.set(int(config.get("voice_alerts", True)))
                
                self.log_alert("Configuration loaded")
        except Exception as e:
            self.log_alert(f"Failed to load config: {str(e)}", "error")
    
    def update_load_controls(self):
        """Update load control UI based on current profiles"""
        for load_name, load_data in self.load_profiles.items():
            if load_name in self.load_controls:
                # Update button
                btn = self.load_controls[load_name]["button"]
                btn.config(text="ON" if load_data["active"] else "OFF",
                          bg="green" if load_data["active"] else "red")
                
                # Update current entry
                current_entry = self.load_controls[load_name]["current_entry"]
                current_entry.delete(0, tk.END)
                current_entry.insert(0, str(load_data["current"]))
                
                # Update power factor entry
                pf_entry = self.load_controls[load_name]["pf_entry"]
                pf_entry.delete(0, tk.END)
                pf_entry.insert(0, str(load_data["power_factor"]))
    
    def clear_data(self):
        """Clear all monitoring data"""
        self.voltage_data.clear()
        self.current_data.clear()
        self.power_data.clear()
        self.energy_consumption = 0.0
        self.start_time = datetime.datetime.now()
        
        # Reset displays
        self.voltage_value.config(text="-- V")
        self.current_value.config(text="-- A")
        self.power_value.config(text="-- W")
        self.energy_value.config(text="-- kWh")
        self.cost_value.config(text="-- Rs.")
        
        # Update graphs
        self.voltage_line.set_ydata([])
        self.current_line.set_ydata([])
        self.power_line.set_ydata([])
        self.energy_line.set_data([], [])
        
        # Redraw canvases
        self.canvas.draw()
        self.energy_canvas.draw()
        
        self.log_alert("All monitoring data cleared", "info")
    
    def on_closing(self):
        """Handle window closing event"""
        self.is_closing = True # Set flag to prevent new UI updates
        self.stop_monitoring()

        if self.data_thread and self.data_thread.is_alive():
            self.data_thread.join(timeout=1.0) # Wait for data thread to finish
        
        self.save_config()
        self.root.destroy()

# Main application
if __name__ == "__main__":
    root = tk.Tk()
    app = LoadManagementSystem(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    root.mainloop()               