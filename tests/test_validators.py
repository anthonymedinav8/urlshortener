import pytest

from app.validators import (
    MAX_URL_LENGTH,
    is_valid_short_code,
    normalize_and_validate_url,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("example.com", "https://example.com"),
        ("  example.com/  ", "https://example.com"),
        ("HTTP://Example.COM/Path", "http://example.com/Path"),
        ("https://example.com/Path?Q=1", "https://example.com/Path?Q=1"),
        ("https://example.com/a/b/", "https://example.com/a/b"),
    ],
)
def test_normalize_valid(raw, expected):
    url, err = normalize_and_validate_url(raw)
    assert err is None
    assert url == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        None,
        123,
        "ftp://example.com",
        "javascript:alert(1)",
        "https://",
        "not a url",
    ],
)
def test_normalize_invalid(raw):
    url, err = normalize_and_validate_url(raw)
    assert url is None
    assert err


def test_normalize_too_long():
    raw = "https://example.com/" + ("a" * MAX_URL_LENGTH)
    url, err = normalize_and_validate_url(raw)
    assert url is None
    assert "maximum length" in err


@pytest.mark.parametrize("code", ["abc", "ABC123", "aZ09xy"])
def test_short_code_valid(code):
    assert is_valid_short_code(code)


@pytest.mark.parametrize("code", ["", "abc!", "a" * 11, None, "ab cd"])
def test_short_code_invalid(code):
    assert not is_valid_short_code(code)
