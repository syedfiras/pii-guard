"""Audit persistence: entries survive restarts, evidence pack summarizes. Synthetic only."""
import json
import os
import sys

sys.path.insert(0, ".")

import fake_tool
from fake_tool import simulate_tool, record_blocked, evidence


def _use_tmp(tmp_path):
    os.environ["VEIL_AUDIT_FILE"] = str(tmp_path / "audit.jsonl")


def test_entries_persist_to_disk(tmp_path):
    _use_tmp(tmp_path)
    simulate_tool("send_sms", {"text": "hello"}, "PASS")
    path = tmp_path / "audit.jsonl"
    assert path.exists()
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    entry = json.loads(lines[-1])
    assert entry["tool"] == "send_sms"
    assert entry["verdict"] == "PASS"
    assert "vault" not in json.dumps(entry).lower()


def test_blocked_recorded_and_summarized(tmp_path):
    _use_tmp(tmp_path)
    before = evidence()["summary"]["blocked_before_send"]
    record_blocked("send_sms")
    after = evidence()["summary"]
    assert after["blocked_before_send"] == before + 1
    assert after["total_tool_calls"] >= 0


def test_evidence_never_holds_originals(tmp_path):
    _use_tmp(tmp_path)
    simulate_tool("lookup_account", {"q": "user_0001__@redacted.test"}, "PASS")
    blob = json.dumps(evidence())
    assert "real_to_token" not in blob
    assert "token_to_real" not in blob
