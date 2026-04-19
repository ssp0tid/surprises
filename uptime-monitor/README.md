# Uptime Monitor

A complete self-hosted URL uptime monitoring micro SaaS utility.

## ✨ Features

- ✅ Add unlimited URLs to monitor
- ✅ Automatic checks every 60 seconds
- ✅ Uptime percentage tracking
- ✅ Response time logging
- ✅ Status history records
- ✅ Console alerts when sites go down
- ✅ Clean modern web interface
- ✅ No external services required
- ✅ Single command installation & run
- ✅ SQLite database storage
- ✅ FastAPI backend

## 🚀 Quick Start

Run with single command:
```bash
./run.sh
```

Or manually:
```bash
pip install -r requirements.txt
python main.py
```

Then open your browser: **http://localhost:8000**

## 🛠️ Technology Stack

- **Backend**: FastAPI / Python
- **Frontend**: Vanilla JavaScript + CSS3
- **Database**: SQLite
- **Scheduler**: APScheduler
- **Server**: Uvicorn

## 📋 Usage

1.  Add websites using the form
2.  Monitor status on the dashboard
3.  View check history for each monitor
4.  Run manual checks at any time
5.  Delete monitors when no longer needed

## ⚙️ Configuration

Checks run every minute by default. Alerts are logged to the console when a site fails 2 consecutive checks.

## 📊 Data Storage

All data is stored locally in `uptime_monitor.db` SQLite file.

## 📝 License

Open source - free to use and modify.
