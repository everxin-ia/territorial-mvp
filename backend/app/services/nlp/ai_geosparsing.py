"""
Sistema de Geosparsing con IA para Detección de Topónimos
==========================================================

Este módulo implementa un sistema completo de geosparsing que:
1. Detecta topónimos (lugares) en español usando IA
2. Resuelve geográficamente usando un gazetteer (catálogo de territorios)
3. Maneja homónimos y desambiguación contextual
4. Proporciona scoring basado en múltiples señales
5. Guarda trazabilidad completa de las detecciones

Proveedores de IA soportados:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic Claude
- spaCy NER (fallback sin API)
"""

from __future__ import annotations
import os
import re
import json
from typing import Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import httpx
from rapidfuzz import fuzz

# Importar el catálogo de territorios de Chile
from app.data.chile_territories import CHILE_TERRITORIES


@dataclass
class ToponymDetection:
    """Representa un topónimo detectado en el texto"""
    toponym: str  # El topónimo detectado (ej: "Rancagua")
    position_start: int  # Posición de inicio en el texto
    position_end: int  # Posición de fin en el texto
    context: str  # Contexto alrededor del topónimo (±50 caracteres)
    in_title: bool  # Si aparece en el título
    method: str  # Método de detección (ai_ner, spacy, regex)
    confidence: float  # Confianza de la detección (0-1)


@dataclass
class TerritoryMatch:
    """Representa un territorio mapeado con trazabilidad"""
    territory_name: str  # Nombre oficial del territorio
    territory_level: str  # Nivel: región, comuna, localidad
    latitude: Optional[float]
    longitude: Optional[float]

    # Trazabilidad
    detected_toponym: str  # El topónimo original detectado
    toponym_position: int  # Posición en el texto
    toponym_context: str  # Contexto del topónimo

    # Scoring
    relevance_score: float  # Score final de relevancia (0-1)
    scoring_breakdown: dict[str, float]  # Desglose de scores

    # Explicabilidad
    mapping_method: str  # exact_match, alias_match, fuzzy_match, ai_disambiguation
    disambiguation_reason: Optional[str]  # Por qué se eligió este territorio

    # Metadata
    matched_at: str  # Timestamp ISO
    ai_provider: Optional[str]  # openai, anthropic, spacy, none


class AIGeoparser:
    """
    Parser geográfico con IA para detección y resolución de topónimos
    """

    def __init__(
        self,
        ai_provider: Optional[str] = None,
        api_key: Optional[str] = None,
        use_spacy_fallback: bool = True
    ):
        """
        Inicializa el geoparser

        Args:
            ai_provider: "openai" o "anthropic" (None usa variables de entorno)
            api_key: API key (None usa variables de entorno)
            use_spacy_fallback: Usar spaCy si no hay API key disponible
        """
        self.ai_provider = ai_provider or os.getenv("AI_PROVIDER", "openai")
        self.api_key = api_key or self._get_api_key()
        self.use_spacy_fallback = use_spacy_fallback
        self.spacy_model = None

        # Construir gazetteer (índice de territorios)
        self.gazetteer = self._build_gazetteer()

        # Cargar modelo spaCy si está habilitado el fallback
        if self.use_spacy_fallback and not self.api_key:
            self._load_spacy_model()

    def _get_api_key(self) -> Optional[str]:
        """Obtiene la API key desde variables de entorno"""
        if self.ai_provider == "openai":
            return os.getenv("OPENAI_API_KEY")
        elif self.ai_provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY")
        return None

    def _load_spacy_model(self):
        """Carga el modelo spaCy para NER en español"""
        try:
            import spacy
            # Intentar cargar modelo en español
            try:
                self.spacy_model = spacy.load("es_core_news_sm")
            except OSError:
                # Si no está instalado, intentar con el grande
                try:
                    self.spacy_model = spacy.load("es_core_news_md")
                except OSError:
                    print("⚠️  No se pudo cargar modelo spaCy. Instalar con: python -m spacy download es_core_news_sm")
                    self.spacy_model = None
        except ImportError:
            print("⚠️  spaCy no está instalado")
            self.spacy_model = None

    def _build_gazetteer(self) -> dict[str, list[dict]]:
        """
        Construye un índice invertido de territorios para búsqueda rápida

        Returns:
            Dict con nombres (normalizados) como keys y lista de territorios como values
        """
        gazetteer = {}

        for region in CHILE_TERRITORIES:
            # Agregar región
            for name in [region["name"]] + region.get("aliases", []):
                normalized = self._normalize_text(name)
                if normalized not in gazetteer:
                    gazetteer[normalized] = []
                gazetteer[normalized].append({
                    "name": region["name"],
                    "level": region["level"],
                    "lat": region["lat"],
                    "lon": region["lon"],
                    "region": region["name"],
                    "matched_via": name
                })

            # Agregar comunas
            for comuna in region.get("comunas", []):
                for name in [comuna["name"]] + comuna.get("aliases", []):
                    normalized = self._normalize_text(name)
                    if normalized not in gazetteer:
                        gazetteer[normalized] = []
                    gazetteer[normalized].append({
                        "name": comuna["name"],
                        "level": "comuna",
                        "lat": comuna["lat"],
                        "lon": comuna["lon"],
                        "region": region["name"],
                        "matched_via": name
                    })

        return gazetteer

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normaliza texto para matching (lowercase, sin acentos)"""
        import unicodedata
        text = text.lower()
        # Remover acentos
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        return text

    async def detect_toponyms(
        self,
        title: str,
        content: str
    ) -> list[ToponymDetection]:
        """
        Detecta topónimos en el texto usando IA o fallback

        Args:
            title: Título de la noticia
            content: Contenido completo

        Returns:
            Lista de topónimos detectados con su contexto
        """
        full_text = f"{title}\n\n{content}"

        # Intentar con IA primero
        if self.api_key:
            if self.ai_provider == "openai":
                return await self._detect_toponyms_openai(title, content, full_text)
            elif self.ai_provider == "anthropic":
                return await self._detect_toponyms_anthropic(title, content, full_text)

        # Fallback a spaCy
        if self.spacy_model:
            return self._detect_toponyms_spacy(title, content, full_text)

        # Fallback final: regex simple
        return self._detect_toponyms_regex(title, content, full_text)

    async def _detect_toponyms_openai(
        self,
        title: str,
        content: str,
        full_text: str
    ) -> list[ToponymDetection]:
        """Detecta topónimos usando OpenAI GPT"""
        prompt = f"""Eres un sistema de NER especializado en detectar topónimos (lugares) en español chileno.

Analiza el siguiente texto y extrae TODOS los topónimos (nombres de lugares) que encuentres.
Incluye: regiones, comunas, ciudades, localidades, barrios, calles principales.

TÍTULO: {title}

CONTENIDO: {content[:3000]}

Devuelve SOLO un JSON con este formato:
{{
  "toponyms": [
    {{"toponym": "nombre del lugar", "position": posición_aproximada_en_caracteres}},
    ...
  ]
}}

Responde SOLO con el JSON, sin explicaciones."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                        "messages": [
                            {"role": "system", "content": "Eres un sistema NER experto en detectar lugares en español chileno. Respondes solo JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1000
                    }
                )

                if response.status_code != 200:
                    print(f"❌ Error OpenAI: {response.status_code}")
                    return []

                result = response.json()
                content_text = result["choices"][0]["message"]["content"]

                # Extraer JSON de la respuesta
                json_match = re.search(r'\{.*\}', content_text, re.DOTALL)
                if not json_match:
                    return []

                data = json.loads(json_match.group())

                # Convertir a ToponymDetection
                detections = []
                for item in data.get("toponyms", []):
                    toponym = item["toponym"]
                    # Buscar posición real en el texto
                    position = full_text.lower().find(toponym.lower())
                    if position == -1:
                        position = item.get("position", 0)

                    in_title = toponym.lower() in title.lower()
                    context = self._extract_context(full_text, position, 50)

                    detections.append(ToponymDetection(
                        toponym=toponym,
                        position_start=position,
                        position_end=position + len(toponym),
                        context=context,
                        in_title=in_title,
                        method="ai_ner_openai",
                        confidence=0.9
                    ))

                return detections

        except Exception as e:
            print(f"❌ Error en detección OpenAI: {e}")
            return []

    async def _detect_toponyms_anthropic(
        self,
        title: str,
        content: str,
        full_text: str
    ) -> list[ToponymDetection]:
        """Detecta topónimos usando Anthropic Claude"""
        prompt = f"""Analiza este texto y extrae todos los topónimos (lugares) en español chileno.

TÍTULO: {title}

CONTENIDO: {content[:3000]}

Devuelve un JSON con este formato:
{{
  "toponyms": [
    {{"toponym": "nombre", "position": posición_aproximada}},
    ...
  ]
}}"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
                        "max_tokens": 1000,
                        "temperature": 0.1,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ]
                    }
                )

                if response.status_code != 200:
                    print(f"❌ Error Anthropic: {response.status_code}")
                    return []

                result = response.json()
                content_text = result["content"][0]["text"]

                # Extraer JSON
                json_match = re.search(r'\{.*\}', content_text, re.DOTALL)
                if not json_match:
                    return []

                data = json.loads(json_match.group())

                detections = []
                for item in data.get("toponyms", []):
                    toponym = item["toponym"]
                    position = full_text.lower().find(toponym.lower())
                    if position == -1:
                        position = item.get("position", 0)

                    in_title = toponym.lower() in title.lower()
                    context = self._extract_context(full_text, position, 50)

                    detections.append(ToponymDetection(
                        toponym=toponym,
                        position_start=position,
                        position_end=position + len(toponym),
                        context=context,
                        in_title=in_title,
                        method="ai_ner_anthropic",
                        confidence=0.9
                    ))

                return detections

        except Exception as e:
            print(f"❌ Error en detección Anthropic: {e}")
            return []

    def _detect_toponyms_spacy(
        self,
        title: str,
        content: str,
        full_text: str
    ) -> list[ToponymDetection]:
        """Detecta topónimos usando spaCy NER"""
        if not self.spacy_model:
            return []

        detections = []

        # Procesar texto con spaCy (limitar para performance)
        doc = self.spacy_model(full_text[:10000])

        for ent in doc.ents:
            # Filtrar solo entidades de tipo LOC (Location) y GPE (Geopolitical Entity)
            if ent.label_ not in ["LOC", "GPE"]:
                continue

            toponym = ent.text
            position = ent.start_char
            in_title = toponym.lower() in title.lower()
            context = self._extract_context(full_text, position, 50)

            detections.append(ToponymDetection(
                toponym=toponym,
                position_start=position,
                position_end=ent.end_char,
                context=context,
                in_title=in_title,
                method="spacy_ner",
                confidence=0.75
            ))

        return detections

    def _detect_toponyms_regex(
        self,
        title: str,
        content: str,
        full_text: str
    ) -> list[ToponymDetection]:
        """
        Fallback: detecta topónimos usando regex simple contra el gazetteer
        No es ideal pero funciona sin IA ni spaCy
        """
        detections = []

        # Buscar todos los nombres del gazetteer en el texto
        for normalized_name, territories in self.gazetteer.items():
            # Reconstruir nombre original
            original_name = territories[0]["matched_via"]

            # Buscar en el texto (case-insensitive)
            pattern = re.compile(r'\b' + re.escape(original_name) + r'\b', re.IGNORECASE)

            for match in pattern.finditer(full_text):
                position = match.start()
                toponym = match.group()
                in_title = toponym.lower() in title.lower()
                context = self._extract_context(full_text, position, 50)

                detections.append(ToponymDetection(
                    toponym=toponym,
                    position_start=position,
                    position_end=match.end(),
                    context=context,
                    in_title=in_title,
                    method="regex_gazetteer",
                    confidence=0.6
                ))

        return detections

    @staticmethod
    def _extract_context(text: str, position: int, window: int = 50) -> str:
        """Extrae contexto alrededor de una posición en el texto"""
        start = max(0, position - window)
        end = min(len(text), position + window)
        context = text[start:end]

        # Agregar ... si está truncado
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."

        return context.strip()

    def resolve_territory(
        self,
        detection: ToponymDetection,
        full_context: str,
        source_region: Optional[str] = None
    ) -> list[TerritoryMatch]:
        """
        Resuelve un topónimo detectado a territorios concretos del catálogo
        Maneja homónimos y desambiguación contextual

        Args:
            detection: Topónimo detectado
            full_context: Texto completo para contexto
            source_region: Región de la fuente (si se conoce, ayuda a desambiguar)

        Returns:
            Lista de posibles territorios ordenados por relevancia
        """
        normalized_toponym = self._normalize_text(detection.toponym)

        # 1. Búsqueda exacta en gazetteer
        candidates = self.gazetteer.get(normalized_toponym, [])

        # 2. Si no hay match exacto, buscar fuzzy
        if not candidates:
            candidates = self._fuzzy_search_gazetteer(detection.toponym)

        # 3. Si aún no hay candidatos, retornar vacío
        if not candidates:
            return []

        # 4. Scoring y desambiguación
        matches = []
        for candidate in candidates:
            score_breakdown = self._calculate_relevance_score(
                detection=detection,
                candidate=candidate,
                full_context=full_context,
                source_region=source_region
            )

            final_score = score_breakdown["final_score"]

            # Determinar método de matching
            if self._normalize_text(candidate["matched_via"]) == normalized_toponym:
                mapping_method = "exact_match" if candidate["matched_via"] == candidate["name"] else "alias_match"
            else:
                mapping_method = "fuzzy_match"

            # Generar explicación de desambiguación
            disambiguation_reason = self._generate_disambiguation_explanation(
                detection, candidate, score_breakdown, source_region
            )

            matches.append(TerritoryMatch(
                territory_name=candidate["name"],
                territory_level=candidate["level"],
                latitude=candidate["lat"],
                longitude=candidate["lon"],
                detected_toponym=detection.toponym,
                toponym_position=detection.position_start,
                toponym_context=detection.context,
                relevance_score=final_score,
                scoring_breakdown=score_breakdown,
                mapping_method=mapping_method,
                disambiguation_reason=disambiguation_reason,
                matched_at=datetime.utcnow().isoformat(),
                ai_provider=self.ai_provider if self.api_key else "none"
            ))

        # Ordenar por score descendente
        matches.sort(key=lambda x: x.relevance_score, reverse=True)

        return matches

    def _fuzzy_search_gazetteer(self, toponym: str, threshold: float = 0.85) -> list[dict]:
        """Búsqueda fuzzy en el gazetteer"""
        normalized_toponym = self._normalize_text(toponym)
        candidates = []

        for name, territories in self.gazetteer.items():
            score = fuzz.ratio(normalized_toponym, name) / 100.0
            if score >= threshold:
                candidates.extend(territories)

        return candidates

    def _calculate_relevance_score(
        self,
        detection: ToponymDetection,
        candidate: dict,
        full_context: str,
        source_region: Optional[str]
    ) -> dict[str, float]:
        """
        Calcula score de relevancia combinando múltiples señales

        Señales:
        - Posición: título vale más que contenido
        - Frecuencia: cuántas veces aparece el topónimo
        - Proximidad: qué tan cerca está de otros topónimos conocidos
        - Fuente: si la fuente es regional y coincide con el territorio
        - Nivel territorial: regiones suelen ser más específicas que comunas en noticias nacionales
        """
        scores = {}

        # 1. Score por posición (título > contenido)
        scores["position_score"] = 1.0 if detection.in_title else 0.5

        # 2. Score por método de detección
        method_scores = {
            "ai_ner_openai": 0.95,
            "ai_ner_anthropic": 0.95,
            "spacy_ner": 0.75,
            "regex_gazetteer": 0.6
        }
        scores["detection_method_score"] = method_scores.get(detection.method, 0.5)

        # 3. Score por confianza de detección
        scores["detection_confidence"] = detection.confidence

        # 4. Score por frecuencia (cuántas veces aparece el topónimo)
        frequency = full_context.lower().count(detection.toponym.lower())
        scores["frequency_score"] = min(frequency / 5.0, 1.0)  # Normalizar a max 5 menciones

        # 5. Score por fuente regional (si coincide)
        if source_region and candidate.get("region"):
            scores["source_region_score"] = 1.0 if source_region == candidate["region"] else 0.3
        else:
            scores["source_region_score"] = 0.5  # Neutral si no se conoce

        # 6. Score por nivel territorial (regiones > comunas para noticias nacionales)
        level_scores = {
            "región": 0.9,
            "comuna": 0.7,
            "localidad": 0.5
        }
        scores["level_score"] = level_scores.get(candidate["level"], 0.5)

        # 7. Calcular score final (promedio ponderado)
        weights = {
            "position_score": 0.25,
            "detection_method_score": 0.15,
            "detection_confidence": 0.15,
            "frequency_score": 0.20,
            "source_region_score": 0.15,
            "level_score": 0.10
        }

        final_score = sum(scores[k] * weights[k] for k in weights.keys())
        scores["final_score"] = round(final_score, 3)

        return scores

    def _generate_disambiguation_explanation(
        self,
        detection: ToponymDetection,
        candidate: dict,
        score_breakdown: dict,
        source_region: Optional[str]
    ) -> str:
        """Genera explicación legible de por qué se eligió este territorio"""
        parts = []

        # Detección
        parts.append(f"Detectado '{detection.toponym}' usando {detection.method}")

        # Matching
        if candidate["matched_via"] == candidate["name"]:
            parts.append(f"match exacto con '{candidate['name']}'")
        else:
            parts.append(f"match vía alias '{candidate['matched_via']}'")

        # Señales fuertes
        if detection.in_title:
            parts.append("aparece en título")

        if score_breakdown.get("frequency_score", 0) > 0.6:
            parts.append("alta frecuencia en texto")

        if source_region and candidate.get("region") == source_region:
            parts.append(f"fuente regional coincide ({source_region})")

        # Contexto
        if detection.context:
            parts.append(f"contexto: \"{detection.context[:60]}...\"")

        return "; ".join(parts)

    async def geoparse(
        self,
        title: str,
        content: str,
        source_region: Optional[str] = None,
        max_territories: int = 3
    ) -> list[TerritoryMatch]:
        """
        Pipeline completo de geosparsing

        Args:
            title: Título del contenido
            content: Contenido completo
            source_region: Región de la fuente (opcional, ayuda a desambiguar)
            max_territories: Número máximo de territorios a retornar

        Returns:
            Lista de territorios identificados con trazabilidad completa
        """
        # 1. Detectar topónimos
        detections = await self.detect_toponyms(title, content)

        if not detections:
            return []

        # 2. Resolver cada topónimo a territorios
        full_context = f"{title}\n\n{content}"
        all_matches = []

        for detection in detections:
            matches = self.resolve_territory(
                detection=detection,
                full_context=full_context,
                source_region=source_region
            )
            all_matches.extend(matches)

        # 3. Deduplicar y ordenar por relevancia
        # Agrupar por territorio_name y quedarse con el mejor score
        unique_matches = {}
        for match in all_matches:
            key = match.territory_name
            if key not in unique_matches or match.relevance_score > unique_matches[key].relevance_score:
                unique_matches[key] = match

        # Ordenar por score descendente
        final_matches = sorted(
            unique_matches.values(),
            key=lambda x: x.relevance_score,
            reverse=True
        )

        return final_matches[:max_territories]


# Funciones de conveniencia para usar en el pipeline


async def geoparse_with_ai(
    title: str,
    content: str,
    source_region: Optional[str] = None,
    ai_provider: Optional[str] = None,
    api_key: Optional[str] = None
) -> list[dict]:
    """
    Función de conveniencia para geosparsing con IA

    Returns:
        Lista de diccionarios serializables para almacenar en DB
    """
    geoparser = AIGeoparser(ai_provider=ai_provider, api_key=api_key)
    matches = await geoparser.geoparse(title, content, source_region)

    # Convertir a dict para serialización
    return [asdict(match) for match in matches]


def get_explainable_territories(
    title: str,
    content: str,
    source_region: Optional[str] = None
) -> dict:
    """
    Versión síncrona simplificada que retorna territorios con explicabilidad
    Útil para debugging y auditoría

    Returns:
        Dict con territorios y metadata de trazabilidad
    """
    import asyncio

    # Ejecutar de forma síncrona
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        matches = loop.run_until_complete(
            geoparse_with_ai(title, content, source_region)
        )

        return {
            "territories": matches,
            "total_detected": len(matches),
            "timestamp": datetime.utcnow().isoformat(),
            "explainable": True,
            "ai_enabled": bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
        }
    finally:
        loop.close()
