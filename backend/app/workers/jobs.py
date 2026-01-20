from __future__ import annotations
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import json

from app.db.session import SessionLocal, engine
from app.db.models import Base, Tenant, Source, AlertRule, Territory
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

    # Territories demo (Chile principales)
    if db.query(Territory).filter(Territory.tenant_id==1).count() == 0:
        demo_territories = [
            {"name": "Santiago", "level": "región", "lat": -33.4489, "lon": -70.6693, "aliases": ["Región Metropolitana", "RM", "Stgo"]},
            {"name": "Valparaíso", "level": "región", "lat": -33.0472, "lon": -71.6127, "aliases": ["Quinta Región", "V Región"]},
            {"name": "Antofagasta", "level": "región", "lat": -23.6509, "lon": -70.3975, "aliases": ["Segunda Región", "II Región"]},
            {"name": "Concepción", "level": "ciudad", "lat": -36.8270, "lon": -73.0498, "aliases": ["Conce", "Región del Biobío"]},
            {"name": "La Serena", "level": "ciudad", "lat": -29.9027, "lon": -71.2519, "aliases": ["Cuarta Región", "IV Región"]},
            {"name": "Temuco", "level": "ciudad", "lat": -38.7359, "lon": -72.5904, "aliases": ["Araucanía", "IX Región"]},
            {"name": "Iquique", "level": "ciudad", "lat": -20.2307, "lon": -70.1355, "aliases": ["Tarapacá", "I Región"]},
            {"name": "Puerto Montt", "level": "ciudad", "lat": -41.4693, "lon": -72.9424, "aliases": ["Los Lagos", "X Región"]},
        ]
        for terr_data in demo_territories:
            db.add(Territory(
                tenant_id=1,
                name=terr_data["name"],
                level=terr_data["level"],
                latitude=terr_data["lat"],
                longitude=terr_data["lon"],
                aliases_json=json.dumps(terr_data["aliases"], ensure_ascii=False),
                enabled=True
            ))
        db.commit()

    # Sources (RSS demo)
    if db.query(Source).filter(Source.tenant_id==1).count() == 0:
        demo_sources = [
            ("Google News - conflicto territorial (ES)", "https://news.google.com/rss/search?q=conflicto+territorial&hl=es-419&gl=CL&ceid=CL:es-419", 1.2, 0.7),
            ("Google News - protesta (ES)", "https://news.google.com/rss/search?q=protesta+comunidad&hl=es-419&gl=CL&ceid=CL:es-419", 1.0, 0.6),
            ("Google News - sanción ambiental (ES)", "https://news.google.com/rss/search?q=sanci%C3%B3n+ambiental&hl=es-419&gl=CL&ceid=CL:es-419", 1.3, 0.8),
        ]
        for name, url, weight, credibility in demo_sources:
            db.add(Source(tenant_id=1, name=name, url=url, type="rss", weight=weight, credibility_score=credibility, enabled=True))
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
