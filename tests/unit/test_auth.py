"""Tests for app/auth.py and app/groups.py — authentication and access control."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.auth import (
    SESSION_USER_KEY,
    get_current_user,
    get_current_user_id,
    is_group_member,
    verify_auth,
)
from app.groups import _get_allowed_emails, check_group_membership


def make_request(session_data: dict | None = None) -> MagicMock:
    request = MagicMock()
    request.session = session_data or {}
    return request


SAMPLE_USER = {
    "google_sub": "sub123",
    "email": "user@example.com",
    "name": "Test User",
    "picture": None,
    "is_group_member": True,
    "membership_checked_at": 9999999999,  # Far future — won't trigger re-check
}


class TestGetCurrentUser:
    def test_returns_user_from_session(self):
        request = make_request({SESSION_USER_KEY: SAMPLE_USER})
        with patch("app.auth.settings") as mock_settings:
            mock_settings.auth_disabled = False
            user = get_current_user(request)
        assert user == SAMPLE_USER

    def test_returns_none_when_session_empty(self):
        request = make_request({})
        with patch("app.auth.settings") as mock_settings:
            mock_settings.auth_disabled = False
            result = get_current_user(request)
        assert result is None

    def test_auth_disabled_returns_anonymous_user(self):
        request = make_request({})
        with patch("app.auth.settings") as mock_settings:
            mock_settings.auth_disabled = True
            user = get_current_user(request)
        assert user is not None
        assert user["google_sub"] == "anonymous"
        assert user["is_group_member"] is True


class TestGetCurrentUserId:
    def test_returns_google_sub_when_authenticated(self):
        request = make_request({SESSION_USER_KEY: SAMPLE_USER})
        with patch("app.auth.settings") as mock_settings:
            mock_settings.auth_disabled = False
            assert get_current_user_id(request) == "sub123"

    def test_returns_none_when_unauthenticated(self):
        request = make_request({})
        with patch("app.auth.settings") as mock_settings:
            mock_settings.auth_disabled = False
            assert get_current_user_id(request) is None


class TestVerifyAuth:
    def test_returns_true_when_session_has_user(self):
        request = make_request({SESSION_USER_KEY: SAMPLE_USER})
        with patch("app.auth.settings") as mock_settings:
            mock_settings.auth_disabled = False
            assert verify_auth(request) is True

    def test_returns_false_when_session_empty(self):
        request = make_request({})
        with patch("app.auth.settings") as mock_settings:
            mock_settings.auth_disabled = False
            assert verify_auth(request) is False

    def test_returns_true_when_auth_disabled(self):
        request = make_request({})
        with patch("app.auth.settings") as mock_settings:
            mock_settings.auth_disabled = True
            assert verify_auth(request) is True


class TestIsGroupMember:
    def test_returns_true_when_user_is_group_member(self):
        user = {**SAMPLE_USER, "is_group_member": True}
        request = make_request({SESSION_USER_KEY: user})
        with patch("app.auth.settings") as mock_settings:
            mock_settings.auth_disabled = False
            assert is_group_member(request) is True

    def test_returns_false_when_user_is_not_group_member(self):
        user = {**SAMPLE_USER, "is_group_member": False}
        request = make_request({SESSION_USER_KEY: user})
        with patch("app.auth.settings") as mock_settings:
            mock_settings.auth_disabled = False
            assert is_group_member(request) is False

    def test_returns_false_when_unauthenticated(self):
        request = make_request({})
        with patch("app.auth.settings") as mock_settings:
            mock_settings.auth_disabled = False
            assert is_group_member(request) is False


class TestGetAllowedEmails:
    def test_parses_comma_separated_emails(self):
        with patch("app.groups.settings") as mock_settings:
            mock_settings.allowed_emails = "alice@example.com, BOB@example.com"
            result = _get_allowed_emails()
        assert "alice@example.com" in result
        assert "bob@example.com" in result  # lowercased

    def test_returns_empty_set_when_not_configured(self):
        with patch("app.groups.settings") as mock_settings:
            mock_settings.allowed_emails = None
            assert _get_allowed_emails() == set()

    def test_filters_whitespace_only_entries(self):
        with patch("app.groups.settings") as mock_settings:
            mock_settings.allowed_emails = "a@b.com, , ,c@d.com"
            result = _get_allowed_emails()
        assert result == {"a@b.com", "c@d.com"}


class TestCheckGroupMembership:
    @pytest.mark.asyncio
    async def test_public_access_grants_all_users(self):
        with patch("app.groups.settings") as mock_settings:
            mock_settings.public_access = True
            mock_settings.allowed_emails = None
            mock_settings.google_service_account_json = None
            result = await check_group_membership("anyuser@example.com")
        assert result is True

    @pytest.mark.asyncio
    async def test_allowlist_grants_listed_email(self):
        with patch("app.groups.settings") as mock_settings:
            mock_settings.public_access = False
            mock_settings.allowed_emails = "allowed@example.com"
            mock_settings.google_service_account_json = None
            result = await check_group_membership("allowed@example.com")
        assert result is True

    @pytest.mark.asyncio
    async def test_allowlist_denies_unlisted_email(self):
        with patch("app.groups.settings") as mock_settings:
            mock_settings.public_access = False
            mock_settings.allowed_emails = "allowed@example.com"
            mock_settings.google_service_account_json = None
            result = await check_group_membership("other@example.com")
        assert result is False

    @pytest.mark.asyncio
    async def test_allowlist_is_case_insensitive(self):
        with patch("app.groups.settings") as mock_settings:
            mock_settings.public_access = False
            mock_settings.allowed_emails = "User@Example.COM"
            mock_settings.google_service_account_json = None
            result = await check_group_membership("user@example.com")
        assert result is True

    @pytest.mark.asyncio
    async def test_no_access_control_denies_by_default(self):
        with patch("app.groups.settings") as mock_settings:
            mock_settings.public_access = False
            mock_settings.allowed_emails = None
            mock_settings.google_service_account_json = None
            result = await check_group_membership("someone@example.com")
        assert result is False

    @pytest.mark.asyncio
    async def test_allowlist_does_not_fall_through_to_groups_api(self):
        """When allowlist is configured but email not in it, the Google Groups API must NOT be called."""
        with patch("app.groups.settings") as mock_settings, \
             patch("app.groups._check_membership_cached") as mock_api:
            mock_settings.public_access = False
            mock_settings.allowed_emails = "other@example.com"
            mock_settings.google_service_account_json = "some-json"
            result = await check_group_membership("unlisted@example.com")
        assert result is False
        mock_api.assert_not_called()
