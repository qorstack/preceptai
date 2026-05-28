__version__ = "0.2.0"


def _load_config() -> None:
    """Load Postgres connection info from a precept.config file or .env.

    Search order (highest priority wins; lower-priority sources never
    overwrite an already-set value):

        1. Process env vars already set (CI / Docker / shell exports win)
        2. ./precept.config — walks up from cwd to find a project-local file
        3. ~/.precept.config — user-global fallback
        4. ./.env — last resort, also used by docker-compose

    Failures are silent so importing precept never breaks.
    """
    import os
    import tomllib
    from pathlib import Path

    _DB_MAPPING = {
        "host":     "POSTGRES_HOST",
        "port":     "POSTGRES_PORT",
        "user":     "POSTGRES_USER",
        "password": "POSTGRES_PASSWORD",
        "db":       "POSTGRES_DB",
        "schema":   "POSTGRES_SCHEMA",
    }
    _FILENAME = "precept.config"

    def _apply_toml(path: Path) -> None:
        try:
            with open(path, "rb") as fh:
                data = tomllib.load(fh)
            for key, env_name in _DB_MAPPING.items():
                val = data.get("database", {}).get(key)
                if val is not None and env_name not in os.environ:
                    os.environ[env_name] = str(val)
        except Exception:
            pass

    # 1. Walk up from cwd looking for project-local precept.config
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        cfg = parent / _FILENAME
        if cfg.is_file():
            _apply_toml(cfg)
            break

    # 2. User-global fallback at ~/.precept.config
    global_cfg = Path.home() / f".{_FILENAME}"
    if global_cfg.is_file():
        _apply_toml(global_cfg)

    # 3. .env fallback (docker-compose compatibility)
    try:
        from dotenv import load_dotenv

        load_dotenv(override=False)
    except ImportError:
        pass


_load_config()
