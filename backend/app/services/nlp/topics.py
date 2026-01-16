TOPIC_RULES = {
    "socioambiental": ["impacto ambiental", "contaminación", "agua", "relave", "fauna", "flor", "humedal", "evaluación ambiental", "eia"],
    "regulatorio": ["superintendencia", "fiscalización", "sanción", "resolución", "normativa", "permiso", "seremi", "municipalidad"],
    "laboral": ["huelga", "sindicato", "negociación colectiva", "paro", "despidos", "turnos"],
    "seguridad": ["accidente", "incendio", "explosión", "heridos", "evacuación", "amenaza"],
    "reputacional": ["denuncia", "críticas", "boicot", "corrupción", "transparencia", "querella"],
    "infraestructura": ["corte de ruta", "bloqueo", "puente", "carretera", "puerto", "aeropuerto"],
    "politico-administrativo": ["gobernación", "delegación", "concejo", "alcalde", "gobernador", "consulta ciudadana"],
}

def topic_scores(text: str) -> list[dict]:
    t = (text or "").lower()
    out = []
    for topic, kws in TOPIC_RULES.items():
        hits = sum(1 for kw in kws if kw in t)
        score = min(hits / 3.0, 1.0)  # 0..1
        if score > 0:
            out.append({"topic": topic, "score": float(score), "method": "rules"})
    if not out:
        out.append({"topic": "otros", "score": 0.2, "method": "rules"})
    return sorted(out, key=lambda x: x["score"], reverse=True)
