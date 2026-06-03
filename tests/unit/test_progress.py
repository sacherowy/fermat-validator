"""Tests for app/progress.py — task graph, prerequisite resolution, and recommendations."""

from unittest.mock import patch

import pytest

from app.models import GraphNode, TaskPdf, TaskInfo, TaskStatus
from app.progress import (
    compute_prerequisites_met,
    get_mastery_threshold,
    get_recommended_tasks,
    get_task_status_batch,
)


def make_task(
    year: str,
    etap: str,
    number: int,
    prerequisites: list[str] | None = None,
    categories: list[str] | None = None,
    difficulty: int = 3,
) -> TaskInfo:
    return TaskInfo(
        year=year,
        etap=etap,
        number=number,
        title=f"Task {year}/{etap}/{number}",
        content="Task content",
        pdf=TaskPdf(tasks="tasks.pdf"),
        prerequisites=prerequisites or [],
        categories=categories or ["algebra"],
        difficulty=difficulty,
    )


def make_node(
    key: str,
    status: TaskStatus,
    best_score: int = 0,
    categories: list[str] | None = None,
    difficulty: int = 3,
) -> GraphNode:
    parts = key.split("_")
    return GraphNode(
        key=key,
        year=parts[0],
        etap=parts[1],
        number=int(parts[2]),
        title=f"Task {key}",
        status=status,
        best_score=best_score,
        categories=categories or ["algebra"],
        difficulty=difficulty,
    )


class TestGetMasteryThreshold:
    def test_etap1_returns_2(self):
        assert get_mastery_threshold("etap1") == 2

    def test_etap2_returns_5(self):
        assert get_mastery_threshold("etap2") == 5

    def test_etap3_returns_5(self):
        assert get_mastery_threshold("etap3") == 5

    def test_unknown_etap_falls_back_to_2(self):
        # Current logic: return 5 if etap in ("etap2", "etap3") else 2
        assert get_mastery_threshold("etap4") == 2


class TestComputePrerequisitesMet:
    def test_task_with_no_prerequisites_is_always_met(self):
        tasks = {"2024_etap1_1": make_task("2024", "etap1", 1)}
        progress: dict[str, int] = {}
        result = compute_prerequisites_met(tasks, progress)
        assert result["2024_etap1_1"] is True

    def test_task_with_mastered_prerequisite_is_met(self):
        tasks = {
            "2024_etap1_1": make_task("2024", "etap1", 1),
            "2024_etap1_2": make_task("2024", "etap1", 2, prerequisites=["2024_etap1_1"]),
        }
        progress = {"2024_etap1_1": 2}  # Mastered (etap1 threshold = 2)
        result = compute_prerequisites_met(tasks, progress)
        assert result["2024_etap1_2"] is True

    def test_task_with_unmastered_prerequisite_is_not_met(self):
        tasks = {
            "2024_etap1_1": make_task("2024", "etap1", 1),
            "2024_etap1_2": make_task("2024", "etap1", 2, prerequisites=["2024_etap1_1"]),
        }
        progress = {"2024_etap1_1": 1}  # Score 1 < mastery threshold 2
        result = compute_prerequisites_met(tasks, progress)
        assert result["2024_etap1_2"] is False

    def test_transitive_chain_all_mastered(self):
        # C requires B requires A; all mastered
        tasks = {
            "2024_etap1_1": make_task("2024", "etap1", 1),
            "2024_etap1_2": make_task("2024", "etap1", 2, prerequisites=["2024_etap1_1"]),
            "2024_etap1_3": make_task("2024", "etap1", 3, prerequisites=["2024_etap1_2"]),
        }
        progress = {"2024_etap1_1": 2, "2024_etap1_2": 2}
        result = compute_prerequisites_met(tasks, progress)
        assert result["2024_etap1_3"] is True

    def test_transitive_chain_intermediate_not_mastered(self):
        # C requires B requires A; B not mastered
        tasks = {
            "2024_etap1_1": make_task("2024", "etap1", 1),
            "2024_etap1_2": make_task("2024", "etap1", 2, prerequisites=["2024_etap1_1"]),
            "2024_etap1_3": make_task("2024", "etap1", 3, prerequisites=["2024_etap1_2"]),
        }
        progress = {"2024_etap1_1": 2}  # A mastered, B not
        result = compute_prerequisites_met(tasks, progress)
        assert result["2024_etap1_3"] is False

    def test_cycle_detection_does_not_infinite_loop(self):
        # A requires B, B requires A — should break cycle cleanly
        tasks = {
            "2024_etap1_1": make_task("2024", "etap1", 1, prerequisites=["2024_etap1_2"]),
            "2024_etap1_2": make_task("2024", "etap1", 2, prerequisites=["2024_etap1_1"]),
        }
        progress: dict[str, int] = {}
        # Should not raise RecursionError or loop forever
        result = compute_prerequisites_met(tasks, progress)
        assert isinstance(result, dict)

    def test_invalid_prerequisite_key_format_is_skipped(self):
        # Key with no etap part — should log a warning and skip
        tasks = {
            "2024_etap1_1": make_task("2024", "etap1", 1, prerequisites=["badkey"]),
        }
        progress: dict[str, int] = {}
        result = compute_prerequisites_met(tasks, progress)
        # Skipped invalid prereq → treated as met
        assert result["2024_etap1_1"] is True

    def test_prerequisite_pointing_to_nonexistent_task_blocks_unlock(self):
        # If a valid-format prerequisite task is not in all_tasks,
        # mastered.get(prereq_key, False) returns False → task is blocked.
        # This is the current behaviour: unknown prereq = unmastered.
        tasks = {
            "2024_etap1_2": make_task("2024", "etap1", 2, prerequisites=["2024_etap1_1"]),
        }
        progress: dict[str, int] = {}
        result = compute_prerequisites_met(tasks, progress)
        assert result["2024_etap1_2"] is False


class TestGetTaskStatusBatch:
    def test_mastered_task(self):
        tasks = {"2024_etap1_1": make_task("2024", "etap1", 1)}
        progress = {"2024_etap1_1": 2}  # At mastery threshold
        statuses = get_task_status_batch(tasks, progress)
        assert statuses["2024_etap1_1"] == TaskStatus.MASTERED

    def test_unlocked_task_no_prerequisites(self):
        tasks = {"2024_etap1_1": make_task("2024", "etap1", 1)}
        progress: dict[str, int] = {}
        statuses = get_task_status_batch(tasks, progress)
        assert statuses["2024_etap1_1"] == TaskStatus.UNLOCKED

    def test_locked_task_prerequisite_not_mastered(self):
        tasks = {
            "2024_etap1_1": make_task("2024", "etap1", 1),
            "2024_etap1_2": make_task("2024", "etap1", 2, prerequisites=["2024_etap1_1"]),
        }
        progress: dict[str, int] = {}
        statuses = get_task_status_batch(tasks, progress)
        assert statuses["2024_etap1_2"] == TaskStatus.LOCKED

    def test_unlocked_task_after_prerequisite_mastered(self):
        tasks = {
            "2024_etap1_1": make_task("2024", "etap1", 1),
            "2024_etap1_2": make_task("2024", "etap1", 2, prerequisites=["2024_etap1_1"]),
        }
        progress = {"2024_etap1_1": 2}
        statuses = get_task_status_batch(tasks, progress)
        assert statuses["2024_etap1_2"] == TaskStatus.UNLOCKED

    def test_etap2_mastery_threshold_is_5(self):
        tasks = {"2024_etap2_1": make_task("2024", "etap2", 1)}
        statuses = get_task_status_batch(tasks, {"2024_etap2_1": 4})
        assert statuses["2024_etap2_1"] == TaskStatus.UNLOCKED  # 4 < 5

        statuses = get_task_status_batch(tasks, {"2024_etap2_1": 5})
        assert statuses["2024_etap2_1"] == TaskStatus.MASTERED


class TestGetRecommendedTasks:
    def test_empty_when_no_unlocked_tasks(self):
        nodes = [make_node("2024_etap1_1", TaskStatus.LOCKED)]
        assert get_recommended_tasks(nodes) == []

    def test_only_unlocked_tasks_recommended(self):
        nodes = [
            make_node("2024_etap1_1", TaskStatus.LOCKED),
            make_node("2024_etap1_2", TaskStatus.UNLOCKED),
            make_node("2024_etap1_3", TaskStatus.MASTERED),
        ]
        result = get_recommended_tasks(nodes)
        assert all(n.status == TaskStatus.UNLOCKED for n in result)
        assert len(result) == 1

    def test_limit_respected(self):
        nodes = [make_node(f"2024_etap1_{i}", TaskStatus.UNLOCKED) for i in range(1, 10)]
        result = get_recommended_tasks(nodes, limit=5)
        assert len(result) <= 5

    def test_unattempted_tasks_ranked_before_attempted(self):
        nodes = [
            make_node("2024_etap1_1", TaskStatus.UNLOCKED, best_score=2),  # attempted
            make_node("2024_etap1_2", TaskStatus.UNLOCKED, best_score=0),  # not attempted
        ]
        result = get_recommended_tasks(nodes, limit=5)
        # Unattempted (best_score=0) should come first
        assert result[0].key == "2024_etap1_2"

    def test_category_filter_applied(self):
        nodes = [
            make_node("2024_etap1_1", TaskStatus.UNLOCKED, categories=["algebra"]),
            make_node("2024_etap1_2", TaskStatus.UNLOCKED, categories=["geometria"]),
        ]
        result = get_recommended_tasks(nodes, category_filter="geometria")
        assert all("geometria" in n.categories for n in result)

    def test_category_filter_no_matches_returns_empty(self):
        nodes = [make_node("2024_etap1_1", TaskStatus.UNLOCKED, categories=["algebra"])]
        result = get_recommended_tasks(nodes, category_filter="geometria")
        assert result == []

    def test_category_diversity_prefers_different_categories(self):
        nodes = [
            make_node("2024_etap1_1", TaskStatus.UNLOCKED, categories=["algebra"]),
            make_node("2024_etap1_2", TaskStatus.UNLOCKED, categories=["algebra"]),
            make_node("2024_etap1_3", TaskStatus.UNLOCKED, categories=["geometria"]),
        ]
        result = get_recommended_tasks(nodes, limit=5)
        categories_in_result = [n.categories[0] for n in result]
        # Should include both algebra and geometria in first pass
        assert "algebra" in categories_in_result
        assert "geometria" in categories_in_result
