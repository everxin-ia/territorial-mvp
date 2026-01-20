from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_db
from app.db.models import AlertRule, AlertComment, AlertEvent

router = APIRouter()

class AlertRuleCreate(BaseModel):
    name: str
    territory_filter: str = ""
    topic_filter: str = ""
    min_prob: float = 0.6
    min_confidence: float = 0.4
    enabled: bool = True

class AlertRuleUpdate(BaseModel):
    name: str | None = None
    territory_filter: str | None = None
    topic_filter: str | None = None
    min_prob: float | None = None
    min_confidence: float | None = None
    enabled: bool | None = None

@router.get("")
def list_alert_rules(tenant_id: int = Query(1), db: Session = Depends(get_db)):
    rules = db.execute(
        select(AlertRule).where(AlertRule.tenant_id == tenant_id)
    ).scalars().all()

    return [{
        "id": r.id,
        "name": r.name,
        "territory_filter": r.territory_filter,
        "topic_filter": r.topic_filter,
        "min_prob": r.min_prob,
        "min_confidence": r.min_confidence,
        "enabled": r.enabled
    } for r in rules]

@router.post("")
def create_alert_rule(data: AlertRuleCreate, tenant_id: int = Query(1), db: Session = Depends(get_db)):
    rule = AlertRule(
        tenant_id=tenant_id,
        name=data.name,
        territory_filter=data.territory_filter,
        topic_filter=data.topic_filter,
        min_prob=data.min_prob,
        min_confidence=data.min_confidence,
        enabled=data.enabled
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    return {
        "id": rule.id,
        "name": rule.name,
        "territory_filter": rule.territory_filter,
        "topic_filter": rule.topic_filter,
        "min_prob": rule.min_prob,
        "min_confidence": rule.min_confidence,
        "enabled": rule.enabled
    }

@router.put("/{rule_id}")
def update_alert_rule(rule_id: int, data: AlertRuleUpdate, db: Session = Depends(get_db)):
    rule = db.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    if data.name is not None:
        rule.name = data.name
    if data.territory_filter is not None:
        rule.territory_filter = data.territory_filter
    if data.topic_filter is not None:
        rule.topic_filter = data.topic_filter
    if data.min_prob is not None:
        rule.min_prob = data.min_prob
    if data.min_confidence is not None:
        rule.min_confidence = data.min_confidence
    if data.enabled is not None:
        rule.enabled = data.enabled

    db.commit()
    db.refresh(rule)

    return {
        "id": rule.id,
        "name": rule.name,
        "territory_filter": rule.territory_filter,
        "topic_filter": rule.topic_filter,
        "min_prob": rule.min_prob,
        "min_confidence": rule.min_confidence,
        "enabled": rule.enabled
    }

@router.delete("/{rule_id}")
def delete_alert_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(AlertRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    db.delete(rule)
    db.commit()
    return {"status": "deleted", "id": rule_id}


# Comments on alerts
class CommentCreate(BaseModel):
    user_name: str = "Usuario"
    comment: str

@router.post("/{alert_id}/comments")
def add_comment(alert_id: int, data: CommentCreate, db: Session = Depends(get_db)):
    alert = db.get(AlertEvent, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    comment = AlertComment(
        alert_id=alert_id,
        user_name=data.user_name,
        comment=data.comment
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {
        "id": comment.id,
        "alert_id": comment.alert_id,
        "user_name": comment.user_name,
        "comment": comment.comment,
        "created_at": comment.created_at.isoformat()
    }

@router.get("/{alert_id}/comments")
def list_comments(alert_id: int, db: Session = Depends(get_db)):
    comments = db.execute(
        select(AlertComment).where(AlertComment.alert_id == alert_id).order_by(AlertComment.created_at.desc())
    ).scalars().all()

    return [{
        "id": c.id,
        "alert_id": c.alert_id,
        "user_name": c.user_name,
        "comment": c.comment,
        "created_at": c.created_at.isoformat()
    } for c in comments]

@router.patch("/{alert_id}/status")
def update_alert_status(alert_id: int, status: str = Query(...), db: Session = Depends(get_db)):
    """
    Actualiza el status de una alerta: new|acked|closed
    """
    alert = db.get(AlertEvent, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if status not in ["new", "acked", "closed"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    alert.status = status
    db.commit()

    return {"id": alert_id, "status": status}
