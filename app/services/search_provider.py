import os
import time
import logging
import requests

logger = logging.getLogger(__name__)

SERPER_API_URL = "https://google.serper.dev/search"
REQUEST_TIMEOUT = 15


def _search_serper(query: str, max_results: int) -> list:
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        logger.error("SERPER_API_KEY manquant dans .env")
        return []

    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": max_results, "gl": "fr", "hl": "fr"}

    try:
        response = requests.post(SERPER_API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error(f"Erreur Serper API: {str(e)}")
        return []

    organic_results = data.get("organic", [])
    results = [
        {"title": item.get("title", ""), "url": item.get("link")}
        for item in organic_results if item.get("link")
    ]
    logger.info(f"Serper a retourné {len(results)} résultat(s) pour '{query}'")
    return results


def _search_ddgs(query: str, max_results: int) -> list:
    """Tentative de secours gratuite (peut être bloquée par DuckDuckGo, non garantie)."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            raw_hits = list(ddgs.text(query, region="fr-fr", max_results=max_results))
        results = [
            {"title": hit.get("title", ""), "url": hit.get("href") or hit.get("url")}
            for hit in raw_hits if hit.get("href") or hit.get("url")
        ]
        logger.info(f"DuckDuckGo (secours) a retourné {len(results)} résultat(s) pour '{query}'")
        return results
    except Exception as e:
        logger.error(f"Erreur DuckDuckGo (secours): {str(e)}")
        return []


def search_web(query: str, max_results: int = 10) -> list:
    """Point d'entrée unique de recherche web. Bascule entre providers via .env."""
    provider = os.getenv("SEARCH_PROVIDER", "serper").lower()

    if provider == "serper":
        results = _search_serper(query, max_results)
        if not results:
            logger.warning("Serper n'a rien retourné, tentative de secours via DuckDuckGo...")
            results = _search_ddgs(query, max_results)
        return results

    elif provider == "ddgs":
        return _search_ddgs(query, max_results)

    else:
        logger.error(f"SEARCH_PROVIDER invalide: '{provider}'")
        return []