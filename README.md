# Plataforma Inteligencia Territorial — MVP Starter (Opción A: scoring + logística)

Este starter-kit levanta **Postgres + FastAPI (API + scheduler) + React (Vite)** con Docker Compose.
Incluye:
- Ingesta RSS (feedparser) + normalización + dedupe simple (hash)
- Tópicos por reglas + territorios por diccionario
- Scoring heurístico → probabilidad logística + confianza
- Snapshots de riesgo por territorio (últimos 7 días)
- Motor de alertas por umbral + webhook
- Endpoints REST + export CSV
- Frontend demo con 4 vistas (Resumen, Señales, Riesgo, Alertas)

## Requisitos
- Docker + Docker Compose
- (Opcional) Node 18+ si quieres correr el frontend fuera de Docker

## Quickstart
```bash
cd territorial-mvp
docker compose up --build
```

- Backend: http://localhost:8000/docs
- Frontend: http://localhost:5173

## Variables de entorno (backend)
Se cargan desde `backend/.env` (ya viene uno de ejemplo). Puedes setear:
- `ALERT_WEBHOOK_URL` (opcional): si existe, manda POST JSON cuando hay alerta

## Notas de demo/ética
Esto **no predice** eventos; estima una **probabilidad de riesgo basada en señales públicas** + drivers + confianza.
No usar para decisiones automatizadas.
