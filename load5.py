import tkinter as tk
from tkinter import messagebox
import random
import winsound
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from collections import deque

alert_active = False  # Flag to track alert sound status

def fetch_data():
    """Fetch energy data from a simulated IoT platform or generate dummy data."""
    try:
        data = {
            "voltage": round(random.uniform(210, 240), 2),
            "current": round(random.uniform(0.5, 5.0), 2),
            "power": round(random.uniform(100, 1200), 2),
        }
        update_labels(data)
        update_graphs(data)
        check_alerts(data)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch data: {e}")

def update_labels(data):
    """Update the GUI labels with fetched data."""
    voltage_label.config(text=f"Voltage: {data['voltage']} V")
    current_label.config(text=f"Current: {data['current']} A")
    power_label.config(text=f"Power: {data['power']} W")

def check_alerts(data):
    """Check if any parameter exceeds thresholds and trigger alerts."""
    voltage_threshold = float(voltage_threshold_entry.get())
    current_threshold = float(current_threshold_entry.get())
    power_threshold = float(power_threshold_entry.get())

    global alert_active  # To control continuous alert sound
    if data['voltage'] > voltage_threshold or \
       data['current'] > current_threshold or \
       data['power'] > power_threshold:
        if not alert_active:
            alert_active = True
            start_alert_sound()
        messagebox.showwarning("Alert", "Threshold Exceeded!")
    else:
        stop_alert_sound()

def start_alert_sound():
    """Start a continuous alert sound."""
    if alert_active:
        winsound.Beep(1000, 500)  # Frequency 1000Hz, 500ms duration
        root.after(500, start_alert_sound)  # Repeats the sound every 500ms

def stop_alert_sound():
    """Stop the alert sound."""
    global alert_active
    alert_active = False

def toggle_load(load):
    """Toggle the state of a load (on/off)."""
    current_state = load_states[load]
    new_state = not current_state
    load_states[load] = new_state
    load_buttons[load].config(text=f"Load {load} {'ON' if new_state else 'OFF'}", bg="green" if new_state else "red")

def update_graphs(data):
    """Update the graphs with new data."""
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
root.title("IoT-Based Energy Monitoring and Load Management")
root.geometry("800x800")

# Start button at the top
start_button = tk.Button(root, text="Start", font=("Arial", 14), command=fetch_data)
start_button.pack(pady=10)

# Frame for graphs
graph_frame = tk.Frame(root)
graph_frame.pack(fill=tk.BOTH, expand=True, pady=10)

# Graph setup
fig, (voltage_ax, current_ax, power_ax) = plt.subplots(3, 1, figsize=(5, 8))
fig.tight_layout(pad=3.0)

voltage_data = deque([0]*50, maxlen=50)
current_data = deque([0]*50, maxlen=50)
power_data = deque([0]*50, maxlen=50)

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

canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Frame for controls
control_frame = tk.Frame(root)
control_frame.pack(fill=tk.BOTH, pady=10)

# Labels for energy parameters
voltage_label = tk.Label(control_frame, text="Voltage: -- V", font=("Arial", 14))
voltage_label.grid(row=0, column=0, padx=5, pady=5)

current_label = tk.Label(control_frame, text="Current: -- A", font=("Arial", 14))
current_label.grid(row=1, column=0, padx=5, pady=5)

power_label = tk.Label(control_frame, text="Power: -- W", font=("Arial", 14))
power_label.grid(row=2, column=0, padx=5, pady=5)

# Threshold input fields
threshold_frame = tk.Frame(control_frame)
threshold_frame.grid(row=0, column=1, rowspan=3, padx=10, pady=5)

tk.Label(threshold_frame, text="Voltage Threshold (V):", font=("Arial", 12)).grid(row=0, column=0, padx=5)
voltage_threshold_entry = tk.Entry(threshold_frame, width=10, font=("Arial", 12))
voltage_threshold_entry.grid(row=0, column=1, padx=5)
voltage_threshold_entry.insert(0, "230")

tk.Label(threshold_frame, text="Current Threshold (A):", font=("Arial", 12)).grid(row=1, column=0, padx=5)
current_threshold_entry = tk.Entry(threshold_frame, width=10, font=("Arial", 12))
current_threshold_entry.grid(row=1, column=1, padx=5)
current_threshold_entry.insert(0, "4.5")

tk.Label(threshold_frame, text="Power Threshold (W):", font=("Arial", 12)).grid(row=2, column=0, padx=5)
power_threshold_entry = tk.Entry(threshold_frame, width=10, font=("Arial", 12))
power_threshold_entry.grid(row=2, column=1, padx=5)
power_threshold_entry.insert(0, "1000")

# Load control buttons
load_states = {1: False, 2: False, 3: False}  # Track the state of each load
load_buttons = {}
for i in range(1, 4):
    btn = tk.Button(
        control_frame,
        text=f"Load {i} OFF",
        bg="red",
        fg="white",
        font=("Arial", 12),
        width=15,
        command=lambda i=i: toggle_load(i),
    )
    btn.grid(row=i-1, column=2, padx=5, pady=5)
    load_buttons[i] = btn

# Start the Tkinter main loop
root.mainloop()
