import streamlit as st
from collections import deque
import matplotlib.pyplot as plt
import random
import datetime
import time
import threading
import csv
import json
import os
import pandas as pd

# Constants
CONFIG_FILE = "load_config.json"
DATA_LOG_FILE = "load_data_log.csv"
MAX_DATA_POINTS = 200
UPDATE_INTERVAL = 0.5  # seconds

class LoadManagementSystem:
    def __init__(self):
        # Initialize all session state variables
        self._init_session_state()
        
        # System state
        self.running = False
        self.authenticated = False
        self.is_closing = False
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
        self.energy_data = deque([0] * MAX_DATA_POINTS, maxlen=MAX_DATA_POINTS)
        self.energy_consumption = 0.0
        self.start_time = datetime.datetime.now()
        
        # Thresholds
        self.voltage_threshold = 230.0
        self.current_threshold = 150.0
        self.power_threshold = 30000.0
        self.energy_budget = 1000.0
        
        # Tariff rates
        self.tariff_rates = {
            "peak": 5.75,
            "off_peak": 5.75,
            "shoulder": 5.75
        }
        
        # Settings
        self.logging_enabled = True
        self.alert_sounds = True
        self.voice_alerts = False
        
        # Load configuration
        self.load_config()
        
        # Thread management
        self.data_thread = None
        self.thread_lock = threading.Lock()

    def _init_session_state(self):
        """Initialize all required session state variables"""
        if 'system_initialized' not in st.session_state:
            st.session_state.system_initialized = True
            st.session_state.monitoring = False
            st.session_state.alerts = []
            st.session_state.latest_data = {
                "voltage": 0,
                "current": 0,
                "power": 0,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.login_attempts = 0
            st.session_state.locked_out = False
            st.session_state.lockout_time = None

    def authenticate(self, username, password):
        """Enhanced authentication with lockout after failed attempts"""
        if st.session_state.locked_out:
            lockout_duration = datetime.datetime.now() - st.session_state.lockout_time
            if lockout_duration.total_seconds() < 300:  # 5 minute lockout
                st.error("Account locked. Please try again after 5 minutes.")
                return False
            else:
                st.session_state.locked_out = False
                st.session_state.login_attempts = 0

        if username == "admin" and password == "password":
            self.authenticated = True
            st.session_state.login_attempts = 0
            return True
        else:
            st.session_state.login_attempts += 1
            if st.session_state.login_attempts >= 3:
                st.session_state.locked_out = True
                st.session_state.lockout_time = datetime.datetime.now()
                st.error("Too many failed attempts. Account locked for 5 minutes.")
            else:
                st.error("Invalid credentials")
            return False
    
    def create_login_page(self):
        """Create a professional login page"""
        st.title("MESCOM Load Management System")
        st.markdown("---")
        
        with st.form("login_form"):
            st.subheader("Authentication Required")
            username = st.text_input("Username", key="username")
            password = st.text_input("Password", type="password", key="password")
            
            if st.form_submit_button("Login"):
                if self.authenticate(username, password):
                    st.rerun()
    
    def create_main_interface(self):
        """Create main application interface"""
        # Create tabs
        tabs = st.tabs(["Monitoring", "Load Control", "Energy & Cost", "Alerts", "Settings"])
        
        with tabs[0]:  # Monitoring tab
            self.create_monitoring_tab()
        
        with tabs[1]:  # Load Control tab
            self.create_control_tab()
        
        with tabs[2]:  # Energy tab
            self.create_energy_tab()
        
        with tabs[3]:  # Alerts tab
            self.create_alerts_tab()
        
        with tabs[4]:  # Settings tab
            self.create_settings_tab()
        
        # Status bar
        st.sidebar.markdown("---")
        st.sidebar.markdown("**System Status:**")
        status_text = "RUNNING" if st.session_state.monitoring else "STOPPED"
        status_color = "green" if st.session_state.monitoring else "red"
        st.sidebar.markdown(f"Monitoring: :{status_color}[{status_text}]")
        st.sidebar.markdown("MESCOM Certified")
        
        # Logout button
        if st.sidebar.button("Logout"):
            self.stop_monitoring()
            self.authenticated = False
            st.rerun()
    
    def create_monitoring_tab(self):
        """Create the monitoring tab with graphs and real-time data"""
        st.header("Monitoring Dashboard")
        
        # Monitoring Control Panel
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Start Monitoring", type="primary"):
                self.start_monitoring()
        
        with col2:
            if st.button("Stop Monitoring", type="secondary"):
                self.stop_monitoring()
        
        with col3:
            if st.button("Export Data"):
                self.export_data()
        
        with col4:
            if st.button("Clear Data"):
                self.clear_data()
        
        # Real-time data display
        st.subheader("Real-time Data")
        data_col1, data_col2, data_col3, data_col4, data_col5 = st.columns(5)
        
        with data_col1:
            st.metric("Voltage", f"{st.session_state.latest_data['voltage']} V")
        
        with data_col2:
            st.metric("Current", f"{st.session_state.latest_data['current']} A")
        
        with data_col3:
            st.metric("Power", f"{st.session_state.latest_data['power']} W")
        
        with data_col4:
            st.metric("Energy", f"{self.energy_consumption:.5f} kWh")
        
        with data_col5:
            current_hour = datetime.datetime.now().hour
            if 8 <= current_hour < 20:  # Peak hours
                rate = self.tariff_rates["peak"]
            elif 0 <= current_hour < 6:  # Off-peak hours
                rate = self.tariff_rates["off_peak"]
            else:  # Shoulder hours
                rate = self.tariff_rates["shoulder"]
            
            cost = self.energy_consumption * rate
            st.metric("Cost", f"{cost:.5f} Rs.")
        
        # Create graphs
        self.create_graphs()
    
    def create_graphs(self):
        """Create the monitoring graphs"""
        st.subheader("Trends")
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
        
        # Voltage graph
        ax1.plot(list(self.voltage_data), label="Voltage (V)", color="blue")
        ax1.set_title("Voltage Over Time")
        ax1.set_ylabel("Voltage (V)")
        ax1.legend()
        ax1.grid(True)
        
        # Current graph
        ax2.plot(list(self.current_data), label="Current (A)", color="green")
        ax2.set_title("Current Over Time")
        ax2.set_ylabel("Current (A)")
        ax2.legend()
        ax2.grid(True)
        
        # Power graph
        ax3.plot(list(self.power_data), label="Power (W)", color="red")
        ax3.set_title("Power Over Time")
        ax3.set_ylabel("Power (W)")
        ax3.legend()
        ax3.grid(True)
        
        plt.tight_layout()
        st.pyplot(fig)
    
    def create_control_tab(self):
        """Create the load control tab"""
        st.header("Load Management Controls")
        
        # Create load control widgets for each load profile
        for load_name, load_data in self.load_profiles.items():
            with st.expander(load_name):
                col1, col2 = st.columns(2)
                
                with col1:
                    status = st.checkbox(
                        f"Active", 
                        value=load_data["active"], 
                        key=f"active_{load_name}",
                        on_change=self.update_load_status,
                        args=(load_name,)
                    )
                
                with col2:
                    current = st.number_input(
                        "Current (A)",
                        value=float(load_data["current"]),
                        key=f"current_{load_name}",
                        on_change=self.update_load_current,
                        args=(load_name,)
                    )
                
                pf = st.number_input(
                    "Power Factor",
                    min_value=0.1,
                    max_value=1.0,
                    value=float(load_data["power_factor"]),
                    key=f"pf_{load_name}",
                    on_change=self.update_load_pf,
                    args=(load_name,)
                )
        
        # Emergency shutdown button
        st.markdown("---")
        if st.button("EMERGENCY SHUTDOWN ALL LOADS", type="primary", use_container_width=True):
            self.emergency_shutdown()
    
    def update_load_status(self, load_name):
        """Update load status from UI"""
        self.load_profiles[load_name]["active"] = st.session_state[f"active_{load_name}"]
        self.log_alert(f"Load '{load_name}' turned {'ON' if self.load_profiles[load_name]['active'] else 'OFF'}")
    
    def update_load_current(self, load_name):
        """Update load current from UI"""
        self.load_profiles[load_name]["current"] = st.session_state[f"current_{load_name}"]
        self.log_alert(f"Load '{load_name}' current updated to {self.load_profiles[load_name]['current']} A")
    
    def update_load_pf(self, load_name):
        """Update load power factor from UI"""
        self.load_profiles[load_name]["power_factor"] = st.session_state[f"pf_{load_name}"]
        self.log_alert(f"Load '{load_name}' power factor updated to {self.load_profiles[load_name]['power_factor']}")
    
    def create_energy_tab(self):
        """Create the energy consumption and cost tab"""
        st.header("Energy Consumption Analysis")
        
        # Energy summary
        st.subheader("Energy Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Energy Consumed", f"{self.energy_consumption:.5f} kWh")
            
            # Calculate cost
            current_hour = datetime.datetime.now().hour
            if 8 <= current_hour < 20:  # Peak hours
                rate = self.tariff_rates["peak"]
            elif 0 <= current_hour < 6:  # Off-peak hours
                rate = self.tariff_rates["off_peak"]
            else:  # Shoulder hours
                rate = self.tariff_rates["shoulder"]
            
            cost = self.energy_consumption * rate
            st.metric("Estimated Cost", f"{cost:.5f} Rs.")
        
        with col2:
            budget_remaining = max(0, self.energy_budget - self.energy_consumption)
            st.metric("Energy Budget Remaining", f"{budget_remaining:.2f} kWh")
            
            # Time remaining estimate
            if self.energy_consumption > 0 and budget_remaining > 0:
                consumption_rate = self.energy_consumption / ((datetime.datetime.now() - self.start_time).total_seconds() / 3600)
                if consumption_rate > 0:
                    hours_remaining = budget_remaining / consumption_rate
                    st.metric("Estimated Time Remaining", f"{hours_remaining:.1f} hours")
        
        with col3:
            # Tariff rate display
            st.metric("Current Tariff Rate", f"{rate} Rs./kWh")
            st.metric("Current Rate Period", 
                     "Peak (8AM-8PM)" if 8 <= current_hour < 20 else 
                     "Off-Peak (12AM-6AM)" if 0 <= current_hour < 6 else 
                     "Shoulder Hours")
        
        # Tariff settings
        st.subheader("Tariff Rates (Rs./kWh)")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self.tariff_rates["peak"] = st.number_input(
                "Peak Hours (8AM-8PM)",
                value=float(self.tariff_rates["peak"]),
                key="peak_rate"
            )
        
        with col2:
            self.tariff_rates["off_peak"] = st.number_input(
                "Off-Peak Hours (12AM-6AM)",
                value=float(self.tariff_rates["off_peak"]),
                key="off_peak_rate"
            )
        
        with col3:
            self.tariff_rates["shoulder"] = st.number_input(
                "Shoulder Hours (6AM-8AM, 8PM-12AM)",
                value=float(self.tariff_rates["shoulder"]),
                key="shoulder_rate"
            )
        
        if st.button("Update Tariff Rates"):
            self.log_alert("Tariff rates updated")
        
        # Energy history graph
        st.subheader("Energy Consumption Over Time")
        energy_fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(list(self.energy_data), label="Energy Consumption (kWh)", color="purple")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Energy (kWh)")
        ax.legend()
        ax.grid(True)
        st.pyplot(energy_fig)
    
    def create_alerts_tab(self):
        """Create the alerts history tab"""
        st.header("Alert History")
        
        # Display alerts in reverse order (newest first)
        for alert in reversed(st.session_state.alerts):
            if "ERROR" in alert:
                st.error(alert)
            elif "WARNING" in alert:
                st.warning(alert)
            else:
                st.info(alert)
        
        if st.button("Clear Alerts"):
            st.session_state.alerts = []
            self.log_alert("Alert history cleared", "info")
    
    def create_settings_tab(self):
        """Create the system settings tab"""
        st.header("System Configuration")
        
        # Threshold settings
        st.subheader("Alert Thresholds")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self.voltage_threshold = st.number_input(
                "Voltage Threshold (V)",
                value=float(self.voltage_threshold),
                key="voltage_threshold"
            )
        
        with col2:
            self.current_threshold = st.number_input(
                "Current Threshold (A)",
                value=float(self.current_threshold),
                key="current_threshold"
            )
        
        with col3:
            self.power_threshold = st.number_input(
                "Power Threshold (W)",
                value=float(self.power_threshold),
                key="power_threshold"
            )
        
        with col4:
            self.energy_budget = st.number_input(
                "Energy Budget (kWh)",
                value=float(self.energy_budget),
                key="energy_budget"
            )
        
        if st.button("Update Thresholds"):
            self.log_alert("Alert thresholds updated")
            self.save_config()
        
        # System settings
        st.subheader("System Settings")
        self.logging_enabled = st.checkbox(
            "Enable Data Logging",
            value=bool(self.logging_enabled),
            key="logging_enabled"
        )
        
        self.alert_sounds = st.checkbox(
            "Enable Alert Sounds",
            value=bool(self.alert_sounds),
            key="alert_sounds"
        )
        
        self.voice_alerts = st.checkbox(
            "Enable Voice Alerts",
            value=bool(self.voice_alerts),
            key="voice_alerts"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Save Configuration"):
                self.save_config()
        
        with col2:
            if st.button("Load Configuration"):
                self.load_config()
                st.rerun()
    
    def start_monitoring(self):
        """Start the monitoring process"""
        if not st.session_state.monitoring:
            with self.thread_lock:
                st.session_state.monitoring = True
                self.running = True
                if self.data_thread is None or not self.data_thread.is_alive():
                    self.data_thread = threading.Thread(target=self._data_collection_loop_wrapper)
                    self.data_thread.daemon = True
                    self.data_thread.start()
                self.log_alert("Monitoring started", "info")
                st.rerun()
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        if st.session_state.monitoring:
            with self.thread_lock:
                st.session_state.monitoring = False
                self.running = False
                self.log_alert("Monitoring stopped", "info")
                st.rerun()
    
    def _data_collection_loop_wrapper(self):
        """Wrapper for data collection loop to handle thread safety"""
        try:
            while self.running and st.session_state.monitoring:
                self.data_collection_loop()
                time.sleep(UPDATE_INTERVAL)
        except Exception as e:
            self.log_alert(f"Data collection error: {str(e)}", "error")
    
    def data_collection_loop(self):
        """Main data collection loop"""
        try:
            # Simulate data
            data = self.simulate_realistic_data()
            
            # Update data storage
            self.voltage_data.append(data["voltage"])
            self.current_data.append(data["current"])
            self.power_data.append(data["power"])
            
            # Calculate energy consumption
            energy_this_interval = (data["power"] / 1000) * (UPDATE_INTERVAL / 3600)
            self.energy_consumption += energy_this_interval
            self.energy_data.append(self.energy_consumption)
            
            # Update session state
            st.session_state.latest_data = data
            
            # Log data if enabled
            if self.logging_enabled:
                self.log_data(data)
            
            # Check for alerts
            self.check_alerts(data)
            
        except Exception as e:
            self.log_alert(f"System Error: {str(e)}", "error")
    
    def simulate_realistic_data(self):
        """Generate realistic load data with occasional errors and spikes"""
        # Base values
        base_voltage = 230.0
        voltage_variation = random.uniform(-10, 10)
        
        # Calculate total current based on active loads
        total_current = 0.0
        total_power = 0.0
        
        # Simulate occasional voltage spikes or drops
        if random.random() < 0.05:
            voltage_spike_or_drop = random.uniform(-50, 50)
            voltage_variation += voltage_spike_or_drop
            self.log_alert(f"Voltage fluctuation detected: {voltage_spike_or_drop:.1f}V fluctuation", "warning")
        
        for load_name, load_data in self.load_profiles.items():
            if load_data["active"]:
                # Add random variation
                current_variation = random.uniform(-10.0, 10.0) * load_data["current"] / 10
                
                # Simulate occasional current spikes
                if random.random() < 0.03:
                    current_spike = random.uniform(20.0, 50.0)
                    current_variation += current_spike
                    self.log_alert(f"Current spike detected in {load_name}: {current_spike:.1f}A spike", "warning")
                
                load_current = load_data["current"] + current_variation
                total_current += load_current
                
                # Calculate power for this load
                load_power = (base_voltage + voltage_variation) * load_current * load_data["power_factor"]
                total_power += load_power
        
        # Add background load
        background_current = random.uniform(5.0, 10.0)
        total_current += background_current
        background_power = (base_voltage + voltage_variation) * background_current * 0.9
        total_power += background_power
        
        # Simulate occasional power measurement errors
        if random.random() < 0.02:
            power_error = random.uniform(-0.1, 0.1) * total_power
            total_power += power_error
            self.log_alert(f"Power measurement error detected: {power_error:.1f}W error", "warning")
        
        # Ensure realistic bounds
        voltage = max(150, min(280, base_voltage + voltage_variation))
        current = max(0, min(800, total_current))
        power = max(0, min(200000, total_power))
        
        return {
            "voltage": round(voltage, 2),
            "current": round(current, 2),
            "power": round(power, 2),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def check_alerts(self, data):
        """Check for threshold violations and trigger alerts"""
        # Check voltage
        if data["voltage"] > self.voltage_threshold:
            self.log_alert(f"High Voltage Alert! {data['voltage']} V (Threshold: {self.voltage_threshold} V)", "warning")
            self.trigger_alert(f"High voltage warning: {data['voltage']} V")
        elif data["voltage"] < 180:
            self.log_alert(f"Low Voltage Alert! {data['voltage']} V (Minimum: 180 V)", "warning")
            self.trigger_alert(f"Low voltage warning: {data['voltage']} V")
        
        # Check current
        if data["current"] > self.current_threshold:
            self.log_alert(f"High Current Alert! {data['current']} A (Threshold: {self.current_threshold} A)", "warning")
            self.trigger_alert(f"High current warning: {data['current']} A")
        elif data["current"] < 0.1 and any(load["active"] for load in self.load_profiles.values()):
            self.log_alert(f"Low Current Alert! {data['current']} A (Expected higher with active loads)", "warning")
            self.trigger_alert(f"Low current warning: {data['current']} A")
        
        # Check power
        if data["power"] > self.power_threshold:
            self.log_alert(f"High Power Alert! {data['power']} W (Threshold: {self.power_threshold} W)", "warning")
            self.trigger_alert(f"High power warning: {data['power']} W")
        elif data["power"] < 50 and any(load["active"] for load in self.load_profiles.values()):
            self.log_alert(f"Low Power Alert! {data['power']} W (Expected higher with active loads)", "warning")
            self.trigger_alert(f"Low power warning: {data['power']} W")
        
        # Check energy budget
        if self.energy_consumption >= self.energy_budget * 0.9:
            if self.energy_consumption >= self.energy_budget:
                self.log_alert(f"Energy Budget Exceeded! {self.energy_consumption:.2f}/{self.energy_budget} kWh", "error")
                self.trigger_alert("Energy budget exceeded!")
            else:
                self.log_alert(f"Energy Budget Warning! {self.energy_consumption:.2f}/{self.energy_budget} kWh (90% threshold)", "warning")
                self.trigger_alert("Energy budget nearly exceeded!")
    
    def trigger_alert(self, message):
        """Trigger visual and audible alerts"""
        if self.alert_sounds:
            try:
                import winsound
                winsound.Beep(1000, 1000)
            except:
                pass
        
        if self.voice_alerts:
            try:
                import pyttsx3
                tts_engine = pyttsx3.init()
                tts_engine.say(message)
                tts_engine.runAndWait()
            except:
                pass
    
    def log_alert(self, message, level="info"):
        """Log an alert message"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"
        st.session_state.alerts.append(log_entry)
        
        # Limit alert history to 100 entries
        if len(st.session_state.alerts) > 100:
            st.session_state.alerts = st.session_state.alerts[-100:]
    
    def emergency_shutdown(self):
        """Turn off all loads"""
        for load_name in self.load_profiles:
            if self.load_profiles[load_name]["active"]:
                self.load_profiles[load_name]["active"] = False
                st.session_state[f"active_{load_name}"] = False
        
        self.log_alert("EMERGENCY SHUTDOWN ACTIVATED", "error")
        self.trigger_alert("Emergency shutdown activated!")
        st.rerun()
    
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
            # Generate timestamp for each data point
            time_step = UPDATE_INTERVAL  # seconds
            start_time = datetime.datetime.now() - datetime.timedelta(
                seconds=len(self.voltage_data) * time_step)
            
            data = []
            for i in range(len(self.voltage_data)):
                timestamp = (start_time + datetime.timedelta(seconds=i * time_step)).strftime("%Y-%m-%d %H:%M:%S")
                energy = sum(list(self.power_data)[:i+1]) / 1000 * (time_step / 3600)  # kWh
                
                data.append([
                    timestamp,
                    list(self.voltage_data)[i],
                    list(self.current_data)[i],
                    list(self.power_data)[i],
                    energy
                ])
            
            df = pd.DataFrame(data, columns=["timestamp", "voltage", "current", "power", "energy"])
            
            # Use Streamlit's download button
            st.download_button(
                label="Download Data as CSV",
                data=df.to_csv(index=False),
                file_name="load_management_data.csv",
                mime="text/csv"
            )
            
            self.log_alert("Data exported")
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
            "logging_enabled": self.logging_enabled,
            "alert_sounds": self.alert_sounds,
            "voice_alerts": self.voice_alerts
        }
        
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
                
                # Update thresholds
                self.voltage_threshold = config.get("voltage_threshold", 230.0)
                self.current_threshold = config.get("current_threshold", 150.0)
                self.power_threshold = config.get("power_threshold", 30000.0)
                self.energy_budget = config.get("energy_budget", 1000.0)
                
                # Update tariff rates
                self.tariff_rates = config.get("tariff_rates", self.tariff_rates)
                
                # Update load profiles
                self.load_profiles = config.get("load_profiles", self.load_profiles)
                
                # Update settings
                self.logging_enabled = config.get("logging_enabled", True)
                self.alert_sounds = config.get("alert_sounds", True)
                self.voice_alerts = config.get("voice_alerts", True)
                
                self.log_alert("Configuration loaded")
        except Exception as e:
            self.log_alert(f"Failed to load config: {str(e)}", "error")
    
    def clear_data(self):
        """Clear all monitoring data"""
        self.voltage_data.clear()
        self.current_data.clear()
        self.power_data.clear()
        self.energy_data.clear()
        self.energy_consumption = 0.0
        self.start_time = datetime.datetime.now()
        
        # Reset latest data
        st.session_state.latest_data = {
            "voltage": 0,
            "current": 0,
            "power": 0,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.log_alert("All monitoring data cleared", "info")
        st.rerun()

def main():
    st.set_page_config(
        page_title="MESCOM Load Management System",
        page_icon="⚡",
        layout="wide"
    )
    
    # Initialize system
    if 'system' not in st.session_state:
        st.session_state.system = LoadManagementSystem()
    
    system = st.session_state.system
    
    # Show appropriate interface based on authentication
    if not system.authenticated:
        system.create_login_page()
    else:
        system.create_main_interface()

if __name__ == "__main__":
    main()