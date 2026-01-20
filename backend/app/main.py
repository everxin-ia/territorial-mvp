from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_signals import router as signals_router
from app.api.routes_alerts import router as alerts_router
from app.api.routes_export import router as export_router
from app.api.routes_territories import router as territories_router
from app.api.routes_alert_rules import router as alert_rules_router
from app.workers.jobs import start_scheduler

app = FastAPI(title="Plataforma Inteligencia Territorial - MVP (Enhanced)")

# CORS para desarrollo
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
app.include_router(territories_router, prefix="/territories", tags=["territories"])
app.include_router(alert_rules_router, prefix="/alert-rules", tags=["alert-rules"])

@app.on_event("startup")
def on_startup():
    start_scheduler()

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}
