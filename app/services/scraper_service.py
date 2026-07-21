import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

MAX_CHARS = 6000
REQUEST_TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (compatible; FastriomLeadBot/1.0; +https://fastriom.com/bot)"
ABOUT_KEYWORDS = ["about", "a-propos", "qui-sommes-nous", "notre-histoire", "about-us", "who-we-are"]


class WebsiteScraper:
    """
    Scraper HTTP léger et robuste pour analyser la landing page et la page
    'A propos' d'un prospect. Utilisé comme outil par le futur agent
    Researcher (LangGraph, Sprint 3).
    """

    def __init__(self, timeout: int = REQUEST_TIMEOUT, max_chars: int = MAX_CHARS):
        self.timeout = timeout
        self.max_chars = max_chars
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({"User-Agent": USER_AGENT})
        return session

    def _clean_text(self, soup: BeautifulSoup) -> str:
        """Supprime le bruit (scripts, styles) et tronque pour protéger
        le context window des futurs LLM """
        for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        return text[: self.max_chars]

    def _find_about_page_url(self, base_url: str, soup: BeautifulSoup) -> str | None:
        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            if any(keyword in href for keyword in ABOUT_KEYWORDS):
                return href if href.startswith("http") else urljoin(base_url, href)
        return None

    def scrape(self, url: str) -> dict:
        result = {
            "url": url,
            "success": False,
            "title": None,
            "meta_description": None,
            "homepage_text": None,
            "about_page_url": None,
            "about_page_text": None,
            "error": None,
        }

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            result["title"] = soup.title.string.strip() if soup.title and soup.title.string else None
            meta_tag = soup.find("meta", attrs={"name": "description"})
            result["meta_description"] = meta_tag["content"].strip() if meta_tag and meta_tag.get("content") else None
            result["homepage_text"] = self._clean_text(soup)

            about_url = self._find_about_page_url(url, soup)
            if about_url:
                try:
                    about_response = self.session.get(about_url, timeout=self.timeout)
                    about_response.raise_for_status()
                    about_soup = BeautifulSoup(about_response.text, "lxml")
                    result["about_page_url"] = about_url
                    result["about_page_text"] = self._clean_text(about_soup)
                except requests.RequestException:
                    pass  # Page "About" optionnelle, échec silencieux

            result["success"] = True

        except requests.RequestException as e:
            result["error"] = f"Erreur réseau: {str(e)}"
        except Exception as e:
            result["error"] = f"Erreur de parsing: {str(e)}"

        return result