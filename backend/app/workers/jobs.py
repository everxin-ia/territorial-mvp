from __future__ import annotations
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.session import SessionLocal, engine
from app.db.models import Base, Tenant, Source, AlertRule
from app.services.ingest.pipeline import ingest_sources
from app.services.risk.compute import compute_risk_snapshots
from app.services.alerts.engine import run_alerts

scheduler = BackgroundScheduler(timezone="UTC")

def seed_demo(db: Session) -> None:
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Tenant
    tenant = db.query(Tenant).filter(Tenant.id==1).first()
    if not tenant:
        tenant = Tenant(id=1, name="Demo Tenant")
        db.add(tenant)
        db.commit()

    # Sources (RSS demo)
    if db.query(Source).filter(Source.tenant_id==1).count() == 0:
        demo_sources = [
            ("Google News - conflicto territorial (ES)", "https://news.google.com/rss/search?q=conflicto+territorial&hl=es-419&gl=CL&ceid=CL:es-419"),
            ("Google News - protesta (ES)", "https://news.google.com/rss/search?q=protesta+comunidad&hl=es-419&gl=CL&ceid=CL:es-419"),
            ("Google News - sanción ambiental (ES)", "https://news.google.com/rss/search?q=sanci%C3%B3n+ambiental&hl=es-419&gl=CL&ceid=CL:es-419"),
        ]
        for name, url in demo_sources:
            db.add(Source(tenant_id=1, name=name, url=url, type="rss", weight=1.2, enabled=True))
        db.commit()

    # Alert rule
    if db.query(AlertRule).filter(AlertRule.tenant_id==1).count() == 0:
        db.add(AlertRule(tenant_id=1, name="Riesgo alto (demo)", min_prob=0.65, min_confidence=0.45, enabled=True))
        db.commit()

def job_ingest():
    db = SessionLocal()
    try:
        ingest_sources(db, tenant_id=1)
    finally:
        db.close()

def job_risk():
    db = SessionLocal()
    try:
        compute_risk_snapshots(db, tenant_id=1, window_days=7)
    finally:
        db.close()

def job_alerts():
    db = SessionLocal()
    try:
        run_alerts(db, tenant_id=1)
    finally:
        db.close()

def start_scheduler():
    # Ensure DB seeded
    db = SessionLocal()
    try:
        seed_demo(db)
    finally:
        db.close()

    if scheduler.running:
        return

    scheduler.add_job(job_ingest, trigger=IntervalTrigger(minutes=30), id="ingest", replace_existing=True)
    scheduler.add_job(job_risk, trigger=IntervalTrigger(minutes=60), id="risk", replace_existing=True)
    scheduler.add_job(job_alerts, trigger=IntervalTrigger(minutes=15), id="alerts", replace_existing=True)

    # run once at startup for demo
    job_ingest()
    job_risk()
    job_alerts()

    scheduler.start()
