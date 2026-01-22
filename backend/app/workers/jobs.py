# app/workers/jobs.py
from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.db.models import Base, Tenant, Source, AlertRule, Territory
from app.services.ingest.pipeline import ingest_sources
from app.services.risk.compute import compute_risk_snapshots
from app.services.alerts.engine import run_alerts
from app.data.chile_territories import CHILE_TERRITORIES

scheduler = BackgroundScheduler(timezone="UTC")


def db_is_ready() -> bool:
    """
    Verifica rápidamente si la DB está accesible.
    Si no lo está, devolvemos False y evitamos crashear el startup.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"⚠️ DB no disponible aún: {e}")
        return False


def seed_demo(db: Session) -> None:
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Tenant
    tenant = db.query(Tenant).filter(Tenant.id == 1).first()
    if not tenant:
        tenant = Tenant(id=1, name="Demo Tenant")
        db.add(tenant)
        db.commit()

    # Territories - Todas las regiones, comunas y localidades de Chile
    if db.query(Territory).filter(Territory.tenant_id == 1).count() == 0:
        print("Seeding Chile territories (16 regiones + 346 comunas)...")

        for region_data in CHILE_TERRITORIES:
            region = Territory(
                tenant_id=1,
                name=region_data["name"],
                level=region_data["level"],
                latitude=region_data["lat"],
                longitude=region_data["lon"],
            )
            db.add(region)
            db.flush()

            for comuna_data in region_data.get("comunas", []):
                comuna = Territory(
                    tenant_id=1,
                    name=comuna_data["name"],
                    level="comuna",
                    latitude=comuna_data["lat"],
                    longitude=comuna_data["lon"],
                    parent_id=region.id,
                )
                db.add(comuna)

        db.commit()
        print("✓ Seeded Chile territories")

    # Sources (RSS feeds de instituciones públicas chilenas)
    if db.query(Source).filter(Source.tenant_id == 1).count() == 0:
        # RSS feeds de instituciones públicas de Chile
        chile_sources = [
            # Instituciones gubernamentales oficiales (alta credibilidad)
            ("Gobierno de Chile - Noticias",
             "https://www.gob.cl/noticias/feed/rss/", 1.5, 0.95),
            ("Biblioteca del Congreso Nacional (BCN)",
             "https://www.bcn.cl/rss", 1.4, 0.95),
            ("SII - Todas las noticias",
             "https://www.sii.cl/pagina/actualizada/noticias/rss/siiall_rss.xml", 1.3, 0.90),
            ("SII - Noticias tributarias",
             "https://www.sii.cl/pagina/actualizada/noticias/rss/siinot_rss.xml", 1.3, 0.90),
            ("CSIRT Nacional - Alertas de seguridad",
             "https://csirt.gob.cl/rss/alertas", 1.4, 0.95),
            ("Ministerio de Economía - Noticias",
             "https://www.economia.gob.cl/category/noticias/feed", 1.2, 0.85),
            ("Ministerio de Desarrollo Social",
             "https://www.desarrollosocialyfamilia.gob.cl/index.php?format=feed&type=atom", 1.2, 0.85),

            # Google News - Búsquedas específicas para Chile
            ("Google News - Conflicto territorial Chile",
             "https://news.google.com/rss/search?q=conflicto+territorial+Chile&hl=es-419&gl=CL&ceid=CL:es-419", 1.0, 0.70),
            ("Google News - Protesta Chile",
             "https://news.google.com/rss/search?q=protesta+Chile&hl=es-419&gl=CL&ceid=CL:es-419", 1.0, 0.65),
            ("Google News - Sanción ambiental Chile",
             "https://news.google.com/rss/search?q=sanción+ambiental+Chile&hl=es-419&gl=CL&ceid=CL:es-419", 1.2, 0.75),
            ("Google News - Riesgo territorial Chile",
             "https://news.google.com/rss/search?q=riesgo+territorial+Chile&hl=es-419&gl=CL&ceid=CL:es-419", 1.1, 0.70),
        ]

        for name, url, weight, credibility in chile_sources:
            db.add(
                Source(
                    tenant_id=1,
                    name=name,
                    url=url,
                    language="es",
                    weight=weight,
                    credibility_score=credibility,
                    enabled=True,
                )
            )
        db.commit()
        print(f"✓ Seeded {len(chile_sources)} RSS sources (Chile instituciones públicas)")

    # Alert rule
    if db.query(AlertRule).filter(AlertRule.tenant_id == 1).count() == 0:
        db.add(AlertRule(tenant_id=1, name="Riesgo alto (demo)",
               min_prob=0.65, min_confidence=0.45, enabled=True))
        db.commit()
        print("✓ Seeded demo alert rule")


def job_ingest():
    db = SessionLocal()
    try:
        ingest_sources(db)
    finally:
        db.close()


def job_risk():
    db = SessionLocal()
    try:
        compute_risk_snapshots(db)
    finally:
        db.close()


def job_alerts():
    db = SessionLocal()
    try:
        run_alerts(db)
    finally:
        db.close()


def start_scheduler():
    """
    Inicia scheduler SOLO si:
    - no está deshabilitado por env (DISABLE_SCHEDULER=true)
    - la DB responde (SELECT 1)
    """
    if settings.disable_scheduler:
        print("ℹ️ Scheduler deshabilitado por DISABLE_SCHEDULER=true")
        return

    if scheduler.running:
        return

    if not db_is_ready():
        print("ℹ️ No se inicia scheduler porque la DB no está lista.")
        return

    # Seed + jobs
    db = SessionLocal()
    try:
        seed_demo(db)
    except OperationalError as e:
        print(f"⚠️ No se pudo seedear demo (DB): {e}")
        return
    finally:
        db.close()

    scheduler.add_job(job_ingest, trigger=IntervalTrigger(
        minutes=30), id="ingest", replace_existing=True)
    scheduler.add_job(job_risk, trigger=IntervalTrigger(
        minutes=60), id="risk", replace_existing=True)
    scheduler.add_job(job_alerts, trigger=IntervalTrigger(
        minutes=15), id="alerts", replace_existing=True)

    # (opcional) correr una vez al arranque si DB OK
    try:
        job_ingest()
        job_risk()
        job_alerts()
    except Exception as e:
        print(f"⚠️ Error ejecutando jobs iniciales: {e}")

    scheduler.start()
    print("✓ Scheduler iniciado")
