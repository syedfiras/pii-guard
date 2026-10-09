"""Metrics suite: detection %, leakage %, restoration %, performance. Synthetic only."""
import sys, time
sys.path.insert(0, ".")
from detectors import detect_all
from vault import TokenVault
from generate_synthetic import make_suite

def run(n=100):
    suite = make_suite(n)
    per_type = {t: {"tp": 0, "fp": 0, "fn": 0} for t in ["EMAIL", "PHONE", "PAN", "AADHAAR", "CARD"]}
    leaks = 0
    restore_ok = 0
    lat = []
    for text, expected in suite:
        t0 = time.perf_counter()
        dets = detect_all(text, aadhaar_strict=False)
        lat.append((time.perf_counter() - t0) * 1000)
        found = {d.type for d in dets}
        for t in per_type:
            if t in expected and t in found:
                per_type[t]["tp"] += 1
            elif t in expected:
                per_type[t]["fn"] += 1
            elif t in found:
                per_type[t]["fp"] += 1
        # leakage + restore check via vault
        v = TokenVault()
        red = text
        for d in sorted(dets, key=lambda x: x.start, reverse=True):
            red = red[:d.start] + v.tokenize(d.type, d.value) + red[d.end:]
        if any(d.value in red for d in dets):
            leaks += 1
        if v.restore_text(red) == text:
            restore_ok += 1
    total_tp = sum(x["tp"] for x in per_type.values())
    total_fn = sum(x["fn"] for x in per_type.values())
    detection_pct = round(100 * total_tp / max(1, total_tp + total_fn), 1)
    print(f"cases={n} detection={detection_pct}% leaks={leaks} restore={restore_ok}/{n} "
          f"avg_ms={sum(lat)/len(lat):.2f} p95_ms={sorted(lat)[int(len(lat)*0.95)]:.2f}")
    for t, x in per_type.items():
        prec = x["tp"] / max(1, x["tp"] + x["fp"])
        rec = x["tp"] / max(1, x["tp"] + x["fn"])
        print(f"  {t}: tp={x['tp']} fp={x['fp']} fn={x['fn']} P={prec:.2f} R={rec:.2f}")
    return detection_pct

def test_metrics():
    assert run(100) >= 80, "detection below 80% — check detectors"

if __name__ == "__main__":
    run(100)
