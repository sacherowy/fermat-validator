"""Tests for app/db/repositories.py — ensure_utc and stale submission detection."""

from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.repositories import ensure_utc, SubmissionRepository, SUBMISSION_TIMEOUT_SECONDS
from app.db.session import Base
from app.db.models import SubmissionDB, SubmissionStatus, IssueType, UserDB


@pytest.fixture
def db_session():
    """Provide an in-memory SQLite session for repository tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create a test user (required for FK constraint)
    user = UserDB(google_sub="user1", email="user1@test.com", name="Test User")
    session.add(user)
    session.commit()

    yield session
    session.close()


def make_submission(
    id: str,
    user_id: str = "user1",
    year: str = "2024",
    etap: str = "etap1",
    task_number: int = 1,
    status: SubmissionStatus = SubmissionStatus.COMPLETED,
    timestamp: datetime | None = None,
    score: int | None = 3,
) -> SubmissionDB:
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    return SubmissionDB(
        id=id,
        user_id=user_id,
        year=year,
        etap=etap,
        task_number=task_number,
        status=status,
        timestamp=timestamp,
        images=[],
        score=score,
        issue_type=IssueType.NONE,
        abuse_score=0,
    )


class TestEnsureUtc:
    def test_none_returns_none(self):
        assert ensure_utc(None) is None

    def test_naive_datetime_gets_utc_timezone(self):
        naive = datetime(2024, 1, 15, 12, 0, 0)
        result = ensure_utc(naive)
        assert result.tzinfo == timezone.utc
        assert result.year == 2024
        assert result.hour == 12

    def test_utc_aware_datetime_returned_unchanged(self):
        aware = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = ensure_utc(aware)
        assert result is aware

    def test_non_utc_aware_datetime_returned_unchanged(self):
        tz_plus5 = timezone(timedelta(hours=5))
        aware = datetime(2024, 1, 15, 12, 0, 0, tzinfo=tz_plus5)
        result = ensure_utc(aware)
        assert result is aware


class TestMarkStaleSubmissionsFailed:
    def test_pending_submission_past_timeout_marked_failed(self, db_session):
        stale_time = datetime.now(timezone.utc) - timedelta(seconds=SUBMISSION_TIMEOUT_SECONDS + 30)
        sub = make_submission("stale1", status=SubmissionStatus.PENDING, timestamp=stale_time, score=None)
        db_session.add(sub)
        db_session.commit()

        repo = SubmissionRepository(db_session)
        repo._mark_stale_submissions_failed([sub])

        assert sub.status == SubmissionStatus.FAILED
        assert sub.error_message is not None

    def test_processing_submission_past_timeout_marked_failed(self, db_session):
        stale_time = datetime.now(timezone.utc) - timedelta(seconds=SUBMISSION_TIMEOUT_SECONDS + 30)
        sub = make_submission("stale2", status=SubmissionStatus.PROCESSING, timestamp=stale_time, score=None)
        db_session.add(sub)
        db_session.commit()

        repo = SubmissionRepository(db_session)
        repo._mark_stale_submissions_failed([sub])

        assert sub.status == SubmissionStatus.FAILED

    def test_recent_pending_submission_not_marked_failed(self, db_session):
        recent_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        sub = make_submission("fresh1", status=SubmissionStatus.PENDING, timestamp=recent_time, score=None)
        db_session.add(sub)
        db_session.commit()

        repo = SubmissionRepository(db_session)
        repo._mark_stale_submissions_failed([sub])

        assert sub.status == SubmissionStatus.PENDING

    def test_completed_submission_not_affected(self, db_session):
        old_time = datetime.now(timezone.utc) - timedelta(hours=24)
        sub = make_submission("done1", status=SubmissionStatus.COMPLETED, timestamp=old_time)
        db_session.add(sub)
        db_session.commit()

        repo = SubmissionRepository(db_session)
        repo._mark_stale_submissions_failed([sub])

        assert sub.status == SubmissionStatus.COMPLETED

    def test_naive_timestamp_treated_as_utc(self, db_session):
        # Naive datetime (no tzinfo) that is past the timeout
        naive_stale = datetime.utcnow() - timedelta(seconds=SUBMISSION_TIMEOUT_SECONDS + 60)
        sub = make_submission("naive1", status=SubmissionStatus.PENDING, timestamp=naive_stale, score=None)
        db_session.add(sub)
        db_session.commit()

        repo = SubmissionRepository(db_session)
        repo._mark_stale_submissions_failed([sub])

        assert sub.status == SubmissionStatus.FAILED


class TestCountUserRecentSubmissions:
    def test_counts_only_submissions_within_24h(self, db_session):
        now = datetime.now(timezone.utc)
        recent = make_submission("r1", timestamp=now - timedelta(hours=12))
        old = make_submission("o1", timestamp=now - timedelta(hours=25))
        db_session.add_all([recent, old])
        db_session.commit()

        repo = SubmissionRepository(db_session)
        count = repo.count_user_recent_submissions("user1", hours=24)
        assert count == 1

    def test_returns_zero_when_no_submissions(self, db_session):
        repo = SubmissionRepository(db_session)
        count = repo.count_user_recent_submissions("user1", hours=24)
        assert count == 0


class TestGetUserProgress:
    def test_returns_best_score_per_task(self, db_session):
        now = datetime.now(timezone.utc)
        s1 = make_submission("p1", status=SubmissionStatus.COMPLETED, score=2)
        s2 = make_submission("p2", status=SubmissionStatus.COMPLETED, score=5)
        db_session.add_all([s1, s2])
        db_session.commit()

        repo = SubmissionRepository(db_session)
        progress = repo.get_user_progress("user1")

        assert progress["2024_etap1_1"] == 5  # Max of 2 and 5

    def test_excludes_failed_submissions(self, db_session):
        s1 = make_submission("f1", status=SubmissionStatus.COMPLETED, score=3)
        s2 = make_submission("f2", status=SubmissionStatus.FAILED, score=None)
        db_session.add_all([s1, s2])
        db_session.commit()

        repo = SubmissionRepository(db_session)
        progress = repo.get_user_progress("user1")

        assert progress["2024_etap1_1"] == 3  # Only completed count

    def test_returns_empty_for_user_with_no_submissions(self, db_session):
        repo = SubmissionRepository(db_session)
        assert repo.get_user_progress("user1") == {}
