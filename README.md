# 🖥️ IT Operations & Ticket Monitoring Dashboard

An interactive web-based dashboard built using **Python**, **Streamlit**, **Pandas**, and **Plotly** to track IT support tickets, engineer workload, system issues, and resolution rates in real time directly from a Google Sheet.

---

## 🌟 Key Features

- 🔄 **Real-Time Data Sync:** Automatically pulls live data from Google Sheets (`Form Responses` & `Open Ticket` sheets).
- 📊 **Interactive Metrics:** Visual representation of Total, Open, and Closed tickets alongside resolution rates.
- 👨‍💻 **Engineer Workload Analysis:** Parses multi-assigned tickets to attribute metrics to individual team members.
- 📈 **Trend Tracking & Issue Breakdown:** Monitors ticket trends over time and highlights top reported systems/issues.
- 🔍 **Dynamic Filtering:** Filter data dynamically by Ticket Status or Assigned Engineer.
- 📋 **Detailed Ticket Logs:** Clean table view of filtered raw ticket records.

---

## 🛠️ Tech Stack

- **Frontend/Framework:** [Streamlit](https://streamlit.io/)
- **Data Processing:** [Pandas](https://pandas.pydata.org/)
- **Data Visualization:** [Plotly Express](https://plotly.com/python/plotly-express/)
- **Data Source:** Google Sheets (CSV Export API)

---

## 🚀 Quick Start (Local Setup)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/OmniOrder223/it-operations-dashboard.git
   cd it-operations-dashboard
