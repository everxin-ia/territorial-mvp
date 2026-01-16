from fastapi import FastAPI
from app.api.routes_signals import router as signals_router
from app.api.routes_alerts import router as alerts_router
from app.api.routes_export import router as export_router
from app.workers.jobs import start_scheduler

app = FastAPI(title="Plataforma Inteligencia Territorial - MVP (Starter)")

app.include_router(signals_router, prefix="/signals", tags=["signals"])
app.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
app.include_router(export_router, prefix="/export", tags=["export"])

@app.on_event("startup")
def on_startup():
    start_scheduler()
