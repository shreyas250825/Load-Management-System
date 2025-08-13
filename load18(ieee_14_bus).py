import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import joblib

class LoadMonitoringSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("IoT-Based Energy Monitoring with Alerts")

        # Thresholds
        self.voltage_threshold = 230
        self.current_threshold = 4.5
        self.power_threshold = 1000

        # Running state
        self.running = False

        # Data storage
        self.data_log = []  # To store data for plotting

        # ML models
        self.anomaly_model = None
        self.forecasting_model = None
        self.scaler = None

        # GUI Elements
        self.setup_gui()
        self.setup_plot()
        
        # Load IEEE dataset
        self.load_ieee_data()

        # Load pre-trained models
        self.load_models()

    def setup_gui(self):
        frame = ttk.Frame(self.root)
        frame.pack(padx=10, pady=10, fill="x")

        # Threshold display
        ttk.Label(frame, text=f"Voltage Threshold (V): {self.voltage_threshold}").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text=f"Current Threshold (A): {self.current_threshold}").grid(row=1, column=0, sticky="w")
        ttk.Label(frame, text=f"Power Threshold (W): {self.power_threshold}").grid(row=2, column=0, sticky="w")

        # Start/Stop buttons
        self.start_button = ttk.Button(frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.grid(row=3, column=0, pady=10, sticky="w")

        self.stop_button = ttk.Button(frame, text="Stop Monitoring", command=self.stop_monitoring, state="disabled")
        self.stop_button.grid(row=3, column=1, pady=10, sticky="w")

        self.export_button = ttk.Button(frame, text="Export Data", command=self.export_data)
        self.export_button.grid(row=3, column=2, pady=10, sticky="w")

        # Anomaly Detection and Prediction
        self.anomaly_button = ttk.Button(frame, text="Run Anomaly Detection", command=self.run_anomaly_detection)
        self.anomaly_button.grid(row=4, column=0, pady=10, sticky="w")

        self.prediction_button = ttk.Button(frame, text="Predict Energy Usage", command=self.run_forecasting)
        self.prediction_button.grid(row=4, column=1, pady=10, sticky="w")

        # Data display
        self.data_frame = ttk.LabelFrame(self.root, text="Live Data")
        self.data_frame.pack(fill="x", padx=10, pady=10)

        self.voltage_label = ttk.Label(self.data_frame, text="Voltage (V): --")
        self.voltage_label.grid(row=0, column=0, padx=5, pady=5)

        self.current_label = ttk.Label(self.data_frame, text="Current (A): --")
        self.current_label.grid(row=0, column=1, padx=5, pady=5)

        self.power_label = ttk.Label(self.data_frame, text="Power (W): --")
        self.power_label.grid(row=0, column=2, padx=5, pady=5)

    def setup_plot(self):
        self.figure, self.axs = plt.subplots(3, 1, figsize=(5, 8))
        self.figure.tight_layout(pad=3.0)

        self.voltage_plot, = self.axs[0].plot([], [], label="Voltage (V)", color="blue")
        self.axs[0].set_title("Voltage Over Time")
        self.axs[0].set_ylabel("Voltage (V)")
        self.axs[0].legend()

        self.current_plot, = self.axs[1].plot([], [], label="Current (A)", color="green")
        self.axs[1].set_title("Current Over Time")
        self.axs[1].set_ylabel("Current (A)")
        self.axs[1].legend()

        self.power_plot, = self.axs[2].plot([], [], label="Power (W)", color="red")
        self.axs[2].set_title("Power Over Time")
        self.axs[2].set_ylabel("Power (W)")
        self.axs[2].legend()

        for ax in self.axs:
            ax.set_xlabel("Time (s)")

        self.canvas = FigureCanvasTkAgg(self.figure, self.root)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def load_ieee_data(self):
        """Load IEEE dataset for simulation."""
        self.ieee_data = [
            {"timestamp": "2023-01-01 00:00", "voltage": 240, "current": 5.0, "power": 1200},
            {"timestamp": "2023-01-01 01:00", "voltage": 230, "current": 4.8, "power": 1104},
            {"timestamp": "2023-01-01 02:00", "voltage": 220, "current": 5.2, "power": 1144},
            {"timestamp": "2023-01-01 03:00", "voltage": 250, "current": 5.5, "power": 1375},
            {"timestamp": "2023-01-01 04:00", "voltage": 230, "current": 4.2, "power": 966},
            {"timestamp": "2023-01-01 05:00", "voltage": 240, "current": 4.5, "power": 1080},
            {"timestamp": "2023-01-01 06:00", "voltage": 260, "current": 6.0, "power": 1560},
        ]

    def load_models(self):
        """Load pre-trained models for anomaly detection and forecasting."""
        try:
            self.anomaly_model = joblib.load("isolation_forest_model.pkl")
        except Exception:
            self.anomaly_model = None
        try:
            self.forecasting_model = joblib.load("lstm_model.h5")
        except Exception:
            self.forecasting_model = None
        try:
            self.scaler = joblib.load("scaler.pkl")
        except Exception:
            self.scaler = None

    def start_monitoring(self):
        self.running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.simulate_ieee_data()

    def stop_monitoring(self):
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def simulate_ieee_data(self):
        if self.running and self.ieee_data:
            data = self.ieee_data.pop(0)
            self.update_labels(data)
            self.check_alerts(data)
            self.log_data(data)
            self.update_plots(data)
            self.root.after(1000, self.simulate_ieee_data)

    def update_labels(self, data):
        self.voltage_label.config(text=f"Voltage (V): {data['voltage']}")
        self.current_label.config(text=f"Current (A): {data['current']}")
        self.power_label.config(text=f"Power (W): {data['power']}")

    def check_alerts(self, data):
        alerts = []
        if data['voltage'] > self.voltage_threshold:
            alerts.append("Voltage exceeds threshold!")
        if data['current'] > self.current_threshold:
            alerts.append("Current exceeds threshold!")
        if data['power'] > self.power_threshold:
            alerts.append("Power exceeds threshold!")

        if alerts:
            messagebox.showwarning("Alerts", "\n".join(alerts))

    def log_data(self, data):
        self.data_log.append(data)
        with open("energy_data.csv", "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([data['timestamp'], data['voltage'], data['current'], data['power']])

    def update_plots(self, data):
        times = list(range(len(self.data_log)))
        voltages = [entry['voltage'] for entry in self.data_log]
        currents = [entry['current'] for entry in self.data_log]
        powers = [entry['power'] for entry in self.data_log]

        self.voltage_plot.set_data(times, voltages)
        self.current_plot.set_data(times, currents)
        self.power_plot.set_data(times, powers)

        for ax, values in zip(self.axs, [voltages, currents, powers]):
            ax.set_xlim(0, len(times))
            ax.set_ylim(0, max(values) * 1.2 if values else 1)

        self.canvas.draw()

    def export_data(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            with open(file_path, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "Voltage (V)", "Current (A)", "Power (W)"])
                for entry in self.data_log:
                    writer.writerow([entry['timestamp'], entry['voltage'], entry['current'], entry['power']])
            messagebox.showinfo("Export Successful", f"Data exported to {file_path}")

    def run_anomaly_detection(self):
        """Run anomaly detection on the dataset. Trains a model if not loaded."""
        if not self.data_log:
            messagebox.showinfo("No Data", "No data available for anomaly detection.")
            return
        data_array = np.array([[entry['voltage'], entry['current'], entry['power']] for entry in self.data_log])
        # If model is not loaded, train a new one on the fly
        if self.anomaly_model is None:
            messagebox.showinfo("Training Model", "No pre-trained anomaly model found. Training a new model on current data.")
            self.anomaly_model = IsolationForest(contamination=0.15, random_state=42)
            self.anomaly_model.fit(data_array)
        try:
            predictions = self.anomaly_model.predict(data_array)
            anomalies = [i for i, pred in enumerate(predictions) if pred == -1]
            if anomalies:
                messagebox.showwarning("Anomalies Detected", f"Anomalies detected at indices: {anomalies}")
            else:
                messagebox.showinfo("No Anomalies", "No anomalies detected.")
        except Exception as e:
            messagebox.showerror("Anomaly Detection Error", f"An error occurred during anomaly detection: {e}")

    def run_forecasting(self):
        """Run energy usage forecasting."""
        if self.forecasting_model and self.data_log:
            data_array = np.array([[entry['voltage'], entry['current'], entry['power']] for entry in self.data_log])
            data_scaled = self.scaler.transform(data_array)

            # Use last 5 entries for prediction
            input_data = np.expand_dims(data_scaled[-5:], axis=0)
            prediction = self.forecasting_model.predict(input_data)
            predicted_power = self.scaler.inverse_transform(prediction)[0, 2]

            messagebox.showinfo("Forecast", f"Predicted next power usage: {predicted_power:.2f} W")

if __name__ == "__main__":
    root = tk.Tk()
    app = LoadMonitoringSystem(root)
    root.mainloop()