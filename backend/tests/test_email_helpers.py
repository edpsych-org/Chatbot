"""Tests for email template helpers."""
from app.utils.email import _format_expiry


def test_format_expiry_one_day():
    assert _format_expiry(24) == "1 day"


def test_format_expiry_just_below_one_day():
    # Boundary: 23 hours is still "23 hours", not rounded to "1 day"
    assert _format_expiry(23) == "23 hours"


def test_format_expiry_seven_days():
    assert _format_expiry(168) == "7 days"


def test_format_expiry_two_days():
    assert _format_expiry(48) == "2 days"


def test_format_expiry_one_hour():
    assert _format_expiry(1) == "1 hour"


def test_format_expiry_non_day_multiple():
    assert _format_expiry(36) == "36 hours"


def test_format_expiry_zero_hours():
    # Edge: zero should be "0 hours" not "0 days"
    assert _format_expiry(0) == "0 hours"
