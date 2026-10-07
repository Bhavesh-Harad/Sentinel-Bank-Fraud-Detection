"""
SENTINEL — Report service.
Generates publication-grade, professionally formatted and styled PDF fraud investigation reports using ReportLab.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas


# ── Color Palette ─────────────────────────────────────────────────────────────
NAVY_PRIMARY = colors.HexColor("#0f172a")     # Slate 900
BLUE_ACCENT = colors.HexColor("#1d4ed8")      # Deep blue
BLUE_LIGHT = colors.HexColor("#eff6ff")       # Blue 50
TEXT_DARK = colors.HexColor("#1e293b")        # Slate 800
TEXT_MUTED = colors.HexColor("#64748b")       # Slate 500
BORDER_COLOR = colors.HexColor("#cbd5e1")     # Slate 300
BORDER_LIGHT = colors.HexColor("#e2e8f0")     # Slate 200
BG_ROW_EVEN = colors.HexColor("#f8fafc")      # Slate 50
BG_WHITE = colors.HexColor("#ffffff")

# Severity Colors & Light Backgrounds
RISK_COLORS = {
    "CRITICAL": {
        "primary": colors.HexColor("#dc2626"),
        "light": colors.HexColor("#fef2f2"),
        "border": colors.HexColor("#f87171"),
        "label": "CRITICAL RISK",
        "action": "ACTION REQUIRED: IMMEDIATE ACCOUNT FREEZE & VERIFICATION",
    },
    "HIGH_RISK": {
        "primary": colors.HexColor("#ea580c"),
        "light": colors.HexColor("#fff7ed"),
        "border": colors.HexColor("#fb923c"),
        "label": "HIGH RISK",
        "action": "ACTION REQUIRED: SUSPEND TRANSACTION & CONTACT CARDHOLDER",
    },
    "SUSPICIOUS": {
        "primary": colors.HexColor("#d97706"),
        "light": colors.HexColor("#fffbeb"),
        "border": colors.HexColor("#fcd34d"),
        "label": "SUSPICIOUS ACTIVITY",
        "action": "RECOMMENDED: SECONDARY AUTHENTICATION & TRANSACTION REVIEW",
    },
    "NORMAL": {
        "primary": colors.HexColor("#059669"),
        "light": colors.HexColor("#ecfdf5"),
        "border": colors.HexColor("#6ee7b7"),
        "label": "NORMAL / VERIFIED",
        "action": "APPROVED: TRANSACTION CLEARED BY RISK PROTOCOLS",
    },
}


class NumberedCanvas(canvas.Canvas):
    """Custom canvas that computes total page count dynamically for professional footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)

        # Bottom rule
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(40, 42, 555, 42)

        # Footer Left
        self.drawString(40, 30, "SENTINEL AI™ — Real-Time Transaction Security Platform (Confidential)")
        # Footer Right
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(555, 30, page_str)
        self.restoreState()


class ReportService:

    @staticmethod
    def generate_transaction_report(
        transaction: dict[str, Any],
        prediction: Optional[dict[str, Any]],
        risk_factors: list[dict[str, Any]],
        customer_profile: Optional[dict[str, Any]],
    ) -> bytes:
        """
        Generate a publication-grade PDF report for a single transaction.
        Returns raw PDF bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=36,
            bottomMargin=54,
        )

        content_width = 515  # 595.27 (A4) - 80 margins
        styles = getSampleStyleSheet()

        # Custom typography styles
        style_title = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=NAVY_PRIMARY,
        )
        style_subtitle = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=TEXT_MUTED,
        )
        style_meta_right = ParagraphStyle(
            "MetaRight",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            alignment=TA_RIGHT,
            textColor=TEXT_MUTED,
        )
        style_section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=NAVY_PRIMARY,
            spaceBefore=10,
            spaceAfter=4,
        )
        style_table_header = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
        )
        style_cell_bold = ParagraphStyle(
            "CellBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=TEXT_DARK,
        )
        style_cell_normal = ParagraphStyle(
            "CellNormal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=TEXT_DARK,
        )
        style_cell_desc = ParagraphStyle(
            "CellDesc",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=TEXT_DARK,
        )

        story: list[Any] = []

        # ── 1. Modern Header with Logo Branding & Metadata ────────────────────
        now_str = datetime.utcnow().strftime("%B %d, %Y • %H:%M:%S UTC")
        txn_id = str(transaction.get("transaction_id", "UNKNOWN"))
        cust_id = str(transaction.get("customer_id", "UNKNOWN"))

        header_left = Paragraph(
            f"<b>SENTINEL AI</b><br/>"
            f"<font size=8 color='#1d4ed8'>INTELLIGENT FRAUD PREVENTION & INVESTIGATION REPORT</font>",
            style_title,
        )
        header_right = Paragraph(
            f"<b>Report Ref:</b> SEC-{txn_id[:12]}<br/>"
            f"<b>Generated:</b> {now_str}<br/>"
            f"<b>Classification:</b> STRICTLY CONFIDENTIAL",
            style_meta_right,
        )

        header_table = Table([[header_left, header_right]], colWidths=[315, 200])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(header_table)
        story.append(HRFlowable(width="100%", thickness=1.5, color=BLUE_ACCENT, spaceAfter=8, spaceBefore=4))

        # ── 2. Prominent Executive Risk Assessment Banner ────────────────────
        risk_level = str((prediction or {}).get("risk_level", "NORMAL")).upper()
        raw_score = float((prediction or {}).get("risk_score", 0.0))
        risk_score = round(raw_score, 2)
        recon_err = float((prediction or {}).get("reconstruction_error", 0.0))
        anomaly_score = float((prediction or {}).get("anomaly_score", 0.0))
        pred_label = str((prediction or {}).get("prediction", "NORMAL"))

        r_cfg = RISK_COLORS.get(risk_level, RISK_COLORS["NORMAL"])
        color_p = r_cfg["primary"]
        color_bg = r_cfg["light"]
        color_bd = r_cfg["border"]

        banner_text = Paragraph(
            f"<font color='{color_p.hexval()}' size=13><b>{r_cfg['label']}</b></font><br/>"
            f"<font color='#334155' size=8><b>Recommendation:</b> {r_cfg['action']}</font>",
            style_cell_normal,
        )
        banner_score = Paragraph(
            f"<font size=7 color='#64748b'>RISK SCORE</font><br/>"
            f"<font size=18 color='{color_p.hexval()}'><b>{risk_score:.2f}</b></font>"
            f"<font size=9 color='#64748b'> / 100</font>",
            ParagraphStyle("ScoreBox", parent=style_cell_normal, alignment=TA_CENTER),
        )
        banner_decision = Paragraph(
            f"<font size=7 color='#64748b'>MODEL DECISION</font><br/>"
            f"<font size=11 color='{color_p.hexval()}'><b>{pred_label.replace('_', ' ')}</b></font>",
            ParagraphStyle("DecBox", parent=style_cell_normal, alignment=TA_CENTER),
        )

        banner_table = Table(
            [[banner_text, banner_score, banner_decision]],
            colWidths=[295, 110, 110],
        )
        banner_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), color_bg),
            ("BOX", (0, 0), (-1, -1), 1, color_bd),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("LINEBEFORE", (1, 0), (1, -1), 0.5, color_bd),
            ("LINEBEFORE", (2, 0), (2, -1), 0.5, color_bd),
        ]))
        story.append(banner_table)
        story.append(Spacer(1, 10))

        # ── 3. Transaction Details & Customer Behavioral Profile (Side-by-Side) ─
        story.append(Paragraph("Transaction Overview & Account Baseline", style_section_heading))

        amount = float(transaction.get("transaction_amount", transaction.get("amount", 0.0)))
        time_since_last = float(transaction.get("time_since_last_txn_hrs", 0.0))
        dist_home = float(transaction.get("distance_from_home_km", 0.0))
        is_intl = "Yes (Flagged)" if transaction.get("is_international") else "No (Domestic)"
        is_night = "Yes (Off-hours)" if transaction.get("is_night_transaction") else "No (Daytime)"
        failed_attempts = int(transaction.get("failed_attempts", 0))
        pin_changed = "Yes (Elevated Risk)" if transaction.get("pin_changed_recently") else "No"

        txn_rows = [
            ("Transaction ID", txn_id),
            ("Customer ID", cust_id),
            ("Timestamp", str(transaction.get("timestamp", transaction.get("transaction_date", "")))),
            ("Amount", f"${amount:,.2f} USD"),
            ("Location", f"{transaction.get('city', '')}, {transaction.get('country', '')}"),
            ("Category", str(transaction.get("merchant_category", ""))),
            ("Payment Method", str(transaction.get("payment_method", ""))),
            ("Device Type", str(transaction.get("device_type", ""))),
            ("Distance from Home", f"{dist_home:,.1f} km"),
            ("Time Since Prior Txn", f"{time_since_last:,.2f} hrs"),
            ("Failed PIN Attempts", str(failed_attempts)),
            ("Recent PIN Change", pin_changed),
            ("Cross-Border / Intl", is_intl),
            ("Night Window", is_night),
        ]

        if customer_profile:
            avg_amt = float(customer_profile.get("avg_amount", 0.0))
            std_amt = float(customer_profile.get("std_amount", 0.0))
            med_amt = float(customer_profile.get("median_amount", 0.0))
            prof_rows = [
                ("Historical Total Txns", f"{int(customer_profile.get('total_transactions', 0)):,}"),
                ("Average Spend", f"${avg_amt:,.2f}"),
                ("Spend Std Deviation", f"${std_amt:,.2f}"),
                ("Median Spend", f"${med_amt:,.2f}"),
                ("Home City", str(customer_profile.get("common_city", ""))),
                ("Home Country", str(customer_profile.get("common_country", ""))),
                ("Primary Category", str(customer_profile.get("common_merchant_category", ""))),
                ("Primary Payment", str(customer_profile.get("common_payment_method", ""))),
                ("Primary Device", str(customer_profile.get("common_device_type", ""))),
                ("Avg Transaction Hour", f"{float(customer_profile.get('avg_hour', 12)):.1f}:00 hrs"),
                ("Txn Velocity", f"{float(customer_profile.get('transactions_per_day', 0)):.2f} / day"),
                ("Customer Age", f"{transaction.get('customer_age', 'N/A')} yrs"),
                ("Credit Score", str(transaction.get("credit_score", "N/A"))),
                ("Prior Confirmed Frauds", str(customer_profile.get("fraud_count", 0))),
            ]
        else:
            prof_rows = [
                ("Customer Profile", "No historical profile found"),
                ("Customer Age", f"{transaction.get('customer_age', 'N/A')} yrs"),
                ("Credit Score", str(transaction.get("credit_score", "N/A"))),
                ("Account Balance", f"${float(transaction.get('account_balance', 0.0)):,.2f}"),
                ("Account Age", f"{float(transaction.get('account_age_years', 0.0)):.1f} yrs"),
                ("Prior Txns", str(transaction.get("num_prev_transactions", "N/A"))),
                ("Monthly Frequency", str(transaction.get("transaction_freq_monthly", "N/A"))),
            ]

        # Construct paired 4-column table
        max_rows = max(len(txn_rows), len(prof_rows))
        combined_data = []
        for i in range(max_rows):
            k1, v1 = txn_rows[i] if i < len(txn_rows) else ("", "")
            k2, v2 = prof_rows[i] if i < len(prof_rows) else ("", "")
            combined_data.append([
                Paragraph(f"<b>{k1}</b>" if k1 else "", style_cell_normal),
                Paragraph(v1, style_cell_normal),
                Paragraph(f"<b>{k2}</b>" if k2 else "", style_cell_normal),
                Paragraph(v2, style_cell_normal),
            ])

        col_w = [115, 137, 125, 138]
        paired_table = Table(
            [[
                Paragraph("CURRENT TRANSACTION", style_table_header),
                Paragraph("EVALUATED VALUES", style_table_header),
                Paragraph("CUSTOMER PROFILE BASELINE", style_table_header),
                Paragraph("HISTORICAL NORMS", style_table_header),
            ]] + combined_data,
            colWidths=col_w,
        )
        paired_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BG_WHITE, BG_ROW_EVEN]),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
            ("LINEBEFORE", (2, 0), (2, -1), 1.0, BORDER_COLOR),
        ]))
        story.append(paired_table)
        story.append(Spacer(1, 10))

        # ── 4. Deep Learning Anomaly & Multi-Factor Explainability ───────────
        story.append(Paragraph("AI Model Risk Breakdown & Explainability", style_section_heading))

        # Summary Metrics Callout
        ml_summary_data = [
            [
                Paragraph("<b>Autoencoder Anomaly Score</b>", style_cell_bold),
                Paragraph(f"<b>{anomaly_score:.4f}</b> (0.00 – 1.00)", style_cell_normal),
                Paragraph("<b>Reconstruction MSE Error</b>", style_cell_bold),
                Paragraph(f"<b>{recon_err:.6f}</b> (Baseline Threshold: 0.5929)", style_cell_normal),
            ]
        ]
        ml_table = Table(ml_summary_data, colWidths=[135, 117, 135, 128])
        ml_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BLUE_LIGHT),
            ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(ml_table)
        story.append(Spacer(1, 6))

        # 10-Component Risk Factors Table
        if risk_factors:
            sorted_factors = sorted(
                risk_factors,
                key=lambda x: float(x.get("weighted_contribution", x.get("contribution", 0.0))),
                reverse=True,
            )
            rf_table_data = [[
                Paragraph("RISK COMPONENT", style_table_header),
                Paragraph("SCORE", style_table_header),
                Paragraph("WEIGHT", style_table_header),
                Paragraph("CONTRIB (pts)", style_table_header),
                Paragraph("AI EXPLANATION & CONTEXT", style_table_header),
            ]]
            for rf in sorted_factors:
                f_name = rf.get("factor_name", rf.get("name", "")).replace("_", " ").title()
                f_score = float(rf.get("factor_score", rf.get("score", 0.0)))
                f_weight = float(rf.get("factor_weight", rf.get("weight", 0.0)))
                f_contrib = float(rf.get("weighted_contribution", rf.get("contribution", 0.0)))
                f_expl = str(rf.get("explanation", rf.get("description", "")))

                # Highlight high contributing factors
                f_color = colors.HexColor("#dc2626") if f_contrib >= 10.0 else (
                    colors.HexColor("#ea580c") if f_contrib >= 5.0 else TEXT_DARK
                )

                rf_table_data.append([
                    Paragraph(f"<b>{f_name}</b>", style_cell_bold),
                    Paragraph(f"{f_score:.2f}", style_cell_normal),
                    Paragraph(f"{f_weight * 100:.0f}%", style_cell_normal),
                    Paragraph(f"<font color='{f_color.hexval()}'><b>+{f_contrib:.2f}</b></font>", style_cell_normal),
                    Paragraph(f_expl, style_cell_desc),
                ])

            rf_table = Table(
                rf_table_data,
                colWidths=[110, 45, 45, 65, 250],
            )
            rf_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BG_WHITE, BG_ROW_EVEN]),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(rf_table)

        # ── 5. Investigator Notes & Audit Trail Sign-off ─────────────────────
        story.append(Spacer(1, 10))
        signoff_data = [
            [
                Paragraph("<b>Audit & Compliance Sign-Off</b>", style_cell_bold),
                Paragraph("<b>Investigator Signature:</b> ___________________", style_cell_normal),
                Paragraph(f"<b>Verified Date:</b> {datetime.utcnow().strftime('%Y-%m-%d')}", style_cell_normal),
            ],
            [
                Paragraph(
                    "<font color='#64748b' size=7.5>This report is automatically synthesized by the SENTINEL Deep Autoencoder engine "
                    "with 10-factor weighted anomaly scoring. All data points conform to regulatory audit guidelines.</font>",
                    style_cell_normal,
                ),
                "",
                "",
            ],
        ]
        signoff_table = Table(signoff_data, colWidths=[215, 170, 130])
        signoff_table.setStyle(TableStyle([
            ("SPAN", (0, 1), (-1, 1)),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, -1), BG_ROW_EVEN),
            ("BOX", (0, 0), (-1, -1), 1, BORDER_LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(signoff_table)

        # Build document with running header/footer
        doc.build(story, canvasmaker=NumberedCanvas)
        return buffer.getvalue()
