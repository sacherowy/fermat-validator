"""YAML-driven scoring configuration for FerMat Validator.

Loads config/scoring.yml at startup and provides get_max_points()
for the submission pipeline. Validates configuration on load.
"""

import logging
from functools import lru_cache
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Path to scoring config relative to repository root
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "scoring.yml"

REQUIRED_ETAPS = {"etap1", "etap2"}


def _validate_config(config: dict, path: Path) -> None:
    """Validate scoring config structure. Raises ValueError with a clear message on failure."""
    for etap in REQUIRED_ETAPS:
        if etap not in config:
            raise ValueError(
                f"Scoring config at {path} is missing required key '{etap}'. "
                f"Both etap1 and etap2 must be present."
            )
        etap_cfg = config[etap]
        groups = etap_cfg.get("task_groups")
        if not groups or not isinstance(groups, list):
            raise ValueError(
                f"Scoring config {path}: '{etap}.task_groups' must be a non-empty list."
            )

        seen_tasks: set[int] = set()
        for i, group in enumerate(groups):
            tasks = group.get("tasks")
            max_pts = group.get("max_points")

            if not tasks or not isinstance(tasks, list):
                raise ValueError(
                    f"Scoring config {path}: '{etap}.task_groups[{i}].tasks' "
                    f"must be a non-empty list of integers."
                )
            if not isinstance(max_pts, int) or max_pts <= 0:
                raise ValueError(
                    f"Scoring config {path}: '{etap}.task_groups[{i}].max_points' "
                    f"must be a positive integer."
                )
            for t in tasks:
                if not isinstance(t, int):
                    raise ValueError(
                        f"Scoring config {path}: task number {t!r} in "
                        f"'{etap}.task_groups[{i}].tasks' must be an integer."
                    )
                if t in seen_tasks:
                    raise ValueError(
                        f"Scoring config {path}: task number {t} appears more than "
                        f"once in '{etap}'."
                    )
                seen_tasks.add(t)


@lru_cache(maxsize=1)
def _load_scoring_config() -> dict:
    """Load and validate scoring.yml. Cached after first call."""
    path = _CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Scoring config not found at {path}. "
            f"Create config/scoring.yml in the repository root."
        )
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Scoring config at {path} contains invalid YAML: {e}") from e

    if not isinstance(config, dict):
        raise ValueError(f"Scoring config at {path} must be a YAML mapping at the top level.")

    _validate_config(config, path)
    logger.info(f"[ScoringConfig] Loaded and validated from {path}")
    return config


def get_max_points(etap: str, task_number: int) -> int:
    """Return the maximum score for a given etap and task number.

    Args:
        etap: Competition stage ("etap1" or "etap2").
        task_number: Task number (1-based integer).

    Returns:
        Maximum integer points for this task.

    Raises:
        ValueError: If etap or task_number are not found in config.
    """
    config = _load_scoring_config()

    etap_cfg = config.get(etap)
    if etap_cfg is None:
        raise ValueError(
            f"Etap '{etap}' not found in scoring config. "
            f"Valid etaps: {sorted(config.keys())}."
        )

    for group in etap_cfg.get("task_groups", []):
        if task_number in group["tasks"]:
            return group["max_points"]

    raise ValueError(
        f"Task number {task_number} not found in scoring config for '{etap}'. "
        f"Brak konfiguracji punktacji dla tego zadania."
    )


def validate_scoring_config() -> list[str]:
    """Validate scoring config at startup. Returns list of error messages (empty if OK)."""
    try:
        _load_scoring_config()
        return []
    except Exception as e:
        return [str(e)]
