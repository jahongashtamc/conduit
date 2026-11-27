"""Brauzer navigatsiyasi chegarasida noto'g'ri URL rad etilishi testi."""

import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app  # noqa: E402

client = TestClient(app)


def test_invalid_url_is_rejected_before_playwright():
    with patch("live_browser.navigate", new_callable=AsyncMock) as navigate:
        res = client.post("/api/browser/navigate", json={"url": "-hel"})
    assert res.status_code == 422
    detail = res.json()["detail"].lower()
    assert "noto'g'ri" in detail or "http" in detail
    navigate.assert_not_awaited()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("example.com", "https://example.com"),
        ("localhost:3000", "http://localhost:3000"),
    ],
)
def test_valid_url_is_normalized_and_navigated(raw, expected):
    with patch("live_browser.navigate", new_callable=AsyncMock, return_value=True) as navigate:
        res = client.post("/api/browser/navigate", json={"url": raw})
    assert res.status_code == 200
    assert res.json()["url"] == expected
    navigate.assert_awaited_once_with(expected)


# --- TLD validatsiyasi regressiyasi (2026-11-27) ---
# Topilgan nuqson: `not-a-url` va `-hel` kabi matn qabul qilinardi — bitta
# nuqtasiz host ham "to'g'ri" hisoblanardi. Playwright bunday manzilga
# "Cannot navigate to invalid URL" bilan yiqilardi.
import pytest as _pytest

from url_validation import normalize_navigation_url


@_pytest.mark.parametrize("bad", ["not-a-url", "-hel", "x", "a.b", "just-text"])
def test_invalid_hosts_rejected(bad):
    with _pytest.raises(ValueError):
        normalize_navigation_url(bad)


@_pytest.mark.parametrize(
    "good,expected",
    [
        ("example.com", "https://example.com"),
        ("https://example.com", "https://example.com"),
        ("sub.domain.co.uk", "https://sub.domain.co.uk"),
        ("localhost:3000", "http://localhost:3000"),
        ("127.0.0.1:8000", "http://127.0.0.1:8000"),
    ],
)
def test_valid_hosts_accepted(good, expected):
    assert normalize_navigation_url(good) == expected
