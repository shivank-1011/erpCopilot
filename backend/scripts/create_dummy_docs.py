"""
scripts/create_dummy_docs.py — Generate 3 realistic ERP PDF documents.

Uses reportlab to create PDFs with real ERP terminology, business rules,
and enough content for meaningful RAG queries and test case generation.

Documents created in backend/sample_docs/:
  1. erp_release_notes_v2.3.pdf   — SAP S/4HANA mock release notes
  2. gl_posting_process_guide.pdf — General Ledger posting guide
  3. invoice_processing_spec.pdf  — Invoice processing specification
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_docs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Styles ────────────────────────────────────────────────────
styles = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "CustomTitle",
    parent=styles["Title"],
    fontSize=20,
    textColor=colors.HexColor("#1a3a5c"),
    spaceAfter=6,
)
H1_STYLE = ParagraphStyle(
    "H1",
    parent=styles["Heading1"],
    fontSize=14,
    textColor=colors.HexColor("#1a3a5c"),
    spaceBefore=16,
    spaceAfter=6,
    borderPad=4,
)
H2_STYLE = ParagraphStyle(
    "H2",
    parent=styles["Heading2"],
    fontSize=12,
    textColor=colors.HexColor("#2c5f8a"),
    spaceBefore=10,
    spaceAfter=4,
)
BODY_STYLE = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontSize=10,
    leading=15,
    alignment=TA_JUSTIFY,
    spaceAfter=8,
)
BULLET_STYLE = ParagraphStyle(
    "Bullet",
    parent=styles["Normal"],
    fontSize=10,
    leading=14,
    leftIndent=20,
    spaceAfter=4,
    bulletIndent=10,
)
META_STYLE = ParagraphStyle(
    "Meta",
    parent=styles["Normal"],
    fontSize=9,
    textColor=colors.grey,
    spaceAfter=4,
)
WARN_STYLE = ParagraphStyle(
    "Warning",
    parent=styles["Normal"],
    fontSize=10,
    backColor=colors.HexColor("#fff3cd"),
    borderColor=colors.HexColor("#ffc107"),
    borderWidth=1,
    borderPad=6,
    leading=14,
    spaceAfter=8,
)

def bullet(text):
    return Paragraph(f"• {text}", BULLET_STYLE)

def h1(text):
    return Paragraph(text, H1_STYLE)

def h2(text):
    return Paragraph(text, H2_STYLE)

def body(text):
    return Paragraph(text, BODY_STYLE)

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=8)

def space(n=1):
    return Spacer(1, n * 0.15 * inch)


# ════════════════════════════════════════════════════════════════
# DOCUMENT 1: ERP Release Notes v2.3
# ════════════════════════════════════════════════════════════════
def create_release_notes():
    path = os.path.join(OUTPUT_DIR, "erp_release_notes_v2.3.pdf")
    doc = SimpleDocTemplate(path, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    story = []

    story.append(Paragraph("ERP Platform Release Notes", TITLE_STYLE))
    story.append(Paragraph("Version 2.3 — May 2026", META_STYLE))
    story.append(Paragraph("Module: Financial Accounting (FI) &amp; Materials Management (MM)", META_STYLE))
    story.append(hr())
    story.append(space(2))

    # Section 1
    story.append(h1("1. New Features — Financial Accounting Module"))
    story.append(h2("1.1 Enhanced General Ledger Posting Validation"))
    story.append(body(
        "Version 2.3 introduces a new three-tier validation framework for General Ledger (GL) "
        "postings. All journal entries must now pass three sequential validation checkpoints "
        "before they are posted to the ledger. These checkpoints enforce business rules at the "
        "field level, the document level, and the accounting period level respectively."
    ))
    story.append(body(
        "Field-level validation: Every GL posting must include a valid cost center code, "
        "profit center, and business area. Postings that reference inactive or locked GL "
        "accounts will be rejected with error code FI-101: 'Account Not Active for Posting Period'."
    ))
    story.append(body(
        "Document-level validation: The system now enforces that every journal entry document "
        "is balanced (debits equal credits) before saving. Unbalanced documents will trigger "
        "error FI-102: 'Document Not in Balance'. Additionally, the posting amount must not "
        "exceed the configured tolerance limit per transaction type. The default tolerance is "
        "set to USD 500,000. Amounts exceeding this threshold require dual-approval from a "
        "Finance Manager and a CFO-designated approver."
    ))
    story.append(body(
        "Period-level validation: Postings are only allowed in open fiscal periods. "
        "The system validates that the posting date falls within an open period in the Fiscal "
        "Year Variant assigned to the company code. Postings to closed periods will be blocked "
        "with error FI-103: 'Fiscal Period Closed'. Special postings to closed periods require "
        "a Period Exception Request approved by the Finance Controller."
    ))

    story.append(h2("1.2 Two-Way and Three-Way Invoice Matching"))
    story.append(body(
        "The invoice matching engine has been upgraded to support both two-way and three-way "
        "matching workflows. The matching method is configured at the vendor master record level "
        "and can be overridden at the purchase order line item level."
    ))
    story.append(body(
        "Two-way matching (Purchase Order vs. Invoice): The system compares the invoiced "
        "quantity and price against the Purchase Order (PO) line items. A match is considered "
        "successful when the invoice quantity does not exceed the PO quantity by more than 5% "
        "(configurable), and the invoice unit price does not deviate from the PO price by more "
        "than the configured price tolerance (default: 2% or USD 100, whichever is lower)."
    ))
    story.append(body(
        "Three-way matching (Purchase Order vs. Goods Receipt vs. Invoice): In addition to the "
        "PO comparison, the system also validates that a Goods Receipt (GR) document exists "
        "for the invoiced goods before releasing the invoice for payment. The GR quantity must "
        "be at least equal to the invoiced quantity. Invoices without a corresponding GR will "
        "be placed in 'Blocked for Payment' status with reason code MM-001: 'Missing Goods Receipt'."
    ))

    story.append(PageBreak())

    # Section 2
    story.append(h1("2. Approval Workflow Changes"))
    story.append(h2("2.1 Dynamic Approval Routing"))
    story.append(body(
        "Release 2.3 replaces the static approval hierarchy with a dynamic approval routing "
        "engine. Approval routes are now determined at runtime based on the following criteria: "
        "transaction type, posting amount, cost center, and the submitting user's organizational "
        "unit. The routing rules are configured in the Workflow Configuration Table (T-WF01)."
    ))
    story.append(body(
        "Standard transactions (Amount &lt; USD 10,000): Single-level approval by the direct "
        "line manager of the submitting user, as defined in the HR Organizational Structure."
    ))
    story.append(body(
        "Mid-value transactions (USD 10,000 – 100,000): Two-level approval. Level 1: Direct "
        "line manager. Level 2: Department Head. Both approvals must be obtained within 48 hours "
        "of submission; otherwise the transaction is escalated to the Finance Controller."
    ))
    story.append(body(
        "High-value transactions (Amount &gt; USD 100,000): Three-level approval required. "
        "Level 1: Line Manager. Level 2: Finance Manager. Level 3: CFO or designated delegate. "
        "High-value transactions also trigger an automatic notification to the Internal Audit team."
    ))

    story.append(h2("2.2 Approval Delegation"))
    story.append(body(
        "Approvers can now delegate their approval authority to a designated substitute during "
        "planned absences. Delegation is configured in the User Delegation Table (T-WF02) and "
        "requires confirmation from the HR department. Delegation periods cannot exceed 30 "
        "consecutive calendar days. The system sends an automated notification to the original "
        "approver when delegation expires. Emergency delegation (activated within the same business "
        "day) requires approval from the System Administrator."
    ))

    # Section 3
    story.append(h1("3. Bug Fixes and Known Issues"))
    story.append(h2("3.1 Resolved Issues"))
    data = [
        ["Bug ID", "Description", "Module", "Severity"],
        ["BUG-1821", "GL posting date defaulted to system date when period field was blank", "FI", "High"],
        ["BUG-1834", "Invoice matching failed for partial GR with decimal quantities", "MM", "Medium"],
        ["BUG-1856", "Cost center validation bypassed for inter-company postings", "FI", "Critical"],
        ["BUG-1901", "Duplicate invoice check did not trigger for amounts below USD 100", "MM", "Medium"],
        ["BUG-1923", "Approval workflow email notifications sent in wrong language", "WF", "Low"],
    ]
    t = Table(data, colWidths=[1.1*inch, 3.2*inch, 0.9*inch, 1.0*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8fc")]),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(space(2))

    story.append(h2("3.2 Known Issues in v2.3"))
    story.append(Paragraph("⚠️  The following issues are known and will be addressed in v2.3.1:", WARN_STYLE))
    story.append(bullet("KI-001: Three-way match may fail for purchase orders with more than 999 line items. Workaround: Split PO into multiple documents."))
    story.append(bullet("KI-002: Approval delegation does not correctly handle UTC+5:30 timezone for expiry notification emails."))
    story.append(bullet("KI-003: PDF export of GL posting journal does not include cost center breakdowns when more than 50 line items are present."))

    doc.build(story)
    print(f"    ✅  Created: {path}")
    return path


# ════════════════════════════════════════════════════════════════
# DOCUMENT 2: GL Posting Process Guide
# ════════════════════════════════════════════════════════════════
def create_gl_posting_guide():
    path = os.path.join(OUTPUT_DIR, "gl_posting_process_guide.pdf")
    doc = SimpleDocTemplate(path, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    story = []

    story.append(Paragraph("General Ledger Posting — Process Guide", TITLE_STYLE))
    story.append(Paragraph("Finance Operations Team | Version 4.1 | Effective: Jan 2026", META_STYLE))
    story.append(hr())
    story.append(space(2))

    story.append(h1("1. Overview"))
    story.append(body(
        "This guide describes the end-to-end process for creating, validating, and posting "
        "journal entries to the General Ledger (GL) in the ERP system. All finance team members "
        "responsible for GL operations must follow this process. Deviations from this process "
        "require written approval from the Finance Controller and must be documented in the "
        "Process Deviation Log (Form: FIN-DEV-001)."
    ))

    story.append(h1("2. Journal Entry Creation"))
    story.append(h2("2.1 Mandatory Header Fields"))
    story.append(body(
        "Every journal entry must include the following mandatory header-level fields. "
        "The system will reject the entry if any of these fields are missing or contain invalid values."
    ))
    story.append(bullet("Company Code: 4-character alphanumeric code (e.g., US01, DE02, IN03). Must match an active company code in Table T001."))
    story.append(bullet("Document Date: The business date of the transaction. Cannot be a future date (system enforces). Cannot be more than 90 days in the past without Finance Controller approval."))
    story.append(bullet("Posting Date: The date on which the entry will affect the GL. Must fall within an open fiscal period."))
    story.append(bullet("Document Type: Classifies the nature of the journal entry (e.g., SA = GL Account Document, KR = Vendor Invoice, DR = Customer Invoice)."))
    story.append(bullet("Fiscal Year: Automatically derived from the posting date. Cannot be manually overridden."))
    story.append(bullet("Reference: Free-text field (max 16 characters). Used for cross-referencing source documents. Mandatory for all adjusting and reversing entries."))
    story.append(bullet("Header Text: Description of the posting (max 25 characters). Must follow naming convention: [CostCenter]-[Month]-[Type] (e.g., CC1001-MAY26-ADJ)."))
    story.append(space())

    story.append(h2("2.2 Line Item Requirements"))
    story.append(body(
        "Each journal entry must contain at least two line items (debit and credit). "
        "The total debit amount must exactly equal the total credit amount. "
        "The maximum number of line items per document is 999."
    ))
    story.append(body(
        "Required line item fields: GL Account, Debit/Credit indicator (D/C), Amount, Currency, "
        "Cost Center (mandatory for expense accounts in account ranges 400000–599999), "
        "Profit Center, Tax Code (if applicable), and Line Item Text (description, max 50 chars)."
    ))
    story.append(body(
        "GL accounts in the range 100000–199999 are balance sheet accounts. Postings to these "
        "accounts do not require a cost center. GL accounts in range 400000–599999 are P&L "
        "(profit and loss) accounts and always require a valid, active cost center. Postings "
        "to inactive cost centers will generate error message FI-204: 'Cost Center Not Active'."
    ))

    story.append(PageBreak())

    story.append(h1("3. Posting Procedures"))
    story.append(h2("3.1 Normal Posting Procedure"))
    story.append(body("Follow these steps to create and post a standard journal entry:"))
    steps = [
        "Navigate to: Accounting → Financial Accounting → General Ledger → Document Entry → Enter G/L Account Document (T-code: FB50).",
        "Enter all mandatory header fields (Company Code, Document Date, Posting Date, Document Type).",
        "Enter line items. Use the 'Add Item' button to add each debit and credit line.",
        "Click 'Check' (F5) to run field-level and document-level validations. Resolve all error messages before proceeding.",
        "If the document requires approval (amount exceeds threshold), click 'Park' instead of 'Post'. The document will be routed to the approval workflow automatically.",
        "If no approval is required, click 'Post' (Ctrl+S). Note the assigned Document Number for your records.",
        "Attach supporting documents (invoices, contracts, receipts) to the posted document using the Attachment Manager (GOS).",
    ]
    for i, step in enumerate(steps, 1):
        story.append(Paragraph(f"{i}. {step}", BULLET_STYLE))
    story.append(space())

    story.append(h2("3.2 Period-End Closing Procedures"))
    story.append(body(
        "At the end of each fiscal period, the following closing tasks must be completed "
        "before the period can be closed. These tasks are listed in order of dependency — "
        "each task must be completed before the next can begin."
    ))
    story.append(bullet("Task 1 — Accruals posting: All accrual entries must be posted by the 2nd business day of the following month."))
    story.append(bullet("Task 2 — Prepaid amortisation: Finance team runs the prepaid amortisation batch job (Program: FIN_PREPAID_AMZ) on the 3rd business day."))
    story.append(bullet("Task 3 — Intercompany reconciliation: All intercompany transactions must be reconciled and confirmed by both entities. Unreconciled items are flagged in Report: FIN_IC_RECON."))
    story.append(bullet("Task 4 — Trial balance review: Finance Controller reviews the trial balance report (T-code: F.01) and signs off by the 5th business day."))
    story.append(bullet("Task 5 — Period lock: System Administrator locks the fiscal period in T-code OB52. No further postings are allowed after locking."))

    story.append(h1("4. Error Handling and Escalation"))
    story.append(body(
        "When the system rejects a GL posting, the user receives an error message with a "
        "specific error code. The following table lists the most common error codes, their "
        "meanings, and the recommended resolution steps."
    ))

    data = [
        ["Error Code", "Description", "Resolution"],
        ["FI-101", "Account Not Active for Posting Period", "Contact Finance Admin to activate account or use an alternative account."],
        ["FI-102", "Document Not in Balance", "Check that total debits equal total credits. Adjust line items."],
        ["FI-103", "Fiscal Period Closed", "Request Period Exception from Finance Controller (Form: FIN-PE-001)."],
        ["FI-104", "Duplicate Document Detected", "Verify the reference number. If posting is valid, contact Finance Admin."],
        ["FI-204", "Cost Center Not Active", "Use active cost center or request activation from Cost Center Admin."],
        ["FI-301", "Tolerance Exceeded — Approval Required", "Park document. Approval workflow will route automatically."],
    ]
    t = Table(data, colWidths=[1.1*inch, 2.0*inch, 3.1*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5f8a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f5fb")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("WORDWRAP", (0, 0), (-1, -1), True),
    ]))
    story.append(t)

    doc.build(story)
    print(f"    ✅  Created: {path}")
    return path


# ════════════════════════════════════════════════════════════════
# DOCUMENT 3: Invoice Processing Specification
# ════════════════════════════════════════════════════════════════
def create_invoice_spec():
    path = os.path.join(OUTPUT_DIR, "invoice_processing_spec.pdf")
    doc = SimpleDocTemplate(path, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    story = []

    story.append(Paragraph("Invoice Processing — Technical Specification", TITLE_STYLE))
    story.append(Paragraph("Materials Management Module | Version 3.0 | April 2026", META_STYLE))
    story.append(Paragraph("Scope: Vendor Invoice Processing, Payment Terms, and Exception Handling", META_STYLE))
    story.append(hr())
    story.append(space(2))

    story.append(h1("1. Invoice Receipt and Registration"))
    story.append(body(
        "All vendor invoices must be registered in the ERP system within 2 business days of "
        "physical or electronic receipt. Invoices received via email must be forwarded to the "
        "centralized Accounts Payable inbox (ap-invoices@company.com) for automated ingestion "
        "via the Document Capture System (DCS). Paper invoices must be scanned and uploaded "
        "to the Invoice Management Portal (IMP) using T-code MIRO or the self-service web portal."
    ))
    story.append(body(
        "Each invoice registration creates a Logical Invoice Document (LID) in the system with "
        "a unique 10-digit LID number. The LID number must be used in all subsequent "
        "communications and processing steps related to that invoice."
    ))

    story.append(h2("1.1 Mandatory Invoice Fields"))
    story.append(body("The following fields must be captured for every invoice:"))
    story.append(bullet("Vendor Number: Must match an active vendor in the Vendor Master (T-code: XK03)."))
    story.append(bullet("Invoice Number: As printed on the vendor's invoice. Maximum 16 characters."))
    story.append(bullet("Invoice Date: Date on the vendor's original invoice document."))
    story.append(bullet("Invoice Amount: Gross invoice amount including tax."))
    story.append(bullet("Currency: Invoice currency code (ISO 4217). Must match PO currency unless currency conversion is approved."))
    story.append(bullet("Tax Code: VAT/GST tax code applicable to the invoice. Auto-suggested based on vendor's tax classification."))
    story.append(bullet("Purchase Order Number: Referenced PO number for 2-way or 3-way matching. Mandatory for all goods and service invoices."))
    story.append(bullet("Payment Terms: Payment terms code (e.g., NT30 = Net 30 days, NT60 = Net 60 days). Defaults from vendor master."))

    story.append(PageBreak())

    story.append(h1("2. Payment Terms Configuration"))
    story.append(body(
        "Payment terms define when a vendor invoice becomes due for payment and whether early "
        "payment discounts (cash discounts) are offered. Payment terms are configured in the "
        "Payment Terms Table (T052) and assigned at the vendor master record level. They can "
        "be overridden at the purchase order or invoice level with Finance Manager approval."
    ))

    data = [
        ["Term Code", "Description", "Due Date Calculation", "Early Pay Discount"],
        ["NT00", "Payable immediately", "Invoice date", "None"],
        ["NT30", "Net 30 days", "Invoice date + 30 days", "None"],
        ["NT60", "Net 60 days", "Invoice date + 60 days", "None"],
        ["2/10NT30", "2% discount if paid in 10 days, else net 30", "Invoice date + 30 days", "2% if paid by day 10"],
        ["3/7NT45", "3% discount if paid in 7 days, else net 45", "Invoice date + 45 days", "3% if paid by day 7"],
        ["EOM30", "End of month + 30 days", "Last day of invoice month + 30 days", "None"],
    ]
    t = Table(data, colWidths=[1.0*inch, 1.8*inch, 1.8*inch, 1.6*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8fc")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(space(2))

    story.append(h1("3. Three-Way Invoice Matching Rules"))
    story.append(body(
        "Three-way matching compares the Purchase Order (PO), the Goods Receipt (GR), and "
        "the vendor Invoice to ensure all three documents are in agreement before payment is "
        "authorized. The following tolerance rules govern the matching process:"
    ))
    story.append(h2("3.1 Quantity Tolerance"))
    story.append(body(
        "Invoice quantity must not exceed the GR quantity. A maximum over-delivery tolerance "
        "of 3% is permitted (configurable per vendor in the Vendor Master). Under-delivery "
        "invoices (invoice quantity less than GR quantity) are accepted and payment is made "
        "for the invoiced quantity only. The remaining PO quantity remains open for future invoices."
    ))
    story.append(h2("3.2 Price Tolerance"))
    story.append(body(
        "Invoice unit price is compared against the PO unit price. Acceptable deviation: "
        "the lesser of 2% or USD 50 per unit. Invoices exceeding this tolerance are "
        "automatically blocked for payment with status MM-PRICE-BLOCK and routed to the "
        "Procurement team for vendor clarification. The Procurement team must resolve "
        "price discrepancies within 5 business days or escalate to the Vendor Manager."
    ))
    story.append(h2("3.3 Blocking and Exception Handling"))
    story.append(body(
        "Invoices that fail three-way match are placed in 'Blocked' status. Blocked invoices "
        "appear in the Blocked Invoice Report (T-code: MRBR). The AP Specialist responsible "
        "for the vendor must investigate and resolve the block within the following SLA timeframes:"
    ))
    story.append(bullet("Price discrepancy: 5 business days from blocking date."))
    story.append(bullet("Missing Goods Receipt: 10 business days. If GR is not received within this period, the AP Specialist must contact the receiving warehouse and escalate to the Procurement Manager."))
    story.append(bullet("Quantity discrepancy: 3 business days. AP Specialist contacts vendor for credit note or delivery confirmation."))
    story.append(bullet("Duplicate invoice: Automatically rejected. Vendor is notified by system-generated email with original LID number."))

    story.append(h1("4. Payment Execution"))
    story.append(body(
        "Approved invoices are included in the next scheduled payment run. Payment runs are "
        "executed on every Monday and Thursday at 11:00 PM UTC using the Automatic Payment "
        "Program (T-code: F110). The payment run selects all approved invoices due for payment "
        "on or before the next payment run date plus 3 days (payment horizon)."
    ))
    story.append(body(
        "Payments are made via bank transfer (ACH or SWIFT depending on vendor's bank) or "
        "check (for vendors without electronic banking). The payment amount is converted to "
        "the vendor's preferred payment currency at the exchange rate loaded daily from the "
        "Central Bank feed at 09:00 AM UTC."
    ))
    story.append(body(
        "Early payment discounts are automatically captured if the payment run date falls "
        "within the discount period. The discount amount is posted to GL account 540010 "
        "(Cash Discount Received) with document type ZD (Discount Document)."
    ))

    doc.build(story)
    print(f"    ✅  Created: {path}")
    return path


# ════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n📄  Creating dummy ERP documents...")
    print(f"    Output directory: {OUTPUT_DIR}\n")

    create_release_notes()
    create_gl_posting_guide()
    create_invoice_spec()

    print("\n✅  All 3 dummy ERP documents created!")
    print("\nDocuments created:")
    print("  • erp_release_notes_v2.3.pdf     — SAP-style release notes")
    print("  • gl_posting_process_guide.pdf    — GL posting guide")
    print("  • invoice_processing_spec.pdf     — Invoice processing spec")
    print(f"\nLocation: {OUTPUT_DIR}")
    print("\nYou can now upload these via the ERP Copilot Lite frontend.")
    print("Or test directly via the API at http://localhost:8000/docs\n")
