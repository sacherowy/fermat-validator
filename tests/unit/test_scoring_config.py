"""Tests for app/ai/scoring_config.py — YAML-driven scoring configuration."""

import pytest
import app.ai.scoring_config as sc_module
from app.ai.scoring_config import get_max_points, _validate_config


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the lru_cache before and after every test."""
    sc_module._load_scoring_config.cache_clear()
    yield
    sc_module._load_scoring_config.cache_clear()


VALID_CONFIG = {
    "etap1": {
        "task_groups": [
            {"tasks": [1, 2, 3, 4, 5], "max_points": 2},
            {"tasks": [6, 7, 8, 9, 10], "max_points": 4},
        ]
    },
    "etap2": {
        "task_groups": [
            {"tasks": [1, 2, 3, 4, 5], "max_points": 2},
            {"tasks": [6, 7, 8, 9, 10], "max_points": 4},
        ]
    },
}


class TestValidateConfig:
    def test_valid_config_passes(self):
        _validate_config(VALID_CONFIG, path="test")  # should not raise

    def test_missing_etap1_raises(self):
        cfg = {"etap2": VALID_CONFIG["etap2"]}
        with pytest.raises(ValueError, match="etap1"):
            _validate_config(cfg, path="test")

    def test_missing_etap2_raises(self):
        cfg = {"etap1": VALID_CONFIG["etap1"]}
        with pytest.raises(ValueError, match="etap2"):
            _validate_config(cfg, path="test")

    def test_empty_task_groups_raises(self):
        cfg = {
            "etap1": {"task_groups": []},
            "etap2": VALID_CONFIG["etap2"],
        }
        with pytest.raises(ValueError, match="task_groups"):
            _validate_config(cfg, path="test")

    def test_task_groups_not_a_list_raises(self):
        cfg = {
            "etap1": {"task_groups": "not-a-list"},
            "etap2": VALID_CONFIG["etap2"],
        }
        with pytest.raises(ValueError, match="task_groups"):
            _validate_config(cfg, path="test")

    def test_zero_max_points_raises(self):
        cfg = {
            "etap1": {"task_groups": [{"tasks": [1], "max_points": 0}]},
            "etap2": VALID_CONFIG["etap2"],
        }
        with pytest.raises(ValueError, match="max_points"):
            _validate_config(cfg, path="test")

    def test_string_max_points_raises(self):
        cfg = {
            "etap1": {"task_groups": [{"tasks": [1], "max_points": "four"}]},
            "etap2": VALID_CONFIG["etap2"],
        }
        with pytest.raises(ValueError, match="max_points"):
            _validate_config(cfg, path="test")

    def test_duplicate_task_number_raises(self):
        cfg = {
            "etap1": {
                "task_groups": [
                    {"tasks": [1, 2, 3], "max_points": 2},
                    {"tasks": [3, 4, 5], "max_points": 4},  # task 3 duplicated
                ]
            },
            "etap2": VALID_CONFIG["etap2"],
        }
        with pytest.raises(ValueError, match="more than once"):
            _validate_config(cfg, path="test")

    def test_non_integer_task_number_raises(self):
        cfg = {
            "etap1": {"task_groups": [{"tasks": ["one", 2], "max_points": 2}]},
            "etap2": VALID_CONFIG["etap2"],
        }
        with pytest.raises(ValueError, match="integer"):
            _validate_config(cfg, path="test")

    def test_empty_tasks_list_raises(self):
        cfg = {
            "etap1": {"task_groups": [{"tasks": [], "max_points": 2}]},
            "etap2": VALID_CONFIG["etap2"],
        }
        with pytest.raises(ValueError, match="tasks"):
            _validate_config(cfg, path="test")


class TestGetMaxPoints:
    """Tests against the real config/scoring.yml checked into the repo."""

    def test_etap1_task_in_first_group(self):
        assert get_max_points("etap1", 1) == 2

    def test_etap1_task_in_second_group(self):
        assert get_max_points("etap1", 6) == 4

    def test_etap2_task_in_first_group(self):
        assert get_max_points("etap2", 3) == 2

    def test_etap2_task_in_second_group(self):
        assert get_max_points("etap2", 8) == 4

    def test_unknown_etap_raises(self):
        with pytest.raises(ValueError, match="etap3"):
            get_max_points("etap3", 1)

    def test_unknown_task_number_raises(self):
        with pytest.raises(ValueError, match="11"):
            get_max_points("etap1", 11)

    def test_file_not_found_raises(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sc_module, "_CONFIG_PATH", tmp_path / "nonexistent.yml")
        with pytest.raises(FileNotFoundError):
            get_max_points("etap1", 1)

    def test_invalid_yaml_raises(self, monkeypatch, tmp_path):
        bad_yaml = tmp_path / "scoring.yml"
        bad_yaml.write_text(": invalid: yaml: [}")
        monkeypatch.setattr(sc_module, "_CONFIG_PATH", bad_yaml)
        with pytest.raises(ValueError, match="invalid YAML"):
            get_max_points("etap1", 1)
