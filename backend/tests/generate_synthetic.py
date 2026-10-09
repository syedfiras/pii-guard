"""Synthetic-only test data generator. No real PII. Deterministic seed."""
import random

random.seed(42)
FIRST = ["Ravi", "Priya", "Amit", "Sneha", "Arjun", "Kavya", "Vikram", "Divya"]
LAST = ["Kumar", "Sharma", "Patel", "Reddy", "Iyer", "Singh"]

def _phone():
    fmt = random.choice(["{}", "+91-{}", "+91 {}"])
    core = str(random.choice([6, 7, 8, 9])) + "".join(str(random.randint(0, 9)) for _ in range(9))
    if random.random() < 0.3:
        core = core[:5] + " " + core[5:]
    return fmt.format(core)

def _email(i):
    return f"user{i:03d}.test@test{random.randint(1,3)}.com"

def _pan():
    import string
    L = lambda n: "".join(random.choice(string.ascii_uppercase) for _ in range(n))
    return f"{L(5)}{random.randint(1000,9999)}{random.choice(string.ascii_uppercase)}"

def _aadhaar():
    # format-valid synthetic (not real). 12 digits starting 2-9.
    return f"{random.randint(2,9)}{random.randint(100,999)} {random.randint(1000,9999)} {random.randint(1000,9999)}"

def _card():
    # Luhn-valid synthetic test numbers (not real). Random brand prefix.
    import sys
    sys.path.insert(0, ".")
    from detectors import luhn_check_digit
    prefix = random.choice(["4111", "5555", "6011", "3782"])
    total = 15 if prefix == "3782" else 16
    body = "".join(str(random.randint(0, 9)) for _ in range(total - 1 - len(prefix)))
    full = prefix + body + luhn_check_digit(prefix + body)
    if total == 15:
        return f"{full[:4]} {full[4:10]} {full[10:]}"
    sep = random.choice([" ", "-", ""])
    if sep:
        return sep.join(full[i:i + 4] for i in range(0, 16, 4))
    return full

def make_case(i):
    """Returns (text_with_pii, expected_types_set)."""
    kind = random.choice(["all", "email", "phone", "pan", "aadhaar", "card", "none", "noisy"])
    name = f"{random.choice(FIRST)} {random.choice(LAST)}"
    if kind == "all":
        t = f"Hi {name}, email {_email(i)}, call {_phone()}, PAN {_pan()}, Aadhaar {_aadhaar()}, card {_card()}."
        exp = {"EMAIL", "PHONE", "PAN", "AADHAAR", "CARD"}
    elif kind == "email":
        t = f"Send invoice to {_email(i)} please."
        exp = {"EMAIL"}
    elif kind == "phone":
        t = f"Call {name} on {_phone()} tomorrow."
        exp = {"PHONE"}
    elif kind == "pan":
        t = f"KYC PAN {_pan()} verify."
        exp = {"PAN"}
    elif kind == "aadhaar":
        t = f"Aadhaar {_aadhaar()} for proof."
        exp = {"AADHAAR"}
    elif kind == "card":
        label = random.choice(["credit card", "debit card", "card"])
        t = f"My {label} {_card()} for payment."
        exp = {"CARD"}
    elif kind == "noisy":
        # edge: order id that looks like aadhaar but invalid + lowercase pan (should NOT match)
        # + dummy 16-digit number (bad Luhn + trivial sequence, should NOT match as CARD;
        #   all-1s prefix also matches no AADHAAR/PHONE start rule)
        t = f"Order 123456789012, pan abcde1234f, phone 5123456789 invalid, card 1111111111111111 bad."
        exp = set()
    else:
        t = f"Hello {name}, your order shipped, track ID {100000+i}."
        exp = set()
    return t, exp

def make_suite(n=100):
    return [make_case(i) for i in range(n)]

if __name__ == "__main__":
    for t, e in make_suite(10):
        print(t, "->", e)
