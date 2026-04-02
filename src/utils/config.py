"""Configuration loader for the NGO Financial Scorecard project."""

import os
from pathlib import Path
from typing import Any, Dict

import yaml


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load YAML configuration file.

    Args:
        config_path: Path to config file. Defaults to configs/config.yaml.

    Returns:
        Dictionary containing configuration parameters.
    """
    if config_path is None:
        config_path = get_project_root() / "configs" / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


def ensure_directories(config: Dict[str, Any]) -> None:
    """Create necessary directories specified in config."""
    root = get_project_root()

    dirs_to_create = [
        root / config["data"]["raw_dir"],
        root / config["data"]["processed_dir"],
        root / config["visualization"]["output_dir"],
        root / config["logging"]["log_dir"],
    ]

    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)
