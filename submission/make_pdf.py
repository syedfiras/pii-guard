"""Generate PII-Guard prototype submission PDF (first evaluation round).
Lean version: no self-scored criteria table. Demo section left empty.
Run: python make_pdf.py  (needs fpdf2)
"""
from fpdf import FPDF

NAVY = (11, 18, 36)
BLUE = (47, 123, 255)
SLATE = (51, 65, 85)
MUTED = (100, 116, 139)
LIGHT = (241, 245, 249)
GREEN = (22, 163, 74)
AMBER = (180, 120, 10)
WHITE = (255, 255, 255)

class Doc(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*MUTED)
        self.cell(0, 8, "PII-GUARD MIDDLEWARE  |  Prototype Submission", align="L")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}   |   Synthetic data only - no real personal information used",
                  align="C")

    def h1(self, t):
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(*NAVY)
        self.multi_cell(0, 10, t)
        self.ln(1)

    def h2(self, t):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*NAVY)
        self.cell(0, 9, t)
        self.ln(9)
        self.set_draw_color(*BLUE)
        self.set_line_width(0.8)
        self.line(self.l_margin, self.get_y(), self.l_margin + 40, self.get_y())
        self.ln(4)

    def body(self, t):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*SLATE)
        self.multi_cell(0, 6, t)
        self.ln(2)

    def bullet(self, t, color=None):
        x = self.get_x()
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*(color or BLUE))
        self.cell(6, 6, "-")
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*SLATE)
        self.multi_cell(0, 6, t)
        self.ln(1)

    def box(self, title, lines, fill=LIGHT, tcolor=NAVY):
        self.set_fill_color(*fill)
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*tcolor)
        y0 = self.get_y()
        self.set_x(self.l_margin + 2)
        self.cell(0, 7, title)
        self.ln(7)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*SLATE)
        for ln in lines:
            self.set_x(self.l_margin + 2)
            self.multi_cell(self.w - self.l_margin - self.r_margin - 4, 5.5, ln)
        y1 = self.get_y() + 2
        self.rect(self.l_margin, y0 - 2, self.w - self.l_margin - self.r_margin, y1 - y0 + 2, style="F")
        # repaint text over fill (fpdf draws rect over text, so redraw by resetting)
        self.set_y(y0 - 2)
        self.set_font("Helvetica", "B", 10.5)
        self.set_text_color(*tcolor)
        self.set_x(self.l_margin + 2)
        self.cell(0, 7, title)
        self.ln(7)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*SLATE)
        for ln in lines:
            self.set_x(self.l_margin + 2)
            self.multi_cell(self.w - self.l_margin - self.r_margin - 4, 5.5, ln)
        self.ln(4)


pdf = Doc(format="A4")
pdf.alias_nb_pages()
pdf.set_margins(18, 16, 18)
pdf.set_auto_page_break(True, 20)

# ---------------- PAGE 1 ----------------
pdf.add_page()
pdf.set_fill_color(*NAVY)
pdf.rect(0, 0, 210, 52, style="F")
pdf.set_xy(18, 10)
pdf.set_font("Helvetica", "B", 24)
pdf.set_text_color(*WHITE)
pdf.cell(0, 11, "PII-GUARD MIDDLEWARE")
pdf.ln(11)
pdf.set_x(18)
pdf.set_font("Helvetica", "", 11)
pdf.set_text_color(180, 200, 230)
pdf.cell(0, 7, "Privacy Layer for AI Agents  |  Data Privacy  |  Prototype Submission")
pdf.ln(7)
pdf.set_x(18)
pdf.set_font("Helvetica", "", 9.5)
pdf.cell(0, 6, "Team: [YOUR TEAM NAME]   |   Moodlakatte Institute of Technology, Dept. of CSE")
pdf.ln(14)

pdf.h2("1. The problem we solve")
pdf.body(
    "AI agents may use personal information - such as phone numbers, email addresses, "
    "and identification numbers - to link user tools through prompts and tool parameters. "
    "When an agent calls an external tool (sending an SMS, looking up a record, charging a card), "
    "real personal values travel inside those tool requests and get stored in third-party logs. "
    "A privacy layer is needed to detect and protect sensitive values before outgoing requests "
    "leave the application."
)
pdf.h2("2. Our solution in one line")
pdf.box("Invisible checkpoint for AI agents", [
    "Every agent-to-tool payload passes through PII-Guard middleware: it detects personal "
    "information, substitutes reversible tokens, sends only fakes to the simulated external "
    "tool, and restores the correct original values in the response.",
])
pdf.h2("3. Architecture")
# 4 boxes with arrows
bx, by, bw, bh, gap = 18, pdf.get_y(), 37, 22, 6
labels = [("AI Agent", "builds tool call"), ("DETECT", "find PII"), ("TOKENIZE", "real -> fake"),
          ("Simulated Tool", "sees FAKES only")]
pdf.set_font("Helvetica", "B", 8.5)
for i, (t, s) in enumerate(labels):
    x = bx + i * (bw + gap)
    pdf.set_fill_color(*LIGHT)
    pdf.rect(x, by, bw, bh, style="F")
    pdf.set_draw_color(*BLUE)
    pdf.set_line_width(0.5)
    pdf.rect(x, by, bw, bh, style="D")
    pdf.set_xy(x, by + 3)
    pdf.set_text_color(*NAVY)
    pdf.cell(bw, 5, t, align="C")
    pdf.set_xy(x, by + 10)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*MUTED)
    pdf.cell(bw, 4, s, align="C")
    pdf.set_font("Helvetica", "B", 8.5)
    if i < 3:
        ax = x + bw + 1
        pdf.set_text_color(*BLUE)
        pdf.set_xy(ax, by + 8)
        pdf.cell(gap - 1, 5, ">", align="C")
pdf.set_y(by + bh + 4)
pdf.set_font("Helvetica", "I", 9.5)
pdf.set_text_color(*MUTED)
pdf.cell(0, 6, "Tool answers flow back through the guard: tokens are restored before reaching the agent.")
pdf.ln(10)

# ---------------- PAGE 2 ----------------
pdf.add_page()
pdf.h2("4. How it protects (4 steps)")
steps = [
    ("INTERCEPT", "middleware captures the outgoing agent-to-tool payload, both structured JSON and natural-language text."),
    ("DETECT", "finds phone numbers, email addresses, PAN, Aadhaar and debit/credit card numbers via patterns + checksums (Verhoeff for Aadhaar, Luhn for cards)."),
    ("PROTECT", "replaces each real value with a format-preserving reversible token; a second scan blocks the request if any real value survives (fail-closed)."),
    ("RESTORE", "tool responses containing tokens are mapped back to the correct originals before returning to the agent."),
]
for n, (t, d) in enumerate(steps, 1):
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*BLUE)
    pdf.cell(8, 6, f"{n}.")
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 6, t)
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(*SLATE)
    pdf.set_x(pdf.l_margin + 8)
    pdf.multi_cell(0, 6, d)
    pdf.ln(1)

pdf.h2("5. What it detects")
pdf.set_font("Helvetica", "B", 9.5)
pdf.set_text_color(*WHITE)
pdf.set_fill_color(*NAVY)
cols = [52, 62, 60]
for c, w in zip(["PII TYPE", "HOW DETECTED", "FAKE TOKEN EXAMPLE"], cols):
    pdf.cell(w, 8, "  " + c, fill=True)
pdf.ln(8)
pdf.set_font("Helvetica", "", 9.5)
pdf.set_text_color(*SLATE)
rows = [
    ("Email", "standard pattern", "user_0001@redacted.test"),
    ("Indian phone", "+91 / prefix + 6-9 rule", "+91-00000-00001"),
    ("PAN", "ABCDE1234F uppercase", "QWERT0001Z"),
    ("Aadhaar", "12-digit + Verhoeff", "2999-8888-0001"),
    ("Debit / credit card", "13-19 digits + Luhn", "4111 0000 0000 0024"),
]
fill = False
for r in rows:
    if fill:
        pdf.set_fill_color(*LIGHT)
    for c, w in zip(r, cols):
        pdf.cell(w, 7, "  " + c, fill=fill)
    pdf.ln(7)
    fill = not fill
pdf.ln(3)

pdf.h2("6. Tech stack")
pdf.bullet("Backend: Python + FastAPI (detectors, token vault, audit log).")
pdf.bullet("Frontend: React + Vite demo dashboard (website is the demo face; the product is the middleware).")
pdf.bullet("Tests: pytest, seeded synthetic generator. No external network calls. Synthetic data only.")

# ---------------- PAGE 3 ----------------
pdf.add_page()
pdf.h2("7. Deliverables checklist")
pdf.bullet("Working middleware that intercepts tool-bound requests (POST /api/invoke).", GREEN)
pdf.bullet("Detection for multiple PII types in structured AND natural-language payloads.", GREEN)
pdf.bullet("Redaction + response re-hydration demonstrated live in the dashboard.", GREEN)
pdf.bullet("Test results + audit log showing exactly what the simulated tool received.", GREEN)
pdf.ln(2)
pdf.h2("8. Prototype demonstration")
pdf.body("Live demo link:")
pdf.set_font("Helvetica", "", 11)
pdf.set_text_color(*MUTED)
pdf.cell(0, 8, "[ PASTE DEMO LINK HERE AFTER DEPLOYMENT ]")
pdf.ln(12)
for cap in ["Screenshot 1 - protection verdict (SAFE + detections)",
            "Screenshot 2 - what-the-tool-received vs restored panels",
            "Screenshot 3 - audit log proving the tool got fakes only"]:
    y = pdf.get_y()
    pdf.set_draw_color(*MUTED)
    pdf.set_line_width(0.4)
    pdf.rect(pdf.l_margin, y, pdf.w - pdf.l_margin - pdf.r_margin, 38, style="D")
    pdf.set_xy(pdf.l_margin, y + 12)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MUTED)
    pdf.cell(pdf.w - pdf.l_margin - pdf.r_margin, 6, "[ ADD IMAGE HERE ]", align="C")
    pdf.set_xy(pdf.l_margin, y + 20)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(pdf.w - pdf.l_margin - pdf.r_margin, 5, cap, align="C")
    pdf.set_y(y + 44)

# ---------------- PAGE 4 ----------------
pdf.add_page()
pdf.h2("9. Real-world relevance")
pdf.body(
    "The same checkpoint pattern protects a bank's SMS agent, a hospital booking bot and a "
    "shopping assistant: tools keep working because fakes preserve valid formats (a fake card "
    "still passes checksum validation), while vendor logs stay worthless to attackers. The audit "
    "log is the evidence that the third party never saw real values."
)
pdf.h2("10. Limits and next steps (honest scope)")
pdf.bullet("Names/addresses need ML-based detection; current MVP is pattern + checksum rules.")
pdf.bullet("Production needs an encrypted persistent vault, per-user sessions and key rotation.")
pdf.bullet("CVV/expiry codes are out of scope: any 3-digit number alone is too ambiguous to detect.")
pdf.bullet("Next build: enforced agent demo where the agent cannot bypass the guard.")
pdf.h2("11. Fairness note")
pdf.body(
    "Designed, built and tested with synthetic personal data only. No real personal or "
    "confidential information was used, submitted, or sent to any external service."
)
pdf.h2("12. Reproduce it")
pdf.set_font("Helvetica", "", 10)
pdf.set_text_color(*SLATE)
pdf.multi_cell(0, 6,
    "Backend:  cd backend  >  pip install -r requirements.txt  >  python -m uvicorn app:app --port 8000\n"
    "Frontend: cd frontend  >  npm install  >  npm run dev   (open http://localhost:5173)\n"
    "Tests:    cd backend  >  python -m pytest tests/ -q")

pdf.output("PII-Guard_Prototype_Submission.pdf")
print("written: PII-Guard_Prototype_Submission.pdf")
