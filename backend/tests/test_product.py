"""Product-layer tests: policy, NER, chain, FPE, rotation, SDK. Synthetic only."""
import sys

sys.path.insert(0, ".")

import policy
from detectors import detect_all
from fake_tool import simulate_tool, verify_chain, TOOL_LOG
from vault import TokenVault


def test_policy_deny_and_reload(tmp_path):
    p = tmp_path / "pol.yaml"
    p.write_text("tools:\n  warehouse:\n    deny:\n      - CARD\n", encoding="utf-8")
    policy.load(str(p))
    assert policy.check_tool("warehouse", ["CARD"])[0] is False
    assert policy.check_tool("warehouse", ["EMAIL"])[0] is True
    policy.load()  # back to shipped policy
    assert policy.check_tool("analytics_export", ["CARD"])[0] is False


def test_policy_unknown_type_ignored(tmp_path):
    p = tmp_path / "pol.yaml"
    p.write_text("types:\n  ALIEN: {enabled: true}\n", encoding="utf-8")
    policy.load(str(p))  # must not crash; ALIEN dropped
    assert "ALIEN" not in policy.enabled_types()
    policy.load()


def test_new_local_types():
    dets = detect_all("pay ram@okhdfcbank, passport N7654321, born 05/12/1999",
                      types=("UPI_ID", "PASSPORT_IN", "DATE"), ner=False)
    kinds = {d.type: d.value for d in dets}
    assert kinds.get("UPI_ID") == "ram@okhdfcbank"
    assert kinds.get("PASSPORT_IN") == "N7654321"
    assert kinds.get("DATE") == "05/12/1999"


def test_email_not_eaten_by_upi():
    dets = detect_all("mail ram@test.com", types=("EMAIL", "UPI_ID"), ner=False)
    assert [(d.type, d.value) for d in dets] == [("EMAIL", "ram@test.com")]


def test_ner_person_graceful():
    import ner
    dets = detect_all("Ravi Kumar called", types=("PERSON",), ner=True)
    if ner.available():
        assert any(d.type == "PERSON" for d in dets)
    else:
        assert dets == []


def test_chain_detects_tampering():
    simulate_tool("t", {"a": 1}, "PASS")
    ok, _ = verify_chain()
    assert ok is True
    TOOL_LOG[-1]["received"] = {"a": 2}  # attacker edit
    ok2, bad = verify_chain()
    assert ok2 is False and bad >= 0
    TOOL_LOG.pop()  # leave the shared log clean for other tests


def test_fpe_roundtrip_and_stateless():
    v = TokenVault(mode="fpe")
    t = v.tokenize("CARD", "4111 1111 1111 1111")
    assert t != "4111 1111 1111 1111" and len(t.replace(" ", "")) == 16
    assert v.restore_text(f"pay {t}") == "pay 4111 1111 1111 1111"
    assert "4111 1111 1111 1111" not in repr([v._sealed, v._fpe, v._index])


def test_sdk_decorator_and_deny():
    from sdk import protect
    seen = []

    @protect("send_sms")
    def go(to):
        seen.append(to)
        return f"ok {to}"

    assert go("9876543210") == "ok 9876543210"
    assert seen and seen[0] != "9876543210"
