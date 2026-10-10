"""Layered-protection tests: unpredictability, at-rest secrecy, wipe, TTL."""
import sys

sys.path.insert(0, ".")
from cryptography.fernet import Fernet

from vault import TokenVault, SessionVaultStore


def _stored_blob(v):
    return repr([v._sealed, v._index])


def test_tokens_unpredictable_across_sessions():
    a, b = TokenVault(), TokenVault()
    assert a.tokenize("PHONE", "9876543210") != b.tokenize("PHONE", "9876543210")


def test_same_session_dedupes():
    v = TokenVault()
    assert v.tokenize("EMAIL", "a@test.com") == v.tokenize("EMAIL", "a@test.com")


def test_no_plaintext_at_rest():
    v = TokenVault()
    v.tokenize("PAN", "ABCDE1234F")
    v.tokenize("EMAIL", "a@test.com")
    assert "ABCDE1234F" not in _stored_blob(v)
    assert "a@test.com" not in _stored_blob(v)


def test_public_mapping_is_masked():
    v = TokenVault()
    t = v.tokenize("PAN", "ABCDE1234F")
    assert v.tokens()[t] != "ABCDE1234F"


def test_wrong_key_cannot_restore():
    v = TokenVault()
    t = v.tokenize("EMAIL", "a@test.com")
    red = f"send to {t}"
    assert v.restore_text(red) == "send to a@test.com"
    thief = TokenVault(key=Fernet.generate_key())
    thief._sealed = dict(v._sealed)  # attacker copied the stored blobs
    assert thief.restore_text(red) == red  # unrestorable, never garbage


def test_wipe_kills_restore():
    v = TokenVault()
    t = v.tokenize("PHONE", "9876543210")
    assert v.wipe() == 1
    assert v.restore_text(t) == t
    assert v.tokens() == {}


def test_session_reveal_and_ttl():
    store = SessionVaultStore(ttl_seconds=3600)
    sid, v = store.get()
    t = v.tokenize("EMAIL", "a@test.com")
    assert store.reveal(sid, [t]) == {t: "a@test.com"}
    assert store.reveal("unknown-session", [t]) == {}
    store._sessions[sid][1] -= 7200  # age it past TTL
    sid2, _ = store.get()
    assert sid2 != sid
    assert store.reveal(sid, [t]) == {}


def test_session_wipe():
    store = SessionVaultStore()
    s1, v1 = store.get()
    s2, v2 = store.get()
    v1.tokenize("EMAIL", "a@test.com")
    v2.tokenize("EMAIL", "b@test.com")
    assert store.wipe() == 2
    assert store.wipe(s1) == 0
