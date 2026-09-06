import os
import json
import uuid
import threading

CONFIG_PATH = "config/search_targets.json"
_file_lock = threading.Lock()


class SearchTargetsConfigError(Exception):
    pass


def _read_raw_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {"targets": [], "max_results_per_target": 8}

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_raw_config(config: dict) -> None:
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    tmp_path = CONFIG_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, CONFIG_PATH)  # écriture atomique : évite un fichier corrompu en cas de crash


def _ensure_ids(config: dict) -> dict:
    """Attribue un id stable à chaque target qui n'en a pas encore
    (ex: entrées historiques créées avant l'ajout de ce champ)."""
    changed = False
    for target in config.get("targets", []):
        if "id" not in target:
            target["id"] = uuid.uuid4().hex[:12]
            changed = True
    if changed:
        _write_raw_config(config)
    return config


def get_config() -> dict:
    with _file_lock:
        config = _read_raw_config()
        return _ensure_ids(config)


def add_target(query: str, business_type_hint: str = "") -> dict:
    query = (query or "").strip()
    if not query:
        raise SearchTargetsConfigError("Le champ 'query' est obligatoire.")

    with _file_lock:
        config = _ensure_ids(_read_raw_config())
        new_target = {
            "id": uuid.uuid4().hex[:12],
            "query": query,
            "business_type_hint": (business_type_hint or "").strip(),
        }
        config.setdefault("targets", []).append(new_target)
        _write_raw_config(config)
        return new_target


def update_target(target_id: str, query: str, business_type_hint: str = "") -> dict:
    query = (query or "").strip()
    if not query:
        raise SearchTargetsConfigError("Le champ 'query' est obligatoire.")

    with _file_lock:
        config = _ensure_ids(_read_raw_config())
        targets = config.get("targets", [])

        for target in targets:
            if target["id"] == target_id:
                target["query"] = query
                target["business_type_hint"] = (business_type_hint or "").strip()
                _write_raw_config(config)
                return target

        raise SearchTargetsConfigError(f"Aucune cible trouvée avec l'id '{target_id}'.")


def delete_target(target_id: str) -> None:
    with _file_lock:
        config = _ensure_ids(_read_raw_config())
        targets = config.get("targets", [])
        remaining = [t for t in targets if t["id"] != target_id]

        if len(remaining) == len(targets):
            raise SearchTargetsConfigError(f"Aucune cible trouvée avec l'id '{target_id}'.")

        config["targets"] = remaining
        _write_raw_config(config)


def update_max_results(value: int) -> dict:
    if not isinstance(value, int) or value < 1 or value > 30:
        raise SearchTargetsConfigError("max_results_per_target doit être un entier entre 1 et 30.")

    with _file_lock:
        config = _ensure_ids(_read_raw_config())
        config["max_results_per_target"] = value
        _write_raw_config(config)
        return config