"""Verification tests for himalaya.py and accounts.py — required scope for continuation obligation."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from email_skill_lib.himalaya import is_available, scan_account, _normalize_envelope, _parse_from
from email_skill_lib.accounts import ACCOUNTS, derive_provider


def test_himalaya_available():
    assert is_available() is True, "himalaya should be on PATH"

def test_accounts_count():
    assert len(ACCOUNTS) == 3, f"expected 3 accounts, got {len(ACCOUNTS)}"

def test_account_names():
    names = [a["name"] for a in ACCOUNTS]
    assert "a-hominidae" in names
    assert "troup-hominidae" in names
    assert "brsthomson" in names

def test_derive_provider():
    assert derive_provider("test@gmail.com") == "gmail"
    assert derive_provider("test@hotmail.com") == "outlook"

def test_scan_a_hominidae():
    acct = [a for a in ACCOUNTS if a["name"] == "a-hominidae"][0]
    result = scan_account(acct, max_items=2)
    assert result["error"] is None, f"unexpected error: {result['error']}"
    assert len(result["items"]) > 0, "expected at least 1 item"

def test_scan_troup_hominidae():
    acct = [a for a in ACCOUNTS if a["name"] == "troup-hominidae"][0]
    result = scan_account(acct, max_items=2)
    assert result["error"] is None, f"unexpected error: {result['error']}"
    assert len(result["items"]) > 0, "expected at least 1 item"

def test_normalize_envelope():
    env = {
        "id": "123",
        "subject": "test",
        "from": [{"name": "Alice", "email": "alice@example.com"}],
        "date": "2026-07-29T12:00:00Z",
        "flags": ["seen"],
    }
    result = _normalize_envelope(env, "test-account")
    assert result["subject"] == "test"
    assert result["account"] == "test-account"

def test_parse_from_string():
    name, email = _parse_from("Alice <alice@example.com>")
    assert email == "alice@example.com"

def test_parse_from_object():
    name, email = _parse_from({"name": "Bob", "email": "bob@example.com"})
    assert email == "bob@example.com"
