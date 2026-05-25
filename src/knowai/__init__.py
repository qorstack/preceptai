__version__ = "0.2.0"


def _load_config() -> None:
    """Load Postgres connection info from `knowai.toml` (preferred) or `.env`.

    Search order (highest priority wins):
        1. Process env vars already set
        2. knowai.toml in cwd or any parent directory
        3. .env in cwd or any parent directory (also used by docker-compose)

    Existing env vars are never overwritten — useful for CI / Docker overrides.
    Failures are silent so importing knowai never breaks.
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

    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        cfg = parent / "knowai.toml"
        if cfg.is_file():
            try:
                with open(cfg, "rb") as fh:
                    data = tomllib.load(fh)
                for key, env_name in _DB_MAPPING.items():
                    val = data.get("database", {}).get(key)
                    if val is not None and env_name not in os.environ:
                        os.environ[env_name] = str(val)
            except Exception:
                pass
            break

    try:
        from dotenv import load_dotenv

        load_dotenv(override=False)
    except ImportError:
        pass


_load_config()
