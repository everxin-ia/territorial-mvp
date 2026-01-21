# app/main.py
from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.core.config import settings
from app.api.routes_signals import router as signals_router
from app.api.routes_alerts import router as alerts_router
from app.api.routes_export import router as export_router
from app.api.routes_territories import router as territories_router
from app.api.routes_alert_rules import router as alert_rules_router
from app.workers.jobs import start_scheduler


BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=BACKEND_ROOT / ".env", override=False)

app = FastAPI(title="Plataforma Inteligencia Territorial - MVP (Enhanced)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(signals_router, prefix="/signals", tags=["signals"])
app.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
app.include_router(export_router, prefix="/export", tags=["export"])
app.include_router(territories_router,
                   prefix="/territories", tags=["territories"])
app.include_router(alert_rules_router,
                   prefix="/alert-rules", tags=["alert-rules"])


@app.on_event("startup")
def on_startup():
    # No dejamos caer el backend por temas de DB/scheduler
    try:
        start_scheduler()
    except Exception as e:
        print(f"⚠️ Scheduler no pudo iniciar (no crítico): {e}")


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/debug/ai")
def debug_ai_config():
    key = settings.openai_api_key
    return {
        "ai_provider": settings.ai_provider,
        "openai_model": settings.openai_model,
        "openai_base_url": settings.openai_base_url,
        "openai_api_key_loaded": bool(key),
        "openai_api_key_preview": (key[:7] + "..." + key[-4:]) if key and len(key) > 12 else None,
    }
