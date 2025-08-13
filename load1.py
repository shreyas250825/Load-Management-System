import tkinter as tk
from tkinter import messagebox
import random
import requests

def fetch_data():
    """Fetch energy data from a simulated IoT platform or generate dummy data."""
    try:
        # Simulate fetching data from an IoT platform (e.g., ThingSpeak)
        # Uncomment the following lines for actual API integration
        # response = requests.get("<IoT Platform API URL>")
        # data = response.json()
        # Simulated data for demonstration purposes
        data = {
            "voltage": round(random.uniform(210, 240), 2),
            "current": round(random.uniform(0.5, 5.0), 2),
            "power": round(random.uniform(100, 1200), 2),
        }
        update_labels(data)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch data: {e}")

def update_labels(data):
    """Update the GUI labels with fetched data."""
    voltage_label.config(text=f"Voltage: {data['voltage']} V")
    current_label.config(text=f"Current: {data['current']} A")
    power_label.config(text=f"Power: {data['power']} W")

def toggle_load(load):
    """Toggle the state of a load (on/off)."""
    current_state = load_states[load]
    new_state = not current_state
    load_states[load] = new_state
    load_buttons[load].config(text=f"Load {load} {'ON' if new_state else 'OFF'}", bg="green" if new_state else "red")

# Initialize the main window
root = tk.Tk()
root.title("IoT-Based Energy Monitoring and Load Management")
root.geometry("400x400")

# Labels for energy parameters
voltage_label = tk.Label(root, text="Voltage: -- V", font=("Arial", 14))
voltage_label.pack(pady=10)

current_label = tk.Label(root, text="Current: -- A", font=("Arial", 14))
current_label.pack(pady=10)

power_label = tk.Label(root, text="Power: -- W", font=("Arial", 14))
power_label.pack(pady=10)

# Load control buttons
load_states = {1: False, 2: False, 3: False}  # Track the state of each load
load_buttons = {}
for i in range(1, 4):
    btn = tk.Button(
        root,
        text=f"Load {i} OFF",
        bg="red",
        fg="white",
        font=("Arial", 12),
        width=15,
        command=lambda i=i: toggle_load(i),
    )
    btn.pack(pady=5)
    load_buttons[i] = btn

# Fetch data button
fetch_button = tk.Button(root, text="Fetch Data", font=("Arial", 12), command=fetch_data)
fetch_button.pack(pady=20)

# Start the Tkinter main loop
root.mainloop()
