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
from app.data.chile_territories import CHILE_TERRITORIES

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

    # Territories - Todas las regiones, comunas y localidades de Chile
    if db.query(Territory).filter(Territory.tenant_id==1).count() == 0:
        print("Seeding Chile territories (16 regiones + 346 comunas)...")

        for region_data in CHILE_TERRITORIES:
            # Insertar región
            region = Territory(
                tenant_id=1,
                name=region_data["name"],
                level=region_data["level"],
                latitude=region_data["lat"],
                longitude=region_data["lon"],
                aliases_json=json.dumps(region_data["aliases"], ensure_ascii=False),
                enabled=True,
                parent_id=None  # Regiones no tienen parent
            )
            db.add(region)
            db.flush()  # Flush para obtener el ID sin commit

            # Insertar comunas de esta región
            if "comunas" in region_data:
                for comuna_data in region_data["comunas"]:
                    comuna = Territory(
                        tenant_id=1,
                        name=comuna_data["name"],
                        level="comuna",
                        latitude=comuna_data["lat"],
                        longitude=comuna_data["lon"],
                        aliases_json=json.dumps(comuna_data.get("aliases", []), ensure_ascii=False),
                        enabled=True,
                        parent_id=region.id  # Comuna tiene como parent a la región
                    )
                    db.add(comuna)

        db.commit()
        print(f"✓ Seeded {db.query(Territory).filter(Territory.tenant_id==1).count()} territories")

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
        print(f"✓ Seeded {len(demo_sources)} RSS sources")

    # Alert rule
    if db.query(AlertRule).filter(AlertRule.tenant_id==1).count() == 0:
        db.add(AlertRule(tenant_id=1, name="Riesgo alto (demo)", min_prob=0.65, min_confidence=0.45, enabled=True))
        db.commit()
        print("✓ Seeded alert rules")

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
