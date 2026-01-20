from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
import json
from app.db.session import get_db
from app.db.models import Territory

router = APIRouter()

class TerritoryCreate(BaseModel):
    name: str
    level: str = "unknown"
    parent_id: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    aliases: list[str] = []
    enabled: bool = True

class TerritoryUpdate(BaseModel):
    name: str | None = None
    level: str | None = None
    parent_id: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    aliases: list[str] | None = None
    enabled: bool | None = None

@router.get("")
def list_territories(tenant_id: int = Query(1), db: Session = Depends(get_db)):
    territories = db.execute(
        select(Territory).where(Territory.tenant_id == tenant_id)
    ).scalars().all()

    return [{
        "id": t.id,
        "name": t.name,
        "level": t.level,
        "parent_id": t.parent_id,
        "latitude": t.latitude,
        "longitude": t.longitude,
        "aliases": json.loads(t.aliases_json or "[]"),
        "enabled": t.enabled
    } for t in territories]

@router.post("")
def create_territory(data: TerritoryCreate, tenant_id: int = Query(1), db: Session = Depends(get_db)):
    terr = Territory(
        tenant_id=tenant_id,
        name=data.name,
        level=data.level,
        parent_id=data.parent_id,
        latitude=data.latitude,
        longitude=data.longitude,
        aliases_json=json.dumps(data.aliases, ensure_ascii=False),
        enabled=data.enabled
    )
    db.add(terr)
    db.commit()
    db.refresh(terr)

    return {
        "id": terr.id,
        "name": terr.name,
        "level": terr.level,
        "parent_id": terr.parent_id,
        "latitude": terr.latitude,
        "longitude": terr.longitude,
        "aliases": data.aliases,
        "enabled": terr.enabled
    }

@router.put("/{territory_id}")
def update_territory(territory_id: int, data: TerritoryUpdate, db: Session = Depends(get_db)):
    terr = db.get(Territory, territory_id)
    if not terr:
        raise HTTPException(status_code=404, detail="Territory not found")

    if data.name is not None:
        terr.name = data.name
    if data.level is not None:
        terr.level = data.level
    if data.parent_id is not None:
        terr.parent_id = data.parent_id
    if data.latitude is not None:
        terr.latitude = data.latitude
    if data.longitude is not None:
        terr.longitude = data.longitude
    if data.aliases is not None:
        terr.aliases_json = json.dumps(data.aliases, ensure_ascii=False)
    if data.enabled is not None:
        terr.enabled = data.enabled

    db.commit()
    db.refresh(terr)

    return {
        "id": terr.id,
        "name": terr.name,
        "level": terr.level,
        "parent_id": terr.parent_id,
        "latitude": terr.latitude,
        "longitude": terr.longitude,
        "aliases": json.loads(terr.aliases_json or "[]"),
        "enabled": terr.enabled
    }

@router.delete("/{territory_id}")
def delete_territory(territory_id: int, db: Session = Depends(get_db)):
    terr = db.get(Territory, territory_id)
    if not terr:
        raise HTTPException(status_code=404, detail="Territory not found")

    db.delete(terr)
    db.commit()
    return {"status": "deleted", "id": territory_id}

@router.get("/map")
def get_map_data(tenant_id: int = Query(1), db: Session = Depends(get_db)):
    """
    Endpoint para obtener datos del mapa: territorios con coordenadas + risk snapshots recientes
    """
    from app.db.models import RiskSnapshot
    from datetime import datetime, timedelta, timezone

    territories = db.execute(
        select(Territory).where(
            Territory.tenant_id == tenant_id,
            Territory.enabled == True,
            Territory.latitude.isnot(None),
            Territory.longitude.isnot(None)
        )
    ).scalars().all()

    # Obtener snapshots recientes (últimas 24h)
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    snapshots = db.execute(
        select(RiskSnapshot).where(
            RiskSnapshot.tenant_id == tenant_id,
            RiskSnapshot.period_end >= since
        )
    ).scalars().all()

    snapshot_map = {s.territory: s for s in snapshots}

    features = []
    for t in territories:
        snap = snapshot_map.get(t.name)

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [t.longitude, t.latitude]
            },
            "properties": {
                "id": t.id,
                "name": t.name,
                "level": t.level,
                "risk_prob": snap.risk_prob if snap else 0.0,
                "risk_score": snap.risk_score if snap else 0.0,
                "confidence": snap.confidence if snap else 0.0,
                "trend": snap.trend if snap else "stable",
                "is_anomaly": snap.is_anomaly if snap else False
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }
