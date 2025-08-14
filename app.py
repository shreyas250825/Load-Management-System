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
        self.voltage_data = deque([220] * MAX_DATA_POINTS, maxlen=MAX_DATA_POINTS)
        self.current_data = deque([50] * MAX_DATA_POINTS, maxlen=MAX_DATA_POINTS)
        self.power_data = deque([11000] * MAX_DATA_POINTS, maxlen=MAX_DATA_POINTS)
        self.energy_data = deque([0] * MAX_DATA_POINTS, maxlen=MAX_DATA_POINTS)
        self.energy_consumption = 0.0
        self.start_time = datetime.datetime.now()
        
        # Thresholds
        self.voltage_threshold = 250.0
        self.current_threshold = 150.0
        self.power_threshold = 30000.0
        self.energy_budget = 1000.0
        
        # Tariff rates
        self.tariff_rates = {
            "peak": 5.75,
            "off_peak": 3.50,
            "shoulder": 4.25
        }
        
        # Settings
        self.logging_enabled = True
        self.alert_sounds = True
        self.voice_alerts = False
        
        # Alert control
        self.last_alert_time = {}
        self.alert_cooldown = 10  # seconds between similar alerts
        
        # Load configuration
        self.load_config()
        
        # Thread management
        self.data_thread = None
        self.thread_lock = threading.Lock()
        self.stop_event = threading.Event()

    def _init_session_state(self):
        """Initialize all required session state variables"""
        if 'system_initialized' not in st.session_state:
            st.session_state.system_initialized = True
            st.session_state.monitoring = False
            st.session_state.alerts = []
            st.session_state.latest_data = {
                "voltage": 220.0,
                "current": 50.0,
                "power": 11000.0,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.login_attempts = 0
            st.session_state.locked_out = False
            st.session_state.lockout_time = None
            st.session_state.data_update_counter = 0

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
        st.title("⚡ MESCOM Load Management System")
        st.markdown("---")
        
        with st.form("login_form"):
            st.subheader("🔐 Authentication Required")
            
            # Show default credentials
            st.info("**Default Login Credentials:**\n- Username: `admin`\n- Password: `password`")
            
            username = st.text_input("Username", value="admin", key="username")
            password = st.text_input("Password", value="password", key="password")
            
            if st.form_submit_button("🚀 Login", type="primary"):
                if self.authenticate(username, password):
                    st.success("✅ Login successful!")
                    time.sleep(1)
                    st.rerun()
    
    def create_main_interface(self):
        """Create main application interface"""
        st.title("⚡ MESCOM Load Management System")
        st.markdown(f"**Logged in as:** admin | **Status:** {'🟢 RUNNING' if st.session_state.monitoring else '🔴 STOPPED'}")
        st.markdown("---")
        
        # Create tabs
        tabs = st.tabs(["📊 Monitoring", "🎛️ Load Control", "💰 Energy & Cost", "⚠️ Alerts", "⚙️ Settings"])
        
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
        st.sidebar.markdown("### 📊 System Status")
        status_text = "RUNNING" if st.session_state.monitoring else "STOPPED"
        status_color = "green" if st.session_state.monitoring else "red"
        st.sidebar.markdown(f"**Monitoring:** :{status_color}[{status_text}]")
        st.sidebar.markdown("**System:** MESCOM Certified ✅")
        st.sidebar.markdown(f"**Data Updates:** {st.session_state.data_update_counter}")
        
        # Auto-refresh when monitoring
        if st.session_state.monitoring:
            time.sleep(1)
            st.rerun()
        
        # Logout button
        if st.sidebar.button("🚪 Logout", type="secondary"):
            self.stop_monitoring()
            self.authenticated = False
            st.rerun()
    
    def create_monitoring_tab(self):
        """Create the monitoring tab with graphs and real-time data"""
        st.header("📊 Real-time Monitoring Dashboard")
        
        # Monitoring Control Panel
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("▶️ Start Monitoring", type="primary", disabled=st.session_state.monitoring):
                self.start_monitoring()
        
        with col2:
            if st.button("⏸️ Stop Monitoring", type="secondary", disabled=not st.session_state.monitoring):
                self.stop_monitoring()
        
        with col3:
            if st.button("📥 Export Data"):
                self.export_data()
        
        with col4:
            if st.button("🗑️ Clear Data"):
                self.clear_data()
        
        # Real-time data display
        st.subheader("⚡ Live Electrical Parameters")
        data_col1, data_col2, data_col3, data_col4, data_col5 = st.columns(5)
        
        # Calculate current rate and cost
        current_hour = datetime.datetime.now().hour
        if 8 <= current_hour < 20:  # Peak hours
            rate = self.tariff_rates["peak"]
            period = "Peak (8AM-8PM)"
        elif 0 <= current_hour < 6:  # Off-peak hours
            rate = self.tariff_rates["off_peak"]
            period = "Off-Peak (12AM-6AM)"
        else:  # Shoulder hours
            rate = self.tariff_rates["shoulder"]
            period = "Shoulder"
        
        cost = self.energy_consumption * rate
        
        with data_col1:
            voltage = st.session_state.latest_data['voltage']
            delta_v = "normal" if 200 <= voltage <= 250 else "inverse"
            st.metric("Voltage", f"{voltage} V", delta=f"{voltage-230:.1f}V", delta_color=delta_v)
        
        with data_col2:
            current = st.session_state.latest_data['current']
            delta_c = "normal" if current <= 100 else "inverse"
            st.metric("Current", f"{current} A", delta=f"{current-50:.1f}A", delta_color=delta_c)
        
        with data_col3:
            power = st.session_state.latest_data['power']
            delta_p = "normal" if power <= 20000 else "inverse"
            st.metric("Power", f"{power:.0f} W", delta=f"{power-11000:.0f}W", delta_color=delta_p)
        
        with data_col4:
            st.metric("Energy", f"{self.energy_consumption:.3f} kWh", delta=f"Budget: {self.energy_budget:.1f} kWh")
        
        with data_col5:
            st.metric("Cost", f"₹{cost:.2f}", delta=f"Rate: ₹{rate}/kWh")
            st.caption(f"Period: {period}")
        
        # System status indicators
        st.subheader("🔍 System Health")
        health_col1, health_col2, health_col3, health_col4 = st.columns(4)
        
        with health_col1:
            v_status = "🟢 Normal" if 200 <= voltage <= 250 else "🔴 Alert"
            st.metric("Voltage Status", v_status)
        
        with health_col2:
            c_status = "🟢 Normal" if current <= self.current_threshold else "🔴 High"
            st.metric("Current Status", c_status)
        
        with health_col3:
            p_status = "🟢 Normal" if power <= self.power_threshold else "🔴 High"
            st.metric("Power Status", p_status)
        
        with health_col4:
            e_status = "🟢 OK" if self.energy_consumption < self.energy_budget * 0.9 else "🟡 Near Limit" if self.energy_consumption < self.energy_budget else "🔴 Exceeded"
            st.metric("Energy Status", e_status)
        
        # Create graphs
        self.create_graphs()
        
        # Last update info
        st.caption(f"Last updated: {st.session_state.latest_data['timestamp']} | Updates: {st.session_state.data_update_counter}")
    
    def create_graphs(self):
        """Create the monitoring graphs"""
        st.subheader("📈 Historical Trends")
        
        # Create three separate graphs in tabs for better visibility
        graph_tabs = st.tabs(["🔌 Voltage", "⚡ Current", "🔥 Power"])
        
        with graph_tabs[0]:
            fig1, ax1 = plt.subplots(figsize=(12, 4))
            ax1.plot(list(self.voltage_data), label="Voltage (V)", color="blue", linewidth=2)
            ax1.axhline(y=self.voltage_threshold, color='red', linestyle='--', alpha=0.7, label=f"Threshold ({self.voltage_threshold}V)")
            ax1.axhline(y=230, color='green', linestyle='--', alpha=0.7, label="Nominal (230V)")
            ax1.set_title("Voltage Over Time", fontsize=14, fontweight='bold')
            ax1.set_ylabel("Voltage (V)")
            ax1.set_xlabel("Time (samples)")
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(150, 300)
            st.pyplot(fig1)
        
        with graph_tabs[1]:
            fig2, ax2 = plt.subplots(figsize=(12, 4))
            ax2.plot(list(self.current_data), label="Current (A)", color="orange", linewidth=2)
            ax2.axhline(y=self.current_threshold, color='red', linestyle='--', alpha=0.7, label=f"Threshold ({self.current_threshold}A)")
            ax2.set_title("Current Over Time", fontsize=14, fontweight='bold')
            ax2.set_ylabel("Current (A)")
            ax2.set_xlabel("Time (samples)")
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            st.pyplot(fig2)
        
        with graph_tabs[2]:
            fig3, ax3 = plt.subplots(figsize=(12, 4))
            ax3.plot(list(self.power_data), label="Power (W)", color="red", linewidth=2)
            ax3.axhline(y=self.power_threshold, color='red', linestyle='--', alpha=0.7, label=f"Threshold ({self.power_threshold}W)")
            ax3.set_title("Power Over Time", fontsize=14, fontweight='bold')
            ax3.set_ylabel("Power (W)")
            ax3.set_xlabel("Time (samples)")
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            st.pyplot(fig3)
    
    def create_control_tab(self):
        """Create the load control tab"""
        st.header("🎛️ Load Management Controls")
        
        # Load status overview
        st.subheader("📋 Load Status Overview")
        overview_cols = st.columns(len(self.load_profiles))
        
        for i, (load_name, load_data) in enumerate(self.load_profiles.items()):
            with overview_cols[i]:
                status_icon = "🟢" if load_data["active"] else "🔴"
                st.metric(
                    f"{status_icon} {load_name}", 
                    f"{load_data['current']:.0f}A",
                    delta="ACTIVE" if load_data["active"] else "OFF"
                )
        
        st.markdown("---")
        
        # Create load control widgets for each load profile
        for load_name, load_data in self.load_profiles.items():
            with st.expander(f"🔧 {load_name} Controls", expanded=load_data["active"]):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    status = st.checkbox(
                        f"🔌 Active", 
                        value=load_data["active"], 
                        key=f"active_{load_name}",
                        on_change=self.update_load_status,
                        args=(load_name,)
                    )
                
                with col2:
                    current = st.number_input(
                        "⚡ Current (A)",
                        min_value=0.0,
                        max_value=500.0,
                        value=float(load_data["current"]),
                        step=10.0,
                        key=f"current_{load_name}",
                        on_change=self.update_load_current,
                        args=(load_name,)
                    )
                
                with col3:
                    pf = st.slider(
                        "📊 Power Factor",
                        min_value=0.1,
                        max_value=1.0,
                        value=float(load_data["power_factor"]),
                        step=0.05,
                        key=f"pf_{load_name}",
                        on_change=self.update_load_pf,
                        args=(load_name,)
                    )
                
                # Show calculated power for this load
                if load_data["active"]:
                    calc_power = 230 * load_data["current"] * load_data["power_factor"]
                    st.info(f"💡 Estimated Power: {calc_power:.0f} W")
        
        # Emergency shutdown button
        st.markdown("---")
        st.subheader("🚨 Emergency Controls")
        if st.button("🛑 EMERGENCY SHUTDOWN ALL LOADS", type="primary", use_container_width=True):
            self.emergency_shutdown()
    
    def update_load_status(self, load_name):
        """Update load status from UI"""
        self.load_profiles[load_name]["active"] = st.session_state[f"active_{load_name}"]
        status = "ON" if self.load_profiles[load_name]["active"] else "OFF"
        self.log_alert(f"Load '{load_name}' turned {status}", "info")
    
    def update_load_current(self, load_name):
        """Update load current from UI"""
        self.load_profiles[load_name]["current"] = st.session_state[f"current_{load_name}"]
        self.log_alert(f"Load '{load_name}' current updated to {self.load_profiles[load_name]['current']} A", "info")
    
    def update_load_pf(self, load_name):
        """Update load power factor from UI"""
        self.load_profiles[load_name]["power_factor"] = st.session_state[f"pf_{load_name}"]
        self.log_alert(f"Load '{load_name}' power factor updated to {self.load_profiles[load_name]['power_factor']}", "info")
    
    def create_energy_tab(self):
        """Create the energy consumption and cost tab"""
        st.header("💰 Energy Consumption Analysis")
        
        # Energy summary
        st.subheader("📊 Energy Summary")
        col1, col2, col3 = st.columns(3)
        
        # Calculate current rate and cost
        current_hour = datetime.datetime.now().hour
        if 8 <= current_hour < 20:  # Peak hours
            rate = self.tariff_rates["peak"]
            period = "Peak Hours (8AM-8PM)"
        elif 0 <= current_hour < 6:  # Off-peak hours
            rate = self.tariff_rates["off_peak"]
            period = "Off-Peak Hours (12AM-6AM)"
        else:  # Shoulder hours
            rate = self.tariff_rates["shoulder"]
            period = "Shoulder Hours (6AM-8AM, 8PM-12AM)"
        
        cost = self.energy_consumption * rate
        
        with col1:
            st.metric("Total Energy Consumed", f"{self.energy_consumption:.3f} kWh")
            st.metric("Estimated Cost", f"₹{cost:.2f}")
        
        with col2:
            budget_remaining = max(0, self.energy_budget - self.energy_consumption)
            budget_percent = (self.energy_consumption / self.energy_budget * 100) if self.energy_budget > 0 else 0
            
            st.metric("Energy Budget Remaining", f"{budget_remaining:.2f} kWh")
            st.metric("Budget Used", f"{budget_percent:.1f}%")
            
            # Progress bar for budget
            st.progress(min(budget_percent / 100, 1.0))
            
            # Time remaining estimate
            if self.energy_consumption > 0 and budget_remaining > 0:
                runtime = (datetime.datetime.now() - self.start_time).total_seconds() / 3600
                if runtime > 0:
                    consumption_rate = self.energy_consumption / runtime
                    if consumption_rate > 0:
                        hours_remaining = budget_remaining / consumption_rate
                        st.metric("Est. Time Remaining", f"{hours_remaining:.1f} hours")
        
        with col3:
            st.metric("Current Tariff Rate", f"₹{rate:.2f}/kWh")
            st.metric("Current Period", period)
            
            # Show next rate change
            next_change_hour = None
            if current_hour < 6:
                next_change_hour = 6
                next_period = "Shoulder"
            elif current_hour < 8:
                next_change_hour = 8
                next_period = "Peak"
            elif current_hour < 20:
                next_change_hour = 20
                next_period = "Shoulder"
            else:
                next_change_hour = 24
                next_period = "Off-Peak"
            
            if next_change_hour:
                hours_until_change = next_change_hour - current_hour
                if hours_until_change < 0:
                    hours_until_change += 24
                st.metric("Next Rate Change", f"{hours_until_change}h to {next_period}")
        
        # Tariff settings
        st.subheader("💸 Tariff Configuration")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self.tariff_rates["peak"] = st.number_input(
                "Peak Hours (8AM-8PM)",
                value=float(self.tariff_rates["peak"]),
                step=0.25,
                format="%.2f",
                key="peak_rate"
            )
        
        with col2:
            self.tariff_rates["off_peak"] = st.number_input(
                "Off-Peak Hours (12AM-6AM)",
                value=float(self.tariff_rates["off_peak"]),
                step=0.25,
                format="%.2f",
                key="off_peak_rate"
            )
        
        with col3:
            self.tariff_rates["shoulder"] = st.number_input(
                "Shoulder Hours (6AM-8AM, 8PM-12AM)",
                value=float(self.tariff_rates["shoulder"]),
                step=0.25,
                format="%.2f",
                key="shoulder_rate"
            )
        
        if st.button("💾 Update Tariff Rates"):
            self.log_alert("Tariff rates updated", "info")
            self.save_config()
            st.success("Tariff rates updated successfully!")
        
        # Energy history graph
        st.subheader("📈 Energy Consumption History")
        energy_fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(list(self.energy_data), label="Energy Consumption (kWh)", color="purple", linewidth=2)
        ax.axhline(y=self.energy_budget, color='red', linestyle='--', alpha=0.7, label=f"Budget ({self.energy_budget} kWh)")
        ax.set_xlabel("Time (samples)")
        ax.set_ylabel("Energy (kWh)")
        ax.set_title("Cumulative Energy Consumption", fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(energy_fig)
    
    def create_alerts_tab(self):
        """Create the alerts history tab"""
        st.header("⚠️ Alert History & Management")
        
        # Alert summary
        if st.session_state.alerts:
            error_count = sum(1 for alert in st.session_state.alerts if "ERROR" in alert)
            warning_count = sum(1 for alert in st.session_state.alerts if "WARNING" in alert)
            info_count = len(st.session_state.alerts) - error_count - warning_count
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🔴 Errors", error_count)
            with col2:
                st.metric("🟡 Warnings", warning_count)
            with col3:
                st.metric("ℹ️ Info", info_count)
            with col4:
                st.metric("📝 Total", len(st.session_state.alerts))
        
        # Control buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All Alerts"):
                st.session_state.alerts = []
                self.log_alert("Alert history cleared", "info")
                st.rerun()
        
        with col2:
            if st.button("📥 Export Alerts"):
                if st.session_state.alerts:
                    alert_df = pd.DataFrame(st.session_state.alerts, columns=["Alert"])
                    st.download_button(
                        label="Download Alerts as CSV",
                        data=alert_df.to_csv(index=False),
                        file_name=f"alerts_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
        
        st.markdown("---")
        
        # Display alerts in reverse order (newest first)
        st.subheader("📋 Recent Alerts")
        if st.session_state.alerts:
            for i, alert in enumerate(reversed(st.session_state.alerts[-20:])):  # Show last 20 alerts
                if "ERROR" in alert:
                    st.error(f"🔴 {alert}")
                elif "WARNING" in alert:
                    st.warning(f"🟡 {alert}")
                else:
                    st.info(f"ℹ️ {alert}")
        else:
            st.info("No alerts to display.")
    
    def create_settings_tab(self):
        """Create the system settings tab"""
        st.header("⚙️ System Configuration")
        
        # Threshold settings
        st.subheader("🚨 Alert Thresholds")
        
        threshold_col1, threshold_col2 = st.columns(2)
        
        with threshold_col1:
            self.voltage_threshold = st.number_input(
                "🔌 Voltage Threshold (V)",
                min_value=200.0,
                max_value=300.0,
                value=float(self.voltage_threshold),
                step=5.0,
                key="voltage_threshold"
            )
            
            self.current_threshold = st.number_input(
                "⚡ Current Threshold (A)",
                min_value=50.0,
                max_value=500.0,
                value=float(self.current_threshold),
                step=10.0,
                key="current_threshold"
            )
        
        with threshold_col2:
            self.power_threshold = st.number_input(
                "🔥 Power Threshold (W)",
                min_value=10000.0,
                max_value=100000.0,
                value=float(self.power_threshold),
                step=1000.0,
                key="power_threshold"
            )
            
            self.energy_budget = st.number_input(
                "🔋 Energy Budget (kWh)",
                min_value=100.0,
                max_value=10000.0,
                value=float(self.energy_budget),
                step=100.0,
                key="energy_budget"
            )
        
        # Alert cooldown setting
        st.subheader("⏰ Alert Settings")
        self.alert_cooldown = st.slider(
            "Alert Cooldown (seconds)",
            min_value=5,
            max_value=60,
            value=self.alert_cooldown,
            help="Minimum time between similar alerts"
        )
        
        if st.button("💾 Update Thresholds"):
            self.log_alert("Alert thresholds updated", "info")
            self.save_config()
            st.success("Thresholds updated successfully!")
        
        # System settings
        st.subheader("🔧 System Settings")
        
        settings_col1, settings_col2 = st.columns(2)
        
        with settings_col1:
            self.logging_enabled = st.checkbox(
                "📝 Enable Data Logging",
                value=bool(self.logging_enabled),
                key="logging_enabled"
            )
            
            self.alert_sounds = st.checkbox(
                "🔊 Enable Alert Sounds",
                value=bool(self.alert_sounds),
                key="alert_sounds"
            )
        
        with settings_col2:
            self.voice_alerts = st.checkbox(
                "🗣️ Enable Voice Alerts",
                value=bool(self.voice_alerts),
                key="voice_alerts"
            )
        
        # Configuration management
        st.subheader("💾 Configuration Management")
        config_col1, config_col2, config_col3 = st.columns(3)
        
        with config_col1:
            if st.button("💾 Save Configuration"):
                self.save_config()
                st.success("Configuration saved!")
        
        with config_col2:
            if st.button("📂 Load Configuration"):
                self.load_config()
                st.success("Configuration loaded!")
                st.rerun()
        
        with config_col3:
            if st.button("🔄 Reset to Defaults"):
                self.reset_to_defaults()
                st.success("Reset to default settings!")
                st.rerun()
    
    def reset_to_defaults(self):
        """Reset all settings to default values"""
        self.voltage_threshold = 250.0
        self.current_threshold = 150.0
        self.power_threshold = 30000.0
        self.energy_budget = 1000.0
        self.tariff_rates = {"peak": 5.75, "off_peak": 3.50, "shoulder": 4.25}
        self.alert_cooldown = 10
        self.log_alert("System reset to default settings", "info")
    
    def start_monitoring(self):
        """Start the monitoring process"""
        if not st.session_state.monitoring:
            st.session_state.monitoring = True
            self.running = True
            self.stop_event.clear()
            
            if self.data_thread is None or not self.data_thread.is_alive():
                self.data_thread = threading.Thread(target=self._data_collection_loop_wrapper, daemon=True)
                self.data_thread.start()
            
            self.log_alert("🟢 Monitoring started", "info")
            st.success("✅ Monitoring started successfully!")
            st.rerun()
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        if st.session_state.monitoring:
            st.session_state.monitoring = False
            self.running = False
            self.stop_event.set()
            
            # Wait for thread to finish
            if self.data_thread and self.data_thread.is_alive():
                self.data_thread.join(timeout=2.0)
            
            self.log_alert("🔴 Monitoring stopped", "info")
            st.success("⏹️ Monitoring stopped successfully!")
            st.rerun()
    
    def _data_collection_loop_wrapper(self):
        """Wrapper for data collection loop to handle thread safety"""
        try:
            while self.running and not self.stop_event.is_set():
                if st.session_state.monitoring:
                    self.data_collection_loop()
                time.sleep(UPDATE_INTERVAL)
        except Exception as e:
            self.log_alert_safe(f"Data collection error: {str(e)}", "error")
    
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
            
            # Update session state safely
            with self.thread_lock:
                st.session_state.latest_data = data
                st.session_state.data_update_counter += 1
            
            # Log data if enabled
            if self.logging_enabled:
                self.log_data(data)
            
            # Check for alerts
            self.check_alerts(data)
            
        except Exception as e:
            self.log_alert_safe(f"System Error: {str(e)}", "error")
    
    def simulate_realistic_data(self):
        """Generate realistic load data with occasional errors and spikes"""
        # Base values
        base_voltage = 230.0
        voltage_variation = random.uniform(-5, 5)
        
        # Calculate total current based on active loads
        total_current = 0.0
        total_power = 0.0
        
        # Simulate occasional voltage spikes or drops (less frequent)
        if random.random() < 0.01:  # 1% chance
            voltage_spike_or_drop = random.uniform(-30, 30)
            voltage_variation += voltage_spike_or_drop
            self.log_alert_safe(f"Voltage fluctuation detected: {voltage_spike_or_drop:.1f}V", "warning")
        
        for load_name, load_data in self.load_profiles.items():
            if load_data["active"]:
                # Add realistic variation
                current_variation = random.uniform(-0.1, 0.1) * load_data["current"]
                
                # Simulate occasional current spikes (rare)
                if random.random() < 0.005:  # 0.5% chance
                    current_spike = random.uniform(10.0, 30.0)
                    current_variation += current_spike
                    self.log_alert_safe(f"Current spike in {load_name}: +{current_spike:.1f}A", "warning")
                
                load_current = max(0, load_data["current"] + current_variation)
                total_current += load_current
                
                # Calculate power for this load
                load_voltage = base_voltage + voltage_variation
                load_power = load_voltage * load_current * load_data["power_factor"]
                total_power += load_power
        
        # Add background load (always present)
        background_current = random.uniform(3.0, 8.0)
        total_current += background_current
        background_power = (base_voltage + voltage_variation) * background_current * 0.92
        total_power += background_power
        
        # Ensure realistic bounds
        voltage = max(180, min(270, base_voltage + voltage_variation))
        current = max(0, min(600, total_current))
        power = max(0, min(150000, total_power))
        
        return {
            "voltage": round(voltage, 1),
            "current": round(current, 1),
            "power": round(power, 0),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def check_alerts(self, data):
        """Check for threshold violations and trigger alerts with cooldown"""
        current_time = time.time()
        
        # Check voltage alerts
        if data["voltage"] > self.voltage_threshold:
            if self.should_trigger_alert("high_voltage", current_time):
                self.log_alert_safe(f"⚠️ HIGH VOLTAGE: {data['voltage']}V (Limit: {self.voltage_threshold}V)", "warning")
                self.trigger_alert(f"High voltage: {data['voltage']} volts")
                
        elif data["voltage"] < 200:
            if self.should_trigger_alert("low_voltage", current_time):
                self.log_alert_safe(f"⚠️ LOW VOLTAGE: {data['voltage']}V (Minimum: 200V)", "warning")
                self.trigger_alert(f"Low voltage: {data['voltage']} volts")
        
        # Check current alerts
        if data["current"] > self.current_threshold:
            if self.should_trigger_alert("high_current", current_time):
                self.log_alert_safe(f"⚠️ HIGH CURRENT: {data['current']}A (Limit: {self.current_threshold}A)", "warning")
                self.trigger_alert(f"High current: {data['current']} amperes")
        
        # Check power alerts
        if data["power"] > self.power_threshold:
            if self.should_trigger_alert("high_power", current_time):
                self.log_alert_safe(f"⚠️ HIGH POWER: {data['power']}W (Limit: {self.power_threshold}W)", "warning")
                self.trigger_alert(f"High power: {data['power']} watts")
        
        # Check energy budget alerts
        budget_usage = (self.energy_consumption / self.energy_budget) * 100 if self.energy_budget > 0 else 0
        
        if budget_usage >= 100:
            if self.should_trigger_alert("budget_exceeded", current_time):
                self.log_alert_safe(f"🚨 ENERGY BUDGET EXCEEDED: {self.energy_consumption:.2f}/{self.energy_budget} kWh", "error")
                self.trigger_alert("Energy budget exceeded!")
        elif budget_usage >= 90:
            if self.should_trigger_alert("budget_warning", current_time):
                self.log_alert_safe(f"⚠️ ENERGY BUDGET WARNING: {budget_usage:.1f}% used", "warning")
                self.trigger_alert("Energy budget nearly exceeded!")
        
        # Voltage stability check
        if len(self.voltage_data) >= 10:
            recent_voltages = list(self.voltage_data)[-10:]
            voltage_std = pd.Series(recent_voltages).std()
            if voltage_std > 15:  # High voltage instability
                if self.should_trigger_alert("voltage_instability", current_time):
                    self.log_alert_safe(f"⚠️ VOLTAGE INSTABILITY: Std dev {voltage_std:.1f}V", "warning")
                    self.trigger_alert("Voltage instability detected")
    
    def should_trigger_alert(self, alert_type, current_time):
        """Check if enough time has passed since last alert of this type"""
        if alert_type not in self.last_alert_time:
            self.last_alert_time[alert_type] = current_time
            return True
        
        time_since_last = current_time - self.last_alert_time[alert_type]
        if time_since_last >= self.alert_cooldown:
            self.last_alert_time[alert_type] = current_time
            return True
        
        return False
    
    def trigger_alert(self, message):
        """Trigger visual and audible alerts"""
        if self.alert_sounds:
            try:
                import winsound
                winsound.Beep(800, 500)  # Shorter beep
            except ImportError:
                pass
        
        if self.voice_alerts:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)
                engine.say(message)
                engine.runAndWait()
            except ImportError:
                pass
    
    def log_alert_safe(self, message, level="info"):
        """Thread-safe version of log_alert"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"
        
        with self.thread_lock:
            try:
                st.session_state.alerts.append(log_entry)
                # Limit alert history to 200 entries
                if len(st.session_state.alerts) > 200:
                    st.session_state.alerts = st.session_state.alerts[-200:]
            except:
                pass  # Gracefully handle session state access issues
    
    def log_alert(self, message, level="info"):
        """Log an alert message"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"
        st.session_state.alerts.append(log_entry)
        
        # Limit alert history to 200 entries
        if len(st.session_state.alerts) > 200:
            st.session_state.alerts = st.session_state.alerts[-200:]
    
    def emergency_shutdown(self):
        """Turn off all loads"""
        shutdown_count = 0
        for load_name in self.load_profiles:
            if self.load_profiles[load_name]["active"]:
                self.load_profiles[load_name]["active"] = False
                st.session_state[f"active_{load_name}"] = False
                shutdown_count += 1
        
        self.log_alert(f"🚨 EMERGENCY SHUTDOWN: {shutdown_count} loads deactivated", "error")
        self.trigger_alert(f"Emergency shutdown activated! {shutdown_count} loads turned off!")
        st.error(f"🚨 Emergency shutdown completed! {shutdown_count} loads deactivated.")
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
            self.log_alert_safe(f"Failed to log data: {str(e)}", "error")
    
    def export_data(self):
        """Export data to a CSV file"""
        try:
            # Generate timestamp for each data point
            time_step = UPDATE_INTERVAL  # seconds
            now = datetime.datetime.now()
            
            data = []
            for i in range(len(self.voltage_data)):
                timestamp = (now - datetime.timedelta(seconds=(len(self.voltage_data)-i-1) * time_step))
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                
                data.append([
                    timestamp_str,
                    list(self.voltage_data)[i],
                    list(self.current_data)[i],
                    list(self.power_data)[i],
                    list(self.energy_data)[i] if i < len(self.energy_data) else 0
                ])
            
            df = pd.DataFrame(data, columns=["timestamp", "voltage", "current", "power", "energy"])
            
            # Use Streamlit's download button
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv_data,
                file_name=f"load_management_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            self.log_alert("📊 Data exported successfully", "info")
            st.success(f"✅ Data exported! {len(data)} records ready for download.")
        except Exception as e:
            self.log_alert(f"Export failed: {str(e)}", "error")
            st.error(f"❌ Export failed: {str(e)}")
    
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
            "voice_alerts": self.voice_alerts,
            "alert_cooldown": self.alert_cooldown
        }
        
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            self.log_alert("💾 Configuration saved", "info")
        except Exception as e:
            self.log_alert(f"Save failed: {str(e)}", "error")
    
    def load_config(self):
        """Load system configuration from file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                
                # Update thresholds
                self.voltage_threshold = config.get("voltage_threshold", 250.0)
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
                self.alert_cooldown = config.get("alert_cooldown", 10)
                
                self.log_alert("📂 Configuration loaded", "info")
        except Exception as e:
            self.log_alert(f"Failed to load config: {str(e)}", "error")
    
    def clear_data(self):
        """Clear all monitoring data"""
        # Initialize with some baseline data instead of zeros
        self.voltage_data = deque([230] * MAX_DATA_POINTS, maxlen=MAX_DATA_POINTS)
        self.current_data = deque([50] * MAX_DATA_POINTS, maxlen=MAX_DATA_POINTS)
        self.power_data = deque([11500] * MAX_DATA_POINTS, maxlen=MAX_DATA_POINTS)
        self.energy_data = deque([0] * MAX_DATA_POINTS, maxlen=MAX_DATA_POINTS)
        self.energy_consumption = 0.0
        self.start_time = datetime.datetime.now()
        
        # Reset latest data
        st.session_state.latest_data = {
            "voltage": 230.0,
            "current": 50.0,
            "power": 11500.0,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.data_update_counter = 0
        
        self.log_alert("🗑️ All monitoring data cleared", "info")
        st.success("✅ Monitoring data cleared successfully!")
        st.rerun()

def main():
    st.set_page_config(
        page_title="MESCOM Load Management System",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better appearance
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric > label {
        font-size: 14px !important;
        font-weight: 600 !important;
    }
    .stAlert > div {
        padding: 0.5rem 1rem;
    }
    div[data-testid="stExpander"] > summary {
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)
    
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