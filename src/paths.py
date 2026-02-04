import os
import sys
from pathlib import Path
from typing import Tuple


APP_NAME = "package-shop"


def _is_windows() -> bool:
    return os.name == "nt"


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False)) or hasattr(sys, "_MEIPASS")


def _default_dirs() -> Tuple[Path, Path, Path, Path]:
    """Return (data, config, log, run) default directories by platform.

    Linux (production): /var/lib, /etc, /var/log, /run
    Windows (dev): %PROGRAMDATA%\\PackageShop for data/config/log, %TEMP% for run
    Others: home-local fallback under ~/.local/state|share
    """
    if _is_windows():
        program_data = Path(os.environ.get("PROGRAMDATA", r"C:\\ProgramData"))
        base = program_data / "PackageShop"
        data = base
        config = base
        log = base / "log"
        run = Path(os.environ.get("TEMP", str(base)))
        return (data, config, log, run)

    # POSIX
    data = Path("/var/lib") / APP_NAME
    config = Path("/etc") / APP_NAME
    log = Path("/var/log") / APP_NAME
    run = Path("/run") / APP_NAME
    return (data, config, log, run)


def get_data_dir() -> Path:
    env = os.environ.get("PACKAGE_SHOP_DATA_DIR")
    return Path(env) if env else _default_dirs()[0]


def get_config_dir() -> Path:
    env = os.environ.get("PACKAGE_SHOP_CONFIG_DIR")
    return Path(env) if env else _default_dirs()[1]


def get_log_dir() -> Path:
    env = os.environ.get("PACKAGE_SHOP_LOG_DIR")
    return Path(env) if env else _default_dirs()[2]


def get_run_dir() -> Path:
    env = os.environ.get("PACKAGE_SHOP_RUN_DIR")
    return Path(env) if env else _default_dirs()[3]


def resolve_data(name: str) -> Path:
    return get_data_dir() / name


def ensure_dirs() -> None:
    for d in (get_data_dir(), get_config_dir(), get_log_dir(), get_run_dir()):
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass


def init_dirs_and_migrate() -> None:
    # Fresh-install semantics: only ensure directories exist.
    ensure_dirs()
