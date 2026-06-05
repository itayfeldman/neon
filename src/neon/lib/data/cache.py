import hashlib
import json
import pickle
import time
from pathlib import Path

import pandas as pd

_CACHE_ROOT = Path.home() / ".neon" / "cache"


def _cache_path(provider: str, params: dict) -> Path:
    key = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:16]
    return _CACHE_ROOT / provider / f"{key}.pkl"


def load(provider: str, params: dict, ttl_seconds: int) -> pd.DataFrame | None:
    path = _cache_path(provider, params)
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > ttl_seconds:
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def save(provider: str, params: dict, df: pd.DataFrame) -> None:
    path = _cache_path(provider, params)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(df, f)
