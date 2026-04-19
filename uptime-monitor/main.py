from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import requests
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Uptime Monitor")

DATABASE_URL = "sqlite:///./uptime_monitor.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Monitor(Base):
    __tablename__ = "monitors"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_check = Column(DateTime, nullable=True)
    is_up = Column(Boolean, default=True)
    consecutive_failures = Column(Integer, default=0)
    checks = relationship("CheckLog", back_populates="monitor", cascade="all, delete-orphan")


class CheckLog(Base):
    __tablename__ = "check_logs"
    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, ForeignKey("monitors.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    response_time = Column(Float)
    status_code = Column(Integer)
    is_up = Column(Boolean)
    error_message = Column(String, nullable=True)
    monitor = relationship("Monitor", back_populates="checks")


Base.metadata.create_all(bind=engine)


class MonitorCreate(BaseModel):
    url: HttpUrl
    name: str


class MonitorUpdate(BaseModel):
    enabled: bool


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def run_check(monitor_id: int):
    db = SessionLocal()
    monitor = db.query(Monitor).get(monitor_id)
    if not monitor:
        db.close()
        return

    start_time = datetime.utcnow()
    try:
        response = requests.get(str(monitor.url), timeout=10)
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        is_up = 200 <= response.status_code < 400

        log = CheckLog(
            monitor_id=monitor.id,
            timestamp=start_time,
            response_time=response_time,
            status_code=response.status_code,
            is_up=is_up
        )
        db.add(log)

        monitor.last_check = start_time
        monitor.is_up = is_up
        monitor.consecutive_failures = 0 if is_up else monitor.consecutive_failures + 1

        if not is_up and monitor.consecutive_failures >= 2:
            logger.warning(f"⚠️ ALERT: Site DOWN - {monitor.url} failed {monitor.consecutive_failures} times!")

    except Exception as e:
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        log = CheckLog(
            monitor_id=monitor.id,
            timestamp=start_time,
            response_time=response_time,
            status_code=0,
            is_up=False,
            error_message=str(e)
        )
        db.add(log)
        monitor.last_check = start_time
        monitor.is_up = False
        monitor.consecutive_failures += 1

        if monitor.consecutive_failures >= 2:
            logger.warning(f"⚠️ ALERT: Site DOWN - {monitor.url} failed {monitor.consecutive_failures} times! Error: {str(e)}")

    db.commit()
    db.close()


def run_all_checks():
    logger.info("Running scheduled uptime checks...")
    db = SessionLocal()
    monitors = db.query(Monitor).all()
    db.close()
    for monitor in monitors:
        run_check(monitor.id)


scheduler = BackgroundScheduler()
scheduler.add_job(run_all_checks, 'interval', minutes=1)
scheduler.start()


@app.get("/", response_class=HTMLResponse)
async def root():
    return templates.TemplateResponse("index.html", {"request": {}})


@app.get("/api/monitors")
def get_monitors():
    db = SessionLocal()
    monitors = db.query(Monitor).order_by(Monitor.created_at.desc()).all()
    result = []
    for m in monitors:
        uptime = 100.0
        last_100 = db.query(CheckLog).filter(CheckLog.monitor_id == m.id).order_by(CheckLog.timestamp.desc()).limit(100).all()
        if last_100:
            up_count = sum(1 for c in last_100 if c.is_up)
            uptime = round((up_count / len(last_100)) * 100, 2)

        result.append({
            "id": m.id,
            "url": m.url,
            "name": m.name,
            "is_up": m.is_up,
            "last_check": m.last_check.isoformat() if m.last_check else None,
            "consecutive_failures": m.consecutive_failures,
            "uptime": uptime
        })
    db.close()
    return result


@app.get("/api/monitors/{monitor_id}/history")
def get_monitor_history(monitor_id: int):
    db = SessionLocal()
    logs = db.query(CheckLog).filter(CheckLog.monitor_id == monitor_id).order_by(CheckLog.timestamp.desc()).limit(50).all()
    result = []
    for log in logs:
        result.append({
            "timestamp": log.timestamp.isoformat(),
            "response_time": log.response_time,
            "status_code": log.status_code,
            "is_up": log.is_up,
            "error": log.error_message
        })
    db.close()
    return result


@app.post("/api/monitors")
def create_monitor(data: MonitorCreate):
    db = SessionLocal()
    existing = db.query(Monitor).filter(Monitor.url == str(data.url)).first()
    if existing:
        raise HTTPException(status_code=400, detail="URL already being monitored")
    monitor = Monitor(url=str(data.url), name=data.name)
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    db.close()
    run_check(monitor.id)
    return {"status": "ok", "id": monitor.id}


@app.delete("/api/monitors/{monitor_id}")
def delete_monitor(monitor_id: int):
    db = SessionLocal()
    monitor = db.query(Monitor).get(monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    db.delete(monitor)
    db.commit()
    db.close()
    return {"status": "ok"}


@app.post("/api/monitors/{monitor_id}/check")
def manual_check(monitor_id: int):
    run_check(monitor_id)
    return {"status": "check completed"}


@app.get("/api/status")
def status():
    db = SessionLocal()
    total = db.query(Monitor).count()
    up = db.query(Monitor).filter(Monitor.is_up == True).count()
    db.close()
    return {
        "total_monitors": total,
        "up_monitors": up,
        "down_monitors": total - up,
        "check_interval": 60,
        "scheduler_running": scheduler.running
    }


@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    logger.info("Scheduler stopped cleanly")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
