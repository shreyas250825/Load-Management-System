import tkinter as tk
from tkinter import messagebox
import random
import winsound
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from collections import deque

fetching_data = False  # Control flag for start/stop
alert_active = False   # Control flag for alert sound

def fetch_data():
    """Fetch and update data."""
    if not fetching_data:
        return
    data = {
        "voltage": round(random.uniform(210, 240), 2),
        "current": round(random.uniform(0.5, 5.0), 2),
        "power": round(random.uniform(100, 1200), 2),
    }
    update_labels(data)
    update_graphs(data)
    check_alerts(data)
    root.after(1000, fetch_data)  # Update every second

def start_fetching():
    """Start data fetching."""
    global fetching_data
    fetching_data = True
    fetch_data()

def stop_fetching():
    """Stop data fetching."""
    global fetching_data
    fetching_data = False
    stop_alert_sound()

def update_labels(data):
    """Update the current values."""
    values_label.config(
        text=f"Current Values:\nVoltage: {data['voltage']} V\nCurrent: {data['current']} A\nPower: {data['power']} W"
    )


def check_alerts(data):
    """Check for threshold breaches and trigger alerts."""
    global alert_active
    voltage_threshold = float(voltage_threshold_entry.get())
    current_threshold = float(current_threshold_entry.get())
    power_threshold = float(power_threshold_entry.get())

    exceeded = []
    if data['voltage'] > voltage_threshold:
        exceeded.append(f"Voltage: {data['voltage']} V")
    if data['current'] > current_threshold:
        exceeded.append(f"Current: {data['current']} A")
    if data['power'] > power_threshold:
        exceeded.append(f"Power: {data['power']} W")

    if exceeded:
        if not alert_active:
            alert_active = True
            start_alert_sound()
        messagebox.showwarning("Threshold Alert", f"Exceeded Parameters:\n" + "\n".join(exceeded))
    else:
        stop_alert_sound()

def start_alert_sound():
    """Play alert sound."""
    if alert_active:
        winsound.Beep(1000, 500)  # Frequency 1000 Hz, duration 500 ms
        root.after(500, start_alert_sound)

def stop_alert_sound():
    """Stop alert sound."""
    global alert_active
    alert_active = False

def update_graphs(data):
    """Update graphs with new data."""
    voltage_data.append(data['voltage'])
    current_data.append(data['current'])
    power_data.append(data['power'])

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

# Initialize the main window
root = tk.Tk()
root.title("IoT-Based Energy Monitoring")
root.geometry("1200x800")  # Set extended dimensions

# Graphs setup
fig, (voltage_ax, current_ax, power_ax) = plt.subplots(3, 1, figsize=(12, 6))
fig.tight_layout(pad=3.0)

voltage_data = deque([0] * 50, maxlen=50)
current_data = deque([0] * 50, maxlen=50)
power_data = deque([0] * 50, maxlen=50)

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
canvas.get_tk_widget().pack(pady=10)

# Display current values in the top-right corner
values_label = tk.Label(root, text="Current Values:\nVoltage: -- V\nCurrent: -- A\nPower: -- W", font=("Arial", 12), justify=tk.LEFT)
values_label.place(relx=0.85, rely=0.05)

# Control buttons
control_frame = tk.Frame(root)
control_frame.pack(pady=10)

start_button = tk.Button(control_frame, text="Start", font=("Arial", 12), command=start_fetching)
start_button.grid(row=0, column=0, padx=10)

stop_button = tk.Button(control_frame, text="Stop", font=("Arial", 12), command=stop_fetching)
stop_button.grid(row=0, column=1, padx=10)

# Threshold input fields
threshold_frame = tk.Frame(root)
threshold_frame.pack(pady=10)

tk.Label(threshold_frame, text="Voltage Threshold (V):", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5)
voltage_threshold_entry = tk.Entry(threshold_frame, width=10, font=("Arial", 12))
voltage_threshold_entry.grid(row=0, column=1, padx=5, pady=5)
voltage_threshold_entry.insert(0, "230")

tk.Label(threshold_frame, text="Current Threshold (A):", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=5)
current_threshold_entry = tk.Entry(threshold_frame, width=10, font=("Arial", 12))
current_threshold_entry.grid(row=1, column=1, padx=5, pady=5)
current_threshold_entry.insert(0, "4.5")

tk.Label(threshold_frame, text="Power Threshold (W):", font=("Arial", 12)).grid(row=2, column=0, padx=5, pady=5)
power_threshold_entry = tk.Entry(threshold_frame, width=10, font=("Arial", 12))
power_threshold_entry.grid(row=2, column=1, padx=5, pady=5)
power_threshold_entry.insert(0, "1000")

# Start Tkinter event loop
root.mainloop()
