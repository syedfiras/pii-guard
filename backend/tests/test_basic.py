"""Quick sanity checks for the core PII types (synthetic data only)."""
from detectors import detect_all
from vault import TokenVault

def test_all():
    text = "Hi Ravi, email ravi.k@test.com phone 9876543210 PAN ABCDE1234F Aadhaar 2344 5678 9012 card 4111 1111 1111 1111"
    dets = detect_all(text, aadhaar_strict=False)
    kinds = {d.type for d in dets}
    assert {"EMAIL", "PHONE", "PAN", "AADHAAR", "CARD"} <= kinds, f"missing: {kinds}"
    v = TokenVault()
    red = text
    for d in sorted(dets, key=lambda x: x.start, reverse=True):
        red = red[:d.start] + v.tokenize(d.type, d.value) + red[d.end:]
    for real in [d.value for d in dets]:
        assert real not in red, f"leak: {real}"
    back = v.restore_text(red)
    assert back == text
    print("PASS: 4 types detect->redact->restore OK")

if __name__ == "__main__":
    test_all()
