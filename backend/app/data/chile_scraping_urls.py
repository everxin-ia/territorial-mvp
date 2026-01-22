# app/data/chile_scraping_urls.py
"""
URLs clave de instituciones públicas chilenas para scraping.
Organizadas por categoría para facilitar la integración futura.
"""

from typing import TypedDict


class ScrapingURL(TypedDict):
    name: str
    url: str
    category: str
    description: str
    requires_api: bool
    api_docs: str | None


CHILE_SCRAPING_URLS: list[ScrapingURL] = [
    # ========================================
    # A) DATOS ABIERTOS Y ESTADÍSTICAS
    # ========================================
    {
        "name": "Portal de Datos Abiertos Chile (CKAN API)",
        "url": "https://datos.gob.cl/es_AR/api/1/util/snippet/api_info.html?resource_id=d34b6a86-4e31-4624-aa42-1bd87a29a8c2",
        "category": "datos_abiertos",
        "description": "Portal nacional de datos abiertos con API CKAN. Usar endpoints: /api/3/action/package_search, datastore_search",
        "requires_api": True,
        "api_docs": "https://docs.ckan.org/en/2.9/api/index.html",
    },
    {
        "name": "Banco Central de Chile - Base de Datos Estadísticos (API)",
        "url": "https://si3.bcentral.cl/estadisticas/Principal1/Web_Services/doc_es.htm",
        "category": "datos_abiertos",
        "description": "Estadísticas económicas y financieras de Chile. Requiere registro/credenciales.",
        "requires_api": True,
        "api_docs": "https://si3.bcentral.cl/estadisticas/Principal1/Web_Services/doc_es.htm",
    },
    {
        "name": "INE - Sala de Prensa",
        "url": "https://www.ine.gob.cl/sala-de-prensa/prensa/general/noticia",
        "category": "datos_abiertos",
        "description": "Comunicados de prensa del Instituto Nacional de Estadísticas (scraping HTML)",
        "requires_api": False,
        "api_docs": None,
    },
    {
        "name": "INE - Redatam",
        "url": "https://redatam-ine.ine.cl/",
        "category": "datos_abiertos",
        "description": "Plataforma de diseminación de datos censales y encuestas (extracción tabular)",
        "requires_api": False,
        "api_docs": None,
    },

    # ========================================
    # B) ELECCIONES Y DATOS ELECTORALES
    # ========================================
    {
        "name": "SERVEL - Servicio Electoral",
        "url": "https://www.servel.cl/",
        "category": "elecciones",
        "description": "Portal del Servicio Electoral de Chile. Incluye resultados históricos y consultas.",
        "requires_api": False,
        "api_docs": None,
    },
    {
        "name": "BCN - Resultados Electorales",
        "url": "https://www.bcn.cl/siit/actualidad-territorial/resultados-electorales",
        "category": "elecciones",
        "description": "Biblioteca del Congreso Nacional - resultados oficiales de elecciones (verificación)",
        "requires_api": False,
        "api_docs": None,
    },

    # ========================================
    # C) LEGAL / NORMATIVO / PUBLICACIONES OFICIALES
    # ========================================
    {
        "name": "Diario Oficial",
        "url": "https://www.diariooficial.interior.gob.cl/publicacion",
        "category": "legal",
        "description": "Portal de publicaciones oficiales del Estado de Chile",
        "requires_api": False,
        "api_docs": None,
    },
    {
        "name": "BCN LeyChile",
        "url": "https://www.bcn.cl/leychile/",
        "category": "legal",
        "description": "Portal de normativa consolidada de Chile",
        "requires_api": False,
        "api_docs": None,
    },

    # ========================================
    # D) REGULADORES Y SUPERVISORES
    # ========================================
    {
        "name": "CMF - Comisión para el Mercado Financiero",
        "url": "https://www.cmfchile.cl/portal/principal/613/w3-channel.html",
        "category": "reguladores",
        "description": "Comunicados y noticias del regulador financiero chileno",
        "requires_api": False,
        "api_docs": None,
    },

    # ========================================
    # E) RIESGO, EMERGENCIAS Y AMENAZAS
    # ========================================
    {
        "name": "Centro Sismológico Nacional (CSN) - Listado de Sismos",
        "url": "https://www.sismologia.cl/",
        "category": "emergencias",
        "description": "Listado de sismos recientes en Chile (scraping HTML)",
        "requires_api": False,
        "api_docs": None,
    },
    {
        "name": "API Pública de Sismos Chile",
        "url": "https://api.gael.cloud/general/public/sismos",
        "category": "emergencias",
        "description": "Endpoint JSON alternativo para sismos en Chile. Verificar condiciones de uso.",
        "requires_api": True,
        "api_docs": "https://api.gael.cloud/general/public/sismos",
    },
    {
        "name": "SERNAGEOMIN - Servicio Nacional de Geología y Minería",
        "url": "https://www.sernageomin.cl/",
        "category": "emergencias",
        "description": "Noticias de geología, minería y riesgos naturales",
        "requires_api": False,
        "api_docs": None,
    },
    {
        "name": "ANCI - Agencia Nacional de Ciberseguridad",
        "url": "https://anci.gob.cl/",
        "category": "emergencias",
        "description": "Noticias y eventos de ciberseguridad nacional",
        "requires_api": False,
        "api_docs": None,
    },
    {
        "name": "SENAPRED - Sistema Nacional de Prevención y Respuesta ante Desastres",
        "url": "https://web.senapred.cl/",
        "category": "emergencias",
        "description": "Alertas y comunicados de emergencias y desastres naturales",
        "requires_api": False,
        "api_docs": None,
    },

    # ========================================
    # F) MEDIOS Y MEDIOS TERRITORIALES
    # ========================================
    {
        "name": "Cooperativa - RSS",
        "url": "https://www.cooperativa.cl/noticias/stat/rss/rss.html",
        "category": "medios",
        "description": "Página de selección de feeds RSS de Radio Cooperativa (varios feeds disponibles)",
        "requires_api": False,
        "api_docs": None,
    },
    {
        "name": "BioBioChile - RSS",
        "url": "https://www.biobiochile.cl/lista/tag/rss",
        "category": "medios",
        "description": "Punto de entrada a RSS de BioBioChile (varios feeds por región)",
        "requires_api": False,
        "api_docs": None,
    },
    {
        "name": "La Tercera - RSS",
        "url": "https://www.latercera.com/etiqueta/rss/",
        "category": "medios",
        "description": "Página RSS de La Tercera (varios feeds disponibles)",
        "requires_api": False,
        "api_docs": None,
    },
]


def get_urls_by_category(category: str) -> list[ScrapingURL]:
    """
    Retorna URLs filtradas por categoría.

    Categorías disponibles:
    - datos_abiertos: Portales de datos, estadísticas, APIs
    - elecciones: SERVEL, resultados electorales
    - legal: Diario Oficial, LeyChile
    - reguladores: CMF, superintendencias
    - emergencias: Sismos, SENAPRED, ANCI, SERNAGEOMIN
    - medios: Cooperativa, BioBio, La Tercera
    """
    return [url for url in CHILE_SCRAPING_URLS if url["category"] == category]


def get_api_urls() -> list[ScrapingURL]:
    """Retorna solo URLs que requieren API."""
    return [url for url in CHILE_SCRAPING_URLS if url["requires_api"]]


def get_scraping_urls() -> list[ScrapingURL]:
    """Retorna solo URLs para scraping HTML."""
    return [url for url in CHILE_SCRAPING_URLS if not url["requires_api"]]
