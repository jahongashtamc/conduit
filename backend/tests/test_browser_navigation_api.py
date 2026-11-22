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
