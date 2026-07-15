import os
import json
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
OLLAMA_CHAT_ENDPOINT = "/api/chat"
REQUEST_TIMEOUT = 60


class LLMError(Exception):
    pass


def _call_groq(system_prompt: str, user_prompt: str, temperature: float) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    if not api_key:
        raise LLMError("GROQ_API_KEY manquant dans .env")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        raise LLMError(f"Erreur Groq API ({response.status_code}): {response.text[:300]}")

    data = response.json()
    return data["choices"][0]["message"]["content"]


def _call_ollama(system_prompt: str, user_prompt: str, temperature: float) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.1")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": temperature},
    }

    try:
        response = requests.post(f"{base_url}{OLLAMA_CHAT_ENDPOINT}", json=payload, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        raise LLMError(f"Ollama injoignable sur {base_url}. Est-il lancé ? Détail: {e}")

    if response.status_code != 200:
        raise LLMError(f"Erreur Ollama ({response.status_code}): {response.text[:300]}")

    data = response.json()
    return data["message"]["content"]


def call_llm_json(system_prompt: str, user_prompt: str, temperature: float = 0.4) -> dict:
   
    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "groq":
        raw_content = _call_groq(system_prompt, user_prompt, temperature)
    elif provider == "ollama":
        raw_content = _call_ollama(system_prompt, user_prompt, temperature)
    else:
        raise LLMError(f"LLM_PROVIDER invalide: '{provider}' (attendu: 'groq' ou 'ollama')")

    try:
        return json.loads(raw_content)
    except json.JSONDecodeError as e:
        raise LLMError(f"Le LLM a renvoyé un JSON invalide: {str(e)} | contenu brut: {raw_content[:300]}")