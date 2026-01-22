"""
Sistema de Geosparsing con IA para Detección de Topónimos
==========================================================

Este módulo implementa un sistema de geosparsing que:
1. Detecta topónimos (lugares) en español usando IA (OpenAI/Anthropic) o fallback spaCy/regex
2. Resuelve territorios usando un gazetteer (catálogo de territorios de Chile)
3. Maneja desambiguación y scoring explicable
4. Incluye un "country gate" para evitar asignar territorios de Chile a noticias fuera de Chile
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

import httpx
from rapidfuzz import fuzz

from app.core.config import settings
from app.data.chile_territories import CHILE_TERRITORIES

# ---------------------------------------------------------------------
# Country gate (Chile-only): señales simples para filtrar noticias fuera
# de Chile y reducir falsos positivos por homónimos.
# ---------------------------------------------------------------------

CHILE_CUES = [
    # País y gentilicio
    "chile",
    "chileno",
    "chilena",
    "chilenos",
    "chilenas",

    # Ciudades principales
    "santiago de chile",
    "santiago chile",
    "valparaíso",
    "valparaiso",
    "concepción",
    "concepcion",
    "temuco",
    "puerto montt",
    "antofagasta",
    "iquique",
    "arica",
    "la serena",
    "coquimbo",
    "rancagua",
    "talca",
    "chillán",
    "chillan",
    "los ángeles",
    "los angeles",
    "osorno",
    "valdivia",
    "punta arenas",
    "copiapó",
    "copiapo",
    "calama",
    "viña del mar",
    "vina del mar",

    # Instituciones gubernamentales
    "carabineros",
    "pdi",
    "la moneda",
    "palacio de la moneda",
    "seremi",
    "conaf",
    "sernageomin",
    "delegación presidencial",
    "delegacion presidencial",
    "gobierno regional",
    "gore",
    "minsal",
    "minvu",
    "mop",
    "sernapesca",
    "sii",
    "servicio de impuestos internos",
    "senado chile",
    "cámara de diputados",
    "camara de diputados",
    "congreso nacional",
    "tribunal constitucional",
    "poder judicial chile",
    "fiscalía nacional",
    "fiscalia nacional",
    "contraloría",
    "contraloria",
    "senapred",
    "onemi",
    "csirt chile",
    "anci",
    "superintendencia",
    "cmf",
    "comisión para el mercado financiero",
    "banco central de chile",
    "servel",
    "servicio electoral",

    # Términos administrativos chilenos
    "región",
    "region",
    "comuna",
    "municipalidad",
    "intendencia",

    # Términos geográficos específicos
    "cordillera de los andes chile",
    "desierto de atacama",
    "patagonia chilena",
    "isla de pascua",
    "rapa nui",
    "archipiélago juan fernández",
    "archipielago juan fernandez",
    "estrecho de magallanes",
]

FOREIGN_STRONG_CUES = [
    # Sudamérica
    "argentina",
    "argentino",
    "argentina",
    "buenos aires",
    "baires",
    "córdoba argentina",
    "cordoba argentina",
    "rosario",
    "mendoza argentina",
    "tucumán",
    "tucuman",
    "casa rosada",
    "perú",
    "peru",
    "peruano",
    "peruana",
    "lima",
    "lima perú",
    "lima peru",
    "arequipa",
    "cusco",
    "cuzco",
    "trujillo perú",
    "bolivia",
    "boliviano",
    "la paz",
    "la paz bolivia",
    "santa cruz bolivia",
    "cochabamba",
    "sucre bolivia",
    "brasil",
    "brazil",
    "brasileño",
    "brasileiro",
    "são paulo",
    "sao paulo",
    "rio de janeiro",
    "brasília",
    "brasilia",
    "salvador de bahía",
    "salvador de bahia",
    "belo horizonte",
    "fortaleza",
    "recife",
    "porto alegre",
    "uruguay",
    "uruguayo",
    "montevideo",
    "punta del este",
    "paraguay",
    "paraguayo",
    "asunción",
    "asuncion",
    "ciudad del este",
    "colombia",
    "colombiano",
    "bogotá",
    "bogota",
    "medellín",
    "medellin",
    "cali",
    "barranquilla",
    "cartagena colombia",
    "bucaramanga",
    "venezuela",
    "venezolano",
    "caracas",
    "maracaibo",
    "valencia venezuela",
    "barquisimeto",
    "ecuador",
    "ecuatoriano",
    "quito",
    "guayaquil",
    "cuenca ecuador",

    # Norteamérica
    "méxico",
    "mexico",
    "mexicano",
    "ciudad de méxico",
    "cdmx",
    "guadalajara",
    "monterrey",
    "puebla méxico",
    "tijuana",
    "cancún",
    "cancun",
    "estados unidos",
    "eeuu",
    "u.s.",
    "usa",
    "estadounidense",
    "new york",
    "nueva york",
    "miami",
    "washington",
    "washington dc",
    "los angeles",
    "chicago",
    "houston",
    "phoenix",
    "philadelphia",
    "san antonio",
    "san diego",
    "dallas",
    "san francisco",
    "seattle",
    "boston",
    "atlanta",
    "las vegas",
    "canadá",
    "canada",
    "canadiense",
    "toronto",
    "montreal",
    "vancouver",
    "ottawa",
    "calgary",

    # Europa
    "españa",
    "espana",
    "español",
    "espanol",
    "madrid",
    "madrid españa",
    "barcelona",
    "valencia españa",
    "sevilla",
    "zaragoza",
    "málaga",
    "malaga",
    "bilbao",
    "francia",
    "francés",
    "frances",
    "parís",
    "paris",
    "marsella",
    "lyon",
    "toulouse",
    "niza",
    "reino unido",
    "inglaterra",
    "británico",
    "britanico",
    "londres",
    "london",
    "manchester",
    "liverpool",
    "birmingham",
    "italia",
    "italiano",
    "roma",
    "milán",
    "milan",
    "nápoles",
    "napoles",
    "turín",
    "turin",
    "florencia",
    "venecia",
    "alemania",
    "alemán",
    "aleman",
    "berlín",
    "berlin",
    "múnich",
    "munich",
    "frankfurt",
    "hamburgo",
    "colonia",
    "portugal",
    "portugués",
    "portugues",
    "lisboa",
    "oporto",
    "países bajos",
    "paises bajos",
    "holanda",
    "ámsterdam",
    "amsterdam",
    "rotterdam",
    "bélgica",
    "belgica",
    "bruselas",
    "amberes",
    "suiza",
    "suizo",
    "ginebra",
    "zúrich",
    "zurich",
    "berna",
    "austria",
    "austríaco",
    "viena",
    "salzburgo",
    "grecia",
    "griego",
    "atenas",
    "tesalónica",
    "rusia",
    "ruso",
    "moscú",
    "moscu",
    "san petersburgo",

    # Asia
    "china",
    "chino",
    "pekín",
    "pekin",
    "beijing",
    "shanghai",
    "hong kong",
    "japón",
    "japon",
    "japonés",
    "japones",
    "tokio",
    "osaka",
    "kioto",
    "india",
    "indio",
    "nueva delhi",
    "bombay",
    "mumbai",
    "bangalore",
    "tailandia",
    "tailandés",
    "bangkok",
    "camboya",
    "camboyano",
    "phnom penh",
    "vietnam",
    "vietnamita",
    "hanoi",
    "ho chi minh",
    "saigón",
    "saigon",
    "corea del sur",
    "coreano",
    "seúl",
    "seoul",
    "busan",
    "indonesia",
    "indonesio",
    "yakarta",
    "jakarta",
    "filipinas",
    "filipino",
    "manila",

    # Medio Oriente
    "israel",
    "israelí",
    "israeli",
    "jerusalén",
    "jerusalem",
    "tel aviv",
    "arabia saudita",
    "arabia saudí",
    "riad",
    "yeda",
    "emiratos árabes",
    "emiratos arabes",
    "dubái",
    "dubai",
    "abu dhabi",
    "turquía",
    "turquia",
    "turco",
    "estambul",
    "ankara",
    "irán",
    "iran",
    "iraní",
    "irani",
    "teherán",
    "tehran",
    "irak",
    "iraquí",
    "bagdad",

    # África
    "sudáfrica",
    "sudafrica",
    "sudafricano",
    "johannesburgo",
    "ciudad del cabo",
    "pretoria",
    "egipto",
    "egipcio",
    "el cairo",
    "alejandría",
    "alejandria",
    "nigeria",
    "nigeriano",
    "lagos",
    "abuja",
    "kenia",
    "keniano",
    "nairobi",
    "marruecos",
    "marroquí",
    "rabat",
    "casablanca",

    # Oceanía
    "australia",
    "australiano",
    "sídney",
    "sidney",
    "sydney",
    "melbourne",
    "brisbane",
    "perth",
    "nueva zelanda",
    "nueva zelandia",
    "auckland",
    "wellington",

    # Otros
    "caribe",
    "puerto rico",
    "cuba",
    "habana",
    "república dominicana",
    "santo domingo",
    "panamá",
    "panama",
]


def _contains_any(text: str, terms: list[str]) -> bool:
    t = (text or "").lower()
    return any(term in t for term in terms)


def _url_looks_chilean(url: Optional[str]) -> bool:
    """
    Señales por URL que sugieren Chile.

    IMPORTANTE:
    - Google News (news.google.com) NO sirve para decidir país aunque tenga ceid=CL.
      Los feeds de Chile incluyen noticias internacionales.
    """
    if not url:
        return False

    u = url.lower()

    # Google News NO es evidencia de país
    if "news.google.com" in u:
        return False

    # Señal fuerte: dominio chileno real
    return (u.endswith(".cl") or ".cl/" in u)


@dataclass
class ToponymDetection:
    """Representa un topónimo detectado en el texto"""

    toponym: str
    position_start: int
    position_end: int
    context: str
    in_title: bool
    method: str
    confidence: float


@dataclass
class TerritoryMatch:
    """Representa un territorio mapeado con trazabilidad"""

    territory_name: str
    territory_level: str
    latitude: Optional[float]
    longitude: Optional[float]

    detected_toponym: str
    toponym_position: int
    toponym_context: str

    relevance_score: float
    scoring_breakdown: dict[str, float]

    mapping_method: str
    disambiguation_reason: Optional[str]

    matched_at: str
    ai_provider: Optional[str]


class AIGeoparser:
    """
    Parser geográfico con IA para detección y resolución de topónimos.
    Incluye filtros para Chile-only (country gate) para reducir falsos positivos.
    """

    def __init__(
        self,
        ai_provider: Optional[str] = None,
        api_key: Optional[str] = None,
        use_spacy_fallback: bool = True,
    ):
        self.ai_provider = ai_provider or (settings.ai_provider or "openai")
        self.api_key = api_key or self._get_api_key_from_settings()
        self.use_spacy_fallback = use_spacy_fallback
        self.spacy_model = None

        self.openai_model = settings.openai_model or "gpt-4o-mini"
        self.openai_base_url = (
            settings.openai_base_url or "https://api.openai.com/v1").rstrip("/")

        self.gazetteer = self._build_gazetteer()

        if self.use_spacy_fallback and not self.api_key:
            self._load_spacy_model()

    def _get_api_key_from_settings(self) -> Optional[str]:
        if self.ai_provider == "openai":
            return settings.openai_api_key
        if self.ai_provider == "anthropic":
            return settings.anthropic_api_key
        return None

    def _load_spacy_model(self):
        try:
            import spacy

            try:
                self.spacy_model = spacy.load("es_core_news_sm")
            except OSError:
                try:
                    self.spacy_model = spacy.load("es_core_news_md")
                except OSError:
                    print(
                        "⚠️  No se pudo cargar modelo spaCy. Instalar con: python -m spacy download es_core_news_sm")
                    self.spacy_model = None
        except ImportError:
            print("⚠️  spaCy no está instalado")
            self.spacy_model = None

    def _build_gazetteer(self) -> dict[str, list[dict]]:
        gazetteer: dict[str, list[dict]] = {}
        for region in CHILE_TERRITORIES:
            for name in [region["name"]] + region.get("aliases", []):
                normalized = self._normalize_text(name)
                gazetteer.setdefault(normalized, []).append(
                    {
                        "name": region["name"],
                        "level": region["level"],
                        "lat": region["lat"],
                        "lon": region["lon"],
                        "region": region["name"],
                        "matched_via": name,
                    }
                )

            for comuna in region.get("comunas", []):
                for name in [comuna["name"]] + comuna.get("aliases", []):
                    normalized = self._normalize_text(name)
                    gazetteer.setdefault(normalized, []).append(
                        {
                            "name": comuna["name"],
                            "level": "comuna",
                            "lat": comuna["lat"],
                            "lon": comuna["lon"],
                            "region": region["name"],
                            "matched_via": name,
                        }
                    )
        return gazetteer

    @staticmethod
    def _normalize_text(text: str) -> str:
        import unicodedata

        text = text.lower()
        text = "".join(c for c in unicodedata.normalize(
            "NFD", text) if unicodedata.category(c) != "Mn")
        return text

    # ------------------------------------------------------------------
    # Country gate (Chile-only)
    # ------------------------------------------------------------------

    def _is_chile_related_heuristic(self, title: str, content: str, url: Optional[str] = None) -> bool:
        """
        Filtro mejorado para determinar si una noticia es relevante para Chile.
        ESTRATEGIA CONSERVADORA: preferimos NO asignar territorios a evitar falsos positivos.

        Reglas:
        1. URL .cl fuerte → Chile (a menos que haya señal fuerte de país extranjero)
        2. Palabras clave de Chile en título → Mayor peso
        3. Si hay palabras clave extranjeras, requiere señales MUY claras de Chile
        4. En caso de ambigüedad → NO asignar territorios
        """
        title_lower = title.lower()
        content_lower = content.lower()
        full = f"{title}\n{content}".lower()

        # 1. Verificar URL
        url_is_chilean = _url_looks_chilean(url)

        # 2. Buscar señales de Chile y países extranjeros
        has_chile_in_title = _contains_any(title_lower, CHILE_CUES)
        has_chile_in_content = _contains_any(content_lower, CHILE_CUES)
        has_chile = has_chile_in_title or has_chile_in_content

        has_foreign_in_title = _contains_any(title_lower, FOREIGN_STRONG_CUES)
        has_foreign_in_content = _contains_any(content_lower, FOREIGN_STRONG_CUES)
        has_foreign = has_foreign_in_title or has_foreign_in_content

        # 3. Caso 1: URL chilena SIN señales extranjeras en título → Chile
        if url_is_chilean and not has_foreign_in_title:
            return True

        # 4. Caso 2: Señales de Chile en título Y NO hay señales extranjeras en título → Chile
        if has_chile_in_title and not has_foreign_in_title:
            return True

        # 5. Caso 3: Señales extranjeras MUY fuertes (en título) → NO Chile
        if has_foreign_in_title:
            # Solo aceptar si hay señales MUY claras de Chile (palabra "chile" explícita)
            chile_explicit = any(
                term in title_lower for term in ["chile", "chileno", "chilena", "chilenos", "chilenas"]
            )
            if not chile_explicit:
                return False

        # 6. Caso 4: Señales de Chile en contenido pero también extranjeras → Requiere más evidencia
        if has_chile_in_content and has_foreign_in_content:
            # Solo aceptar si hay múltiples señales de Chile
            chile_count = sum(1 for term in CHILE_CUES if term in full)
            foreign_count = sum(1 for term in FOREIGN_STRONG_CUES if term in full)

            # Requiere al menos 2x más señales de Chile que extranjeras
            if chile_count < foreign_count * 2:
                return False

        # 7. Caso 5: Solo señales de Chile, sin extranjeras → Chile
        if has_chile and not has_foreign:
            return True

        # 8. Caso 6: Solo señales extranjeras → NO Chile
        if has_foreign and not has_chile:
            return False

        # 9. Por defecto: conservador → NO asignar
        return False

    async def _is_chile_related_ai(self, title: str, content: str) -> bool:
        """
        Clasificador IA ultra-corto: responde CHILE o NO_CHILE.
        Se usa solo cuando hay API key OpenAI. Si falla, retorna False.
        """
        if not self.api_key or self.ai_provider != "openai":
            return False

        prompt = f"""
Responde SOLO con una palabra: CHILE o NO_CHILE.

¿La siguiente noticia ocurre principalmente en Chile (lugar del hecho principal)?

TITULO: {title}
TEXTO: {content[:1500]}
""".strip()

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    f"{self.openai_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.openai_model,
                        "messages": [
                            {"role": "system", "content": "Clasificador geográfico. Respondes solo CHILE o NO_CHILE."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.0,
                        "max_tokens": 5,
                    },
                )

                if resp.status_code != 200:
                    return False

                out = resp.json()[
                    "choices"][0]["message"]["content"].strip().upper()
                return out.startswith("CHILE")
        except Exception:
            return False

    async def is_chile_related(self, title: str, content: str, url: Optional[str] = None) -> bool:
        heuristic = self._is_chile_related_heuristic(title, content, url=url)
        if heuristic:
            return True

        # Intento IA para rescatar casos chilenos sin cues obvias
        if self.api_key and self.ai_provider == "openai":
            return await self._is_chile_related_ai(title, content)

        return False

    # ------------------------------------------------------------------
    # Toponym detection
    # ------------------------------------------------------------------

    async def detect_toponyms(self, title: str, content: str) -> list[ToponymDetection]:
        full_text = f"{title}\n\n{content}"

        if self.api_key:
            if self.ai_provider == "openai":
                return await self._detect_toponyms_openai(title, content, full_text)
            if self.ai_provider == "anthropic":
                return await self._detect_toponyms_anthropic(title, content, full_text)

        if self.spacy_model:
            return self._detect_toponyms_spacy(title, content, full_text)

        return self._detect_toponyms_regex(title, content, full_text)

    async def _detect_toponyms_openai(self, title: str, content: str, full_text: str) -> list[ToponymDetection]:
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

        url = f"{self.openai_base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.openai_model,
                        "messages": [
                            {"role": "system", "content": "Eres un sistema NER experto en detectar lugares. Respondes solo JSON."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1000,
                    },
                )

                if resp.status_code != 200:
                    print(f"❌ OpenAI error {resp.status_code}: {resp.text}")
                    return []

                result = resp.json()
                content_text = result["choices"][0]["message"]["content"]

                json_match = re.search(r"\{.*\}", content_text, re.DOTALL)
                if not json_match:
                    print("⚠️ OpenAI respondió sin JSON parseable")
                    return []

                data = json.loads(json_match.group())

                detections: list[ToponymDetection] = []
                for item in data.get("toponyms", []):
                    toponym = str(item.get("toponym", "")).strip()
                    if not toponym:
                        continue

                    position = full_text.lower().find(toponym.lower())
                    if position == -1:
                        position = int(item.get("position", 0) or 0)

                    in_title = toponym.lower() in title.lower()
                    context = self._extract_context(full_text, position, 50)

                    detections.append(
                        ToponymDetection(
                            toponym=toponym,
                            position_start=position,
                            position_end=position + len(toponym),
                            context=context,
                            in_title=in_title,
                            method="ai_ner_openai",
                            confidence=0.9,
                        )
                    )

                return detections

        except Exception as e:
            print(f"❌ Error en detección OpenAI: {e}")
            return []

    async def _detect_toponyms_anthropic(self, title: str, content: str, full_text: str) -> list[ToponymDetection]:
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
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.anthropic_model or "claude-3-5-sonnet-20241022",
                        "max_tokens": 1000,
                        "temperature": 0.1,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )

                if resp.status_code != 200:
                    print(f"❌ Anthropic error {resp.status_code}: {resp.text}")
                    return []

                result = resp.json()
                content_text = result["content"][0]["text"]

                json_match = re.search(r"\{.*\}", content_text, re.DOTALL)
                if not json_match:
                    return []

                data = json.loads(json_match.group())

                detections: list[ToponymDetection] = []
                for item in data.get("toponyms", []):
                    toponym = str(item.get("toponym", "")).strip()
                    if not toponym:
                        continue

                    position = full_text.lower().find(toponym.lower())
                    if position == -1:
                        position = int(item.get("position", 0) or 0)

                    in_title = toponym.lower() in title.lower()
                    context = self._extract_context(full_text, position, 50)

                    detections.append(
                        ToponymDetection(
                            toponym=toponym,
                            position_start=position,
                            position_end=position + len(toponym),
                            context=context,
                            in_title=in_title,
                            method="ai_ner_anthropic",
                            confidence=0.9,
                        )
                    )

                return detections

        except Exception as e:
            print(f"❌ Error en detección Anthropic: {e}")
            return []

    def _detect_toponyms_spacy(self, title: str, content: str, full_text: str) -> list[ToponymDetection]:
        if not self.spacy_model:
            return []

        detections: list[ToponymDetection] = []
        doc = self.spacy_model(full_text[:10000])

        for ent in doc.ents:
            if ent.label_ not in ["LOC", "GPE"]:
                continue

            toponym = ent.text
            position = ent.start_char
            in_title = toponym.lower() in title.lower()
            context = self._extract_context(full_text, position, 50)

            detections.append(
                ToponymDetection(
                    toponym=toponym,
                    position_start=position,
                    position_end=ent.end_char,
                    context=context,
                    in_title=in_title,
                    method="spacy_ner",
                    confidence=0.75,
                )
            )

        return detections

    def _detect_toponyms_regex(self, title: str, content: str, full_text: str) -> list[ToponymDetection]:
        detections: list[ToponymDetection] = []

        for normalized_name, territories in self.gazetteer.items():
            original_name = territories[0]["matched_via"]
            pattern = re.compile(
                r"\b" + re.escape(original_name) + r"\b", re.IGNORECASE)

            for match in pattern.finditer(full_text):
                position = match.start()
                toponym = match.group()
                in_title = toponym.lower() in title.lower()
                context = self._extract_context(full_text, position, 50)

                detections.append(
                    ToponymDetection(
                        toponym=toponym,
                        position_start=position,
                        position_end=match.end(),
                        context=context,
                        in_title=in_title,
                        method="regex_gazetteer",
                        confidence=0.6,
                    )
                )

        return detections

    @staticmethod
    def _extract_context(text: str, position: int, window: int = 50) -> str:
        start = max(0, position - window)
        end = min(len(text), position + window)
        context = text[start:end]
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."
        return context.strip()

    # ------------------------------------------------------------------
    # Territory resolution
    # ------------------------------------------------------------------

    def resolve_territory(
        self,
        detection: ToponymDetection,
        full_context: str,
        source_region: Optional[str] = None,
    ) -> list[TerritoryMatch]:
        normalized_toponym = self._normalize_text(detection.toponym)

        candidates = self.gazetteer.get(normalized_toponym, [])
        if not candidates:
            candidates = self._fuzzy_search_gazetteer(detection.toponym)

        if not candidates:
            return []

        matches: list[TerritoryMatch] = []
        for candidate in candidates:
            score_breakdown = self._calculate_relevance_score(
                detection, candidate, full_context, source_region)
            final_score = score_breakdown["final_score"]

            if self._normalize_text(candidate["matched_via"]) == normalized_toponym:
                mapping_method = "exact_match" if candidate[
                    "matched_via"] == candidate["name"] else "alias_match"
            else:
                mapping_method = "fuzzy_match"

            reason = self._generate_disambiguation_explanation(
                detection, candidate, score_breakdown, source_region)

            matches.append(
                TerritoryMatch(
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
                    disambiguation_reason=reason,
                    matched_at=datetime.utcnow().isoformat(),
                    ai_provider=self.ai_provider if self.api_key else "none",
                )
            )

        matches.sort(key=lambda x: x.relevance_score, reverse=True)
        return matches

    def _fuzzy_search_gazetteer(self, toponym: str, threshold: float = 0.85) -> list[dict]:
        normalized_toponym = self._normalize_text(toponym)
        candidates: list[dict] = []

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
        source_region: Optional[str],
    ) -> dict[str, float]:
        scores: dict[str, float] = {}

        scores["position_score"] = 1.0 if detection.in_title else 0.5

        method_scores = {
            "ai_ner_openai": 0.95,
            "ai_ner_anthropic": 0.95,
            "spacy_ner": 0.75,
            "regex_gazetteer": 0.6,
        }
        scores["detection_method_score"] = method_scores.get(
            detection.method, 0.5)

        scores["detection_confidence"] = detection.confidence

        frequency = full_context.lower().count(detection.toponym.lower())
        scores["frequency_score"] = min(frequency / 5.0, 1.0)

        if source_region and candidate.get("region"):
            scores["source_region_score"] = 1.0 if source_region == candidate["region"] else 0.3
        else:
            scores["source_region_score"] = 0.5

        level_scores = {"región": 0.9, "comuna": 0.7, "localidad": 0.5}
        scores["level_score"] = level_scores.get(candidate["level"], 0.5)

        weights = {
            "position_score": 0.25,
            "detection_method_score": 0.15,
            "detection_confidence": 0.15,
            "frequency_score": 0.20,
            "source_region_score": 0.15,
            "level_score": 0.10,
        }

        final_score = sum(scores[k] * weights[k] for k in weights.keys())
        scores["final_score"] = round(final_score, 3)
        return scores

    def _generate_disambiguation_explanation(
        self,
        detection: ToponymDetection,
        candidate: dict,
        score_breakdown: dict,
        source_region: Optional[str],
    ) -> str:
        parts: list[str] = []

        parts.append(
            f"Detectado '{detection.toponym}' usando {detection.method}")

        if candidate["matched_via"] == candidate["name"]:
            parts.append(f"match exacto con '{candidate['name']}'")
        else:
            parts.append(f"match vía alias '{candidate['matched_via']}'")

        if detection.in_title:
            parts.append("aparece en título")

        if score_breakdown.get("frequency_score", 0) > 0.6:
            parts.append("alta frecuencia en texto")

        if source_region and candidate.get("region") == source_region:
            parts.append(f"fuente regional coincide ({source_region})")

        if detection.context:
            parts.append(f'contexto: "{detection.context[:60]}..."')

        return "; ".join(parts)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def geoparse(
        self,
        title: str,
        content: str,
        source_region: Optional[str] = None,
        max_territories: int = 3,
        url: Optional[str] = None,
        require_chile: bool = True,
    ) -> list[TerritoryMatch]:
        # Country gate: si no parece Chile, no asignamos territorios de Chile
        if require_chile:
            ok = await self.is_chile_related(title, content, url=url)
            if not ok:
                return []

        detections = await self.detect_toponyms(title, content)
        if not detections:
            return []

        full_context = f"{title}\n\n{content}"
        all_matches: list[TerritoryMatch] = []

        for detection in detections:
            all_matches.extend(
                self.resolve_territory(
                    detection=detection, full_context=full_context, source_region=source_region)
            )

        unique_matches: dict[str, TerritoryMatch] = {}
        for match in all_matches:
            key = match.territory_name
            if key not in unique_matches or match.relevance_score > unique_matches[key].relevance_score:
                unique_matches[key] = match

        final_matches = sorted(unique_matches.values(),
                               key=lambda x: x.relevance_score, reverse=True)
        return final_matches[:max_territories]


async def geoparse_with_ai(
    title: str,
    content: str,
    source_region: Optional[str] = None,
    ai_provider: Optional[str] = None,
    api_key: Optional[str] = None,
    url: Optional[str] = None,
) -> list[dict]:
    """
    Wrapper simple que devuelve dicts (para endpoints/serialización).
    Backward compatible: si no pasas url, igual funciona.
    """
    geoparser = AIGeoparser(ai_provider=ai_provider, api_key=api_key)
    matches = await geoparser.geoparse(title, content, source_region, url=url, require_chile=True)
    return [asdict(match) for match in matches]


def get_explainable_territories(title: str, content: str, source_region: Optional[str] = None) -> dict:
    import asyncio

    async def _run():
        return await geoparse_with_ai(title, content, source_region)

    try:
        matches = asyncio.run(_run())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            matches = loop.run_until_complete(_run())
        finally:
            loop.close()

    return {
        "territories": matches,
        "total_detected": len(matches),
        "timestamp": datetime.utcnow().isoformat(),
        "explainable": True,
        "ai_enabled": bool(settings.openai_api_key or settings.anthropic_api_key),
    }
