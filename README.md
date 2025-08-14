# ⚡ Load Management System (Streamlit Version)

🔗 **[⬇️ Download Project Files (ZIP)](https://loadmanagementsystem.streamlit.app/?download=true)**  
🌐 **[Live Demo](https://loadmanagementsystem.streamlit.app/)**

A **real-time load monitoring and control system** built originally with **Tkinter GUI**, now migrated to a **Streamlit web application** for better accessibility, responsiveness, and interactive data visualization.

---

## 📌 Features

- **User Authentication**  
  Secure login with lockout mechanism after multiple failed attempts.

- **Real-Time Monitoring Dashboard**  
  Live voltage, current, power, energy consumption, and cost updates.

- **Load Control**  
  Switch individual loads ON/OFF, adjust current and power factor, emergency shutdown for all loads.

- **Energy & Cost Analysis**  
  Calculate total energy consumed, remaining budget, and estimated cost based on configurable tariff rates.

- **Alerts & Notifications**  
  Automatic alerts for voltage, current, power threshold breaches, and energy budget warnings.

- **Customizable Settings**  
  Modify thresholds, tariff rates, and save/load configuration.

- **Data Export**  
  Export historical monitoring data and alerts to CSV for further analysis.

- **Interactive Graphs**  
  Historical trends for voltage, current, power, and cumulative energy consumption.

---

## 🚀 Getting Started

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/load-management-system.git
cd load-management-system
```

### 2️⃣ Install Dependencies
Ensure you have Python 3.8+ installed. Then install required packages:
```bash
pip install -r requirements.txt
```

**Sample `requirements.txt`**
```txt
streamlit
pandas
matplotlib
```

### 3️⃣ Run the Application Locally
```bash
streamlit run app.py
```
The app will open in your default browser at `http://localhost:8501`.

---

## 🌐 Online Access
You can try the live app here:  
🔗 [Load Management System - Streamlit App](https://loadmanagementsystem.streamlit.app/)

---

## 🛠 Default Login Credentials
| Username | Password  |
|----------|-----------|
| admin    | password  |

---

## 📂 Project Structure
```
.
├── app.py               # Main application file
├── load_config.json     # Configuration file (auto-generated)
├── load_data_log.csv    # Logged monitoring data (auto-generated)
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

---

## ⚙️ Key Configurations
- **Thresholds:** Voltage, current, power, and energy budget.
- **Tariff Rates:** Peak, off-peak, and shoulder rates.
- **Load Profiles:** Name, current rating, power factor, and status.

---

## 📊 Example Use Cases
- **Industrial Power Management** – Monitor factory loads in real-time.
- **Building Energy Optimization** – Track and control office or campus energy use.
- **Educational Labs** – Demonstrate load management concepts to students.

---

## 📝 License
This project is licensed under the MIT License.

---

## ✨ Credits
- **Original Tkinter Version:** Developed for offline usage.
- **Streamlit Migration:** Interactive, browser-based version with improved UI/UX.

---
