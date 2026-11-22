"""Browser navigatsiyasi chegaradagi URL validatsiyasi."""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import url_validation  # noqa: E402


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("example.com", "https://example.com"),
        ("https://github.com/obra/superpowers", "https://github.com/obra/superpowers"),
        ("http://localhost:3000", "http://localhost:3000"),
        ("localhost:3000", "http://localhost:3000"),
        ("127.0.0.1:8000/api/health", "http://127.0.0.1:8000/api/health"),
    ],
)
def test_valid_urls(raw, expected):
    assert url_validation.normalize_navigation_url(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "-hel",
        "https://-hel",
        "http://",
        "javascript:alert(1)",
        "file:///C:/Windows",
        "https://bad_host.example",
        "https://exa mple.com",
    ],
)
def test_invalid_urls_rejected(raw):
    with pytest.raises(ValueError):
        url_validation.normalize_navigation_url(raw)
