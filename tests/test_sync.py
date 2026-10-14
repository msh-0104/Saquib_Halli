import pytest
from src.parser import sanitize_diff, parse_diff_summary
from src.mapper import map_changes_to_docs

def test_sanitize_diff_redaction():
    raw_diff = "+ api_key = \"secret_sk_live_1234567890abcdef\"\n+ password = \"supersecret123\""
    clean_diff = sanitize_diff(raw_diff)
    assert "[REDACTED_SECRET]" in clean_diff
    assert "secret_sk_live" not in clean_diff

def test_parse_diff_summary():
    mock_diff = "diff --git a/src/api/users.py b/src/api/users.py\n--- a/src/api/users.py\n+++ b/src/api/users.py\n"
    files = parse_diff_summary(mock_diff)
    assert "src/api/users.py" in files
