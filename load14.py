import tkinter as tk
from tkinter import messagebox
import random
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from collections import deque
import pyttsx3  # Offline text-to-speech library
import winsound
import threading

# Initialize the text-to-speech engine
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 150)  # Set speaking speed

# Function to generate and play alert sounds and voice alerts
def speak_alert(message):
    try:
        # Play beep sound for alert
        winsound.Beep(1000, 1000)  # Frequency 1000 Hz for 1 second

        # Use pyttsx3 to speak the alert message
        tts_engine.say(message)
        tts_engine.runAndWait()
    except Exception as e:
        print(f"Error with text-to-speech: {e}")

# Function to fetch simulated data
def fetch_data():
    if running:
        data = {
            "voltage": round(random.uniform(210, 240), 2),
            "current": round(random.uniform(0.5, 5.0), 2),
            "power": round(random.uniform(100, 1200), 2),
        }
        update_labels(data)
        update_graphs(data)
        check_alerts(data)
        root.after(200, fetch_data)  # Fetch data every 200 ms

# Update displayed real-time values
def update_labels(data):
    voltage_real_value.config(text=f"{data['voltage']} V")
    current_real_value.config(text=f"{data['current']} A")
    power_real_value.config(text=f"{data['power']} W")

# Check if values exceed thresholds and trigger alerts
def check_alerts(data):
    voltage_threshold = float(voltage_threshold_entry.get())
    current_threshold = float(current_threshold_entry.get())
    power_threshold = float(power_threshold_entry.get())

    if data["voltage"] > voltage_threshold:
        alert_message = f"Voltage exceeded! Current: {data['voltage']} V"
        threading.Thread(target=speak_alert, args=(alert_message,)).start()
        messagebox.showwarning("Alert", alert_message)
    if data["current"] > current_threshold:
        alert_message = f"Current exceeded! Current: {data['current']} A"
        threading.Thread(target=speak_alert, args=(alert_message,)).start()
        messagebox.showwarning("Alert", alert_message)
    if data["power"] > power_threshold:
        alert_message = f"Power exceeded! Current: {data['power']} W"
        threading.Thread(target=speak_alert, args=(alert_message,)).start()
        messagebox.showwarning("Alert", alert_message)

# Update the graphs
def update_graphs(data):
    voltage_data.append(data["voltage"])
    current_data.append(data["current"])
    power_data.append(data["power"])

    voltage_line.set_ydata(voltage_data)
    current_line.set_ydata(current_data)
    power_line.set_ydata(power_data)

    voltage_ax.relim()
    voltage_ax.autoscale_view()
    current_ax.relim()
    current_ax.autoscale_view()
    power_ax.relim()
    power_ax.autoscale_view()

    canvas.draw()

# Start fetching data
def start_monitoring():
    global running
    running = True
    fetch_data()

# Stop fetching data
def stop_monitoring():
    global running
    running = False

# Toggle load on/off
def toggle_load(load_num):
    global voltage_adjustment

    if load_num == 1:
        load_button_1.config(text="Load 1 OFF" if load_status_1.get() == "ON" else "Load 1 ON")
        load_status_1.set("OFF" if load_status_1.get() == "ON" else "ON")
        voltage_adjustment -= 2 if load_status_1.get() == "OFF" else 0
    elif load_num == 2:
        load_button_2.config(text="Load 2 OFF" if load_status_2.get() == "ON" else "Load 2 ON")
        load_status_2.set("OFF" if load_status_2.get() == "ON" else "ON")
        voltage_adjustment -= 2 if load_status_2.get() == "OFF" else 0
    elif load_num == 3:
        load_button_3.config(text="Load 3 OFF" if load_status_3.get() == "ON" else "Load 3 ON")
        load_status_3.set("OFF" if load_status_3.get() == "ON" else "ON")
        voltage_adjustment -= 2 if load_status_3.get() == "OFF" else 0

# Initialize main window
root = tk.Tk()
root.title("IoT-Based Energy Monitoring with Alerts")
root.geometry("1200x800")

# Threshold input and real-time values
threshold_frame = tk.Frame(root)
threshold_frame.pack(pady=10)

tk.Label(threshold_frame, text="Voltage Threshold (V):", font=("Arial", 12)).grid(row=0, column=0, padx=5)
voltage_threshold_entry = tk.Entry(threshold_frame, width=10, font=("Arial", 12))
voltage_threshold_entry.grid(row=0, column=1, padx=5)
voltage_threshold_entry.insert(0, "230")
voltage_real_value = tk.Label(threshold_frame, text="-- V", font=("Arial", 12), fg="blue")
voltage_real_value.grid(row=0, column=2, padx=10)

tk.Label(threshold_frame, text="Current Threshold (A):", font=("Arial", 12)).grid(row=1, column=0, padx=5)
current_threshold_entry = tk.Entry(threshold_frame, width=10, font=("Arial", 12))
current_threshold_entry.grid(row=1, column=1, padx=5)
current_threshold_entry.insert(0, "4.5")
current_real_value = tk.Label(threshold_frame, text="-- A", font=("Arial", 12), fg="blue")
current_real_value.grid(row=1, column=2, padx=10)

tk.Label(threshold_frame, text="Power Threshold (W):", font=("Arial", 12)).grid(row=2, column=0, padx=5)
power_threshold_entry = tk.Entry(threshold_frame, width=10, font=("Arial", 12))
power_threshold_entry.grid(row=2, column=1, padx=5)
power_threshold_entry.insert(0, "1000")
power_real_value = tk.Label(threshold_frame, text="-- W", font=("Arial", 12), fg="blue")
power_real_value.grid(row=2, column=2, padx=10)

# Graph setup
fig, (voltage_ax, current_ax, power_ax) = plt.subplots(3, 1, figsize=(14, 8))
fig.tight_layout(pad=3.0)

voltage_data = deque([0] * 100, maxlen=100)
current_data = deque([0] * 100, maxlen=100)
power_data = deque([0] * 100, maxlen=100)

voltage_line, = voltage_ax.plot(voltage_data, label="Voltage (V)", color="blue")
current_line, = current_ax.plot(current_data, label="Current (A)", color="green")
power_line, = power_ax.plot(power_data, label="Power (W)", color="red")

voltage_ax.set_title("Voltage Over Time")
voltage_ax.set_ylabel("Voltage (V)")
voltage_ax.legend()

current_ax.set_title("Current Over Time")
current_ax.set_ylabel("Current (A)")
current_ax.legend()

power_ax.set_title("Power Over Time")
power_ax.set_ylabel("Power (W)")
power_ax.legend()

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Start and Stop buttons
control_frame = tk.Frame(root)
control_frame.pack(pady=10)

start_button = tk.Button(control_frame, text="Start Monitoring", font=("Arial", 12), bg="green", fg="white", command=start_monitoring)
start_button.grid(row=0, column=0, padx=10)

stop_button = tk.Button(control_frame, text="Stop Monitoring", font=("Arial", 12), bg="red", fg="white", command=stop_monitoring)
stop_button.grid(row=0, column=1, padx=10)

# Load Control buttons
load_control_frame = tk.Frame(root)
load_control_frame.pack(pady=10)

load_status_1 = tk.StringVar(value="OFF")
load_button_1 = tk.Button(load_control_frame, text="Load 1 ON", font=("Arial", 12), bg="blue", fg="white", command=lambda: toggle_load(1))
load_button_1.grid(row=0, column=0, padx=10)

load_status_2 = tk.StringVar(value="OFF")
load_button_2 = tk.Button(load_control_frame, text="Load 2 ON", font=("Arial", 12), bg="blue", fg="white", command=lambda: toggle_load(2))
load_button_2.grid(row=0, column=1, padx=10)

load_status_3 = tk.StringVar(value="OFF")
load_button_3 = tk.Button(load_control_frame, text="Load 3 ON", font=("Arial", 12), bg="blue", fg="white", command=lambda: toggle_load(3))
load_button_3.grid(row=0, column=2, padx=10)

# Variable to adjust voltage when loads are turned off
voltage_adjustment = 0

# Start the main loop
running = False
root.mainloop()
