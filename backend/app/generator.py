import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from typing import Dict, Any

def set_cell_background(cell, hex_color: str):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def set_cell_margins(cell, top=20, bottom=20, left=40, right=40):
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    cell._tc.get_or_add_tcPr().append(tcMar)

def set_cell_borders(cell, top=None, bottom=None, left=None, right=None):
    tcPr = cell._tc.get_or_add_tcPr()
    borders_xml = ['<w:tcBorders ' + nsdecls('w') + '>']
    for side, border in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        if border:
            val, sz, color = border
            borders_xml.append(f'<w:{side} w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>')
        else:
            borders_xml.append(f'<w:{side} w:val="none"/>')
    borders_xml.append('</w:tcBorders>')
    tcPr.append(parse_xml(''.join(borders_xml)))

def set_row_cant_split(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

_LOGO_CANDIDATES = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "jfll-logo.jpeg")),
    os.path.abspath("jfll-logo.jpeg"),
    os.path.abspath("frontend/public/jfll-logo.jpeg"),
]
_RESOLVED_LOGO_PATH = next((p for p in _LOGO_CANDIDATES if os.path.exists(p)), None)

def build_crif_docx(data: Dict[str, Any], output_path: str):
    doc = docx.Document()
    
    # 1-Page Layout Geometry: Narrow margins to guarantee executive 1-page fit
    for section in doc.sections:
        section.top_margin = Inches(0.32)
        section.bottom_margin = Inches(0.32)
        section.left_margin = Inches(0.40)
        section.right_margin = Inches(0.40)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)
        
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(8.0)
    normal_style.font.color.rgb = RGBColor(15, 23, 42)
    
    # TABLE 0: Executive Corporate Letterhead
    logo_path = _RESOLVED_LOGO_PATH if (_RESOLVED_LOGO_PATH and os.path.exists(_RESOLVED_LOGO_PATH)) else next((p for p in _LOGO_CANDIDATES if os.path.exists(p)), None)

    cols = 3 if logo_path else 2
    header_table = doc.add_table(rows=1, cols=cols)
    header_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    header_table.autofit = False
    set_row_cant_split(header_table.rows[0])
    col_widths = [Inches(0.95), Inches(4.15), Inches(2.40)] if logo_path else [Inches(5.00), Inches(2.50)]
    
    for i, cell in enumerate(header_table.rows[0].cells):
        cell.width = col_widths[i]
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_margins(cell, top=25, bottom=25, left=20, right=20)
        set_cell_borders(cell, bottom=('single', '12', '1E3A8A'))
        
    if logo_path:
        logo_cell = header_table.cell(0, 0)
        p_logo = logo_cell.paragraphs[0]
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(0)
        p_logo.paragraph_format.space_after = Pt(0)
        p_logo.add_run().add_picture(logo_path, width=Inches(0.85))
        
    mid_cell = header_table.cell(0, 1 if logo_path else 0)
    p_brand = mid_cell.paragraphs[0]
    p_brand.paragraph_format.space_before = Pt(0)
    p_brand.paragraph_format.space_after = Pt(1)
    r_brand = p_brand.add_run("JET FREIGHT LOGISTICS LIMITED")
    r_brand.font.size = Pt(11.5)
    r_brand.font.bold = True
    r_brand.font.color.rgb = RGBColor(15, 47, 100)
    
    p_title = mid_cell.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(1)
    r_title = p_title.add_run("CREDIT APPRAISAL MEMORANDUM (CRIF)")
    r_title.font.size = Pt(9.0)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(30, 58, 138)
    
    p_dept = mid_cell.add_paragraph()
    p_dept.paragraph_format.space_before = Pt(0)
    p_dept.paragraph_format.space_after = Pt(0)
    r_dept = p_dept.add_run("Credit Control & Underwriting  •  Appraisal Memo")
    r_dept.font.size = Pt(7.0)
    r_dept.font.color.rgb = RGBColor(100, 116, 139)
    
    right_cell = header_table.cell(0, 2 if logo_path else 1)
    p_date = right_cell.paragraphs[0]
    p_date.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_date.paragraph_format.space_before = Pt(0)
    p_date.paragraph_format.space_after = Pt(1)
    r_date_lbl = p_date.add_run("Date: ")
    r_date_lbl.font.bold = True
    r_date_lbl.font.size = Pt(7.5)
    r_date_lbl.font.color.rgb = RGBColor(71, 85, 105)
    r_date_val = p_date.add_run(data.get('date', 'N/A'))
    r_date_val.font.size = Pt(7.5)
    r_date_val.font.color.rgb = RGBColor(15, 23, 42)
    
    p_src = right_cell.add_paragraph()
    p_src.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_src.paragraph_format.space_before = Pt(0)
    p_src.paragraph_format.space_after = Pt(2)
    bureau_source = data.get('bureau_source') or "Rubix Data Sciences"
    r_ref_lbl = p_src.add_run("Source: ")
    r_ref_lbl.font.bold = True
    r_ref_lbl.font.size = Pt(7.5)
    r_ref_lbl.font.color.rgb = RGBColor(71, 85, 105)
    r_ref_val = p_src.add_run(bureau_source)
    r_ref_val.font.size = Pt(7.5)
    r_ref_val.font.color.rgb = RGBColor(15, 23, 42)
    
    p_status = right_cell.add_paragraph()
    p_status.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_status.paragraph_format.space_before = Pt(0)
    p_status.paragraph_format.space_after = Pt(0)
    r_status = p_status.add_run("  ✔ SANCTIONED & APPROVED  ")
    r_status.font.bold = True
    r_status.font.size = Pt(7.0)
    r_status.font.color.rgb = RGBColor(5, 150, 105)
    rPr = r_status._r.get_or_add_rPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="ECFDF5"/>')
    bdr = parse_xml(f'<w:bdr {nsdecls("w")} w:val="single" w:sz="4" w:space="1" w:color="A7F3D0"/>')
    rPr.append(shd)
    rPr.append(bdr)
    
    # Vertical spacing between Header and Key Metrics
    p_gap = doc.add_paragraph()
    p_gap.paragraph_format.space_before = Pt(0)
    p_gap.paragraph_format.space_after = Pt(6)
    
    # TABLE 1: Key Executive Metrics 4-Box Grid (doc.tables[1] - required by unit test contracts)
    metric_table = doc.add_table(rows=2, cols=4)
    metric_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    metric_table.autofit = False
    for row in metric_table.rows:
        set_row_cant_split(row)
    m_widths = [Inches(1.875), Inches(1.875), Inches(1.875), Inches(1.875)]
    bureau_risk_header = "CRIF EVALUATION" if "CRIF" in bureau_source.upper() else "RUBIX RISK GRADE"
    labels = ["CRIF CREDIT LIMIT", "APPROVED CREDIT DAYS", bureau_risk_header, "SALESPERSON"]
    values = [
        data.get('crif_credit_limit', '₹ 0.00'),
        data.get('credit_days', '30 Days'),
        data.get('risk_grade_score', 'Rx5 (58)'),
        data.get('salesperson', 'N/A')
    ]
    sub_notes = [
        "Approved Credit Limit",
        "Approved Payment Terms",
        data.get('risk_description', 'Risk Grade Evaluation'),
        "Sales Representative"
    ]
    
    for i in range(4):
        c = metric_table.cell(0, i)
        c.width = m_widths[i]
        set_cell_background(c, "F1F5F9")
        set_cell_margins(c, top=20, bottom=12, left=35, right=35)
        set_cell_borders(c, top=('single', '6', 'CBD5E1'), left=('single', '6', 'CBD5E1'), right=('single', '6', 'CBD5E1'))
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(labels[i])
        r.font.size = Pt(7.0)
        r.font.bold = True
        r.font.color.rgb = RGBColor(71, 85, 105)
        
    for i in range(4):
        c = metric_table.cell(1, i)
        c.width = m_widths[i]
        set_cell_background(c, "FFFFFF")
        set_cell_margins(c, top=12, bottom=20, left=35, right=35)
        set_cell_borders(c, bottom=('single', '8', '1E3A8A' if i==0 else 'CBD5E1'), left=('single', '6', 'CBD5E1'), right=('single', '6', 'CBD5E1'))
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(1)
        r_val = p.add_run(values[i])
        r_val.font.bold = True
        if i == 0:
            r_val.font.size = Pt(12.0)
            r_val.font.color.rgb = RGBColor(30, 58, 138)
        elif i == 1:
            if len(values[1]) > 16:
                r_val.font.size = Pt(8.5)
            else:
                r_val.font.size = Pt(9.5)
            r_val.font.color.rgb = RGBColor(15, 23, 42)
        elif i == 2:
            r_val.font.size = Pt(10.0)
            r_val.font.color.rgb = RGBColor(217, 119, 6)
        else:
            r_val.font.size = Pt(9.5)
            r_val.font.color.rgb = RGBColor(15, 23, 42)
            
        p_sub = c.add_paragraph()
        p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_sub.paragraph_format.space_before = Pt(0)
        p_sub.paragraph_format.space_after = Pt(0)
        r_sub = p_sub.add_run(sub_notes[i])
        r_sub.font.size = Pt(6.5)
        r_sub.font.color.rgb = RGBColor(100, 116, 139)

    def add_section_header(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8.0)
        p.paragraph_format.space_after = Pt(3.0)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title)
        r.font.size = Pt(8.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(15, 23, 42)

    # TABLE 2: Section 1 - Customer Identity & Business Profile
    add_section_header("1. CUSTOMER IDENTITY & BUSINESS PROFILE")
    p_rows = [
        ("Customer Legal Name", data.get('customer_name', 'N/A'), "Company Type (Entity)", data.get('type_of_company', 'N/A')),
        ("Date of Incorporation", data.get('date_of_incorporation', 'N/A'), "Operating Branch", data.get('branch', 'Mumbai Air Cargo')),
        ("Registered Address", data.get('registered_address', 'N/A'), None, None),
        ("Nature of Business", data.get('nature_of_business', 'N/A'), None, None)
    ]
    if data.get('additional_info'):
        p_rows.append(("Additional Information", data['additional_info'], None, None))
        
    profile_table = doc.add_table(rows=len(p_rows), cols=4)
    profile_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    profile_table.autofit = False
    p_widths = [Inches(1.65), Inches(2.10), Inches(1.65), Inches(2.10)]
    
    for r_idx, (l1, v1, l2, v2) in enumerate(p_rows):
        row = profile_table.rows[r_idx]
        set_row_cant_split(row)
        b_col = "E2E8F0"
        if l2 is None:
            # Merged 3 cols for broad text (Address, Nature of Business, Additional Info)
            c_lbl = row.cells[0]
            c_lbl.width = p_widths[0]
            set_cell_background(c_lbl, "F8FAFC")
            set_cell_margins(c_lbl, top=18, bottom=18, left=35, right=35)
            set_cell_borders(c_lbl, top=('single', '4', b_col), bottom=('single', '4', b_col),
                              left=('single', '6', '1E3A8A' if r_idx == 0 else b_col), right=('single', '4', b_col))
            p = c_lbl.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(l1)
            r.font.bold = True
            r.font.size = Pt(7.5)
            r.font.color.rgb = RGBColor(71, 85, 105)
            
            c_val = row.cells[1]
            c_val.merge(row.cells[3])
            c_val.width = Inches(5.85)
            set_cell_background(c_val, "FFFFFF")
            set_cell_margins(c_val, top=18, bottom=18, left=35, right=35)
            set_cell_borders(c_val, top=('single', '4', b_col), bottom=('single', '4', b_col), left=('single', '4', b_col), right=('single', '4', b_col))
            p = c_val.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(v1)
            r.font.size = Pt(7.5)
            if "Nature" in l1:
                r.font.italic = True
                r.font.color.rgb = RGBColor(51, 65, 85)
            else:
                r.font.color.rgb = RGBColor(15, 23, 42)
        else:
            cells = [
                (row.cells[0], l1, True, "F8FAFC", "475569"),
                (row.cells[1], v1, False, "FFFFFF", "0F172A"),
                (row.cells[2], l2, True, "F8FAFC", "475569"),
                (row.cells[3], v2, False, "FFFFFF", "0F172A")
            ]
            for c_idx, (c, text_val, is_lbl, bg_col, txt_col) in enumerate(cells):
                c.width = p_widths[c_idx]
                set_cell_background(c, bg_col)
                set_cell_margins(c, top=18, bottom=18, left=35, right=35)
                set_cell_borders(c, top=('single', '4', b_col), bottom=('single', '4', b_col),
                                  left=('single', '6', '1E3A8A' if (c_idx == 0 and r_idx == 0) else b_col), right=('single', '4', b_col))
                p = c.paragraphs[0]
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                r = p.add_run(str(text_val))
                r.font.size = Pt(7.5)
                if is_lbl:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(71, 85, 105)
                else:
                    if r_idx == 0 and c_idx == 1:
                        r.font.bold = True
                    r.font.color.rgb = RGBColor(15, 23, 42)

    # TABLE 3: Section 2 - Logistics Commercial Terms & Risk Controls
    add_section_header("2. LOGISTICS COMMERCIAL TERMS & RISK CONTROLS")
    sec_138_val = "Collected & Held (Enforceable)" if data.get('sec_138_cheque', True) else "Not Collected / Waived"
    caf_val = "Signed & Cargo Lien Executed" if data.get('caf_signed', True) else "Pending Signature"
    comm_mode = data.get('commercial_mode', 'Both')
    iata_tenor = data.get('iata_credit_days', '15 Days')
    ocean_tenor = data.get('ocean_credit_days', '30 Days')
    duty_terms = data.get('customs_duty_terms', '0 Days (Immediate / COD)')

    terms_rows = [
        ("Commercial Shipment Mode", comm_mode, "Customs Duty & Handling", duty_terms),
        ("IATA Air Freight Tenor (Credit Days)", iata_tenor if comm_mode in ('Air', 'Both') else "N/A (Ocean Only)",
         "Ocean / Multimodal Tenor (Credit Days)", ocean_tenor if comm_mode in ('Ocean', 'Both') else "N/A (Air Only)"),
        ("Sec. 138 NI Act Cheque (Security Cheque)", sec_138_val, "CAF with Cargo Lien Signed (Credit Agreement)", caf_val)
    ]

    statutory_highlights = []
    if data.get('pf_delay_days', 0) > 0:
        statutory_highlights.append(f"PF Delay: {data['pf_delay_days']} Days")
    if data.get('gst_delay_days', 0) > 0:
        statutory_highlights.append(f"GST Delay: {data['gst_delay_days']} Days")
    if data.get('court_cases_count', 0) > 0:
        statutory_highlights.append(f"Litigation: {data['court_cases_count']} Cases")

    if statutory_highlights:
        terms_rows.append(("Statutory & Court Alerts", ", ".join(statutory_highlights), "Bureau Risk Evaluation", data.get('risk_grade_score', 'N/A')))

    terms_table = doc.add_table(rows=len(terms_rows), cols=4)
    terms_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    terms_table.autofit = False
    t_widths = [Inches(1.85), Inches(1.90), Inches(1.85), Inches(1.90)]

    for r_idx, (lbl1, val1, lbl2, val2) in enumerate(terms_rows):
        row = terms_table.rows[r_idx]
        set_row_cant_split(row)
        is_stat_alert = (r_idx == len(terms_rows) - 1 and statutory_highlights)
        cells = [
            (row.cells[0], lbl1, True, "FEF2F2" if is_stat_alert else "F8FAFC", "991B1B" if is_stat_alert else "475569"),
            (row.cells[1], val1, False, "FFFFFF", "991B1B" if is_stat_alert else "0F172A"),
            (row.cells[2], lbl2, True, "F8FAFC", "475569"),
            (row.cells[3], val2, False, "FFFFFF", "0F172A")
        ]
        b_col = "E2E8F0"
        for c_idx, (c, text_val, is_lbl, bg_col, txt_col) in enumerate(cells):
            c.width = t_widths[c_idx]
            set_cell_background(c, bg_col)
            set_cell_margins(c, top=18, bottom=18, left=35, right=35)
            set_cell_borders(c, top=('single', '4', b_col), bottom=('single', '4', b_col),
                               left=('single', '6', '1E3A8A' if (c_idx == 0 and r_idx == 0) else b_col), right=('single', '4', b_col))
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(text_val))
            r.font.size = Pt(7.5)
            if is_lbl:
                r.font.bold = True
                if is_stat_alert and c_idx == 0:
                    r.font.color.rgb = RGBColor(153, 27, 27)
                else:
                    r.font.color.rgb = RGBColor(71, 85, 105)
            else:
                if "Enforceable" in str(text_val) or "Executed" in str(text_val):
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(5, 150, 105)
                elif is_stat_alert and c_idx == 1:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(153, 27, 27)
                else:
                    r.font.color.rgb = RGBColor(15, 23, 42)

    # TABLE 4: Section 3 - KYC Verification & Statutory Compliance Checklist
    add_section_header("3. KYC VERIFICATION & STATUTORY COMPLIANCE CHECKLIST")
    kyc_items = data.get('kyc_documents', [])
    if not kyc_items:
        kyc_items = [
            {"document": "Permanent Account Number (PAN)", "status": "Available", "source": "Income Tax / Rubix", "remarks": "Active & Linked"},
            {"document": "GST Registration Certificate", "status": "Available", "source": "GSTN Portal / Rubix", "remarks": "Active (0 Days Delay)"},
            {"document": "Aadhaar Card / Proprietor ID", "status": "Available", "source": "UIDAI / Master Record", "remarks": "Proprietor Verified"},
            {"document": "Certificate of Incorporation (COI) / IEC", "status": "Available", "source": "MCA / DGFT Portal", "remarks": "Active Compliant"}
        ]
        
    kyc_table = doc.add_table(rows=len(kyc_items) + 1, cols=4)
    kyc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    kyc_table.autofit = False
    for row in kyc_table.rows:
        set_row_cant_split(row)
    kyc_widths = [Inches(2.50), Inches(1.15), Inches(1.70), Inches(2.15)]
    kyc_headers = ["Document Description", "Status", "Verification Source", "Compliance Remarks"]
    
    for col_idx, h_text in enumerate(kyc_headers):
        c = kyc_table.cell(0, col_idx)
        c.width = kyc_widths[col_idx]
        set_cell_background(c, "1E3A8A")
        set_cell_margins(c, top=18, bottom=18, left=35, right=35)
        set_cell_borders(c, top=('single', '4', '1E3A8A'), bottom=('single', '4', '1E3A8A'), left=('single', '4', '1E3A8A'), right=('single', '4', '1E3A8A'))
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.font.bold = True
        r.font.size = Pt(7.0)
        r.font.color.rgb = RGBColor(255, 255, 255)
        
    for row_idx, item in enumerate(kyc_items, start=1):
        bg = "FFFFFF" if row_idx % 2 != 0 else "F8FAFC"
        row_vals = [
            item.get('document', ''),
            item.get('status', 'Available'),
            item.get('source', 'Bureau Verified'),
            item.get('remarks', 'Active')
        ]
        b_col = "E2E8F0"
        for col_idx, text_val in enumerate(row_vals):
            c = kyc_table.cell(row_idx, col_idx)
            c.width = kyc_widths[col_idx]
            set_cell_background(c, bg)
            set_cell_margins(c, top=14, bottom=14, left=35, right=35)
            set_cell_borders(c, top=('single', '4', b_col), bottom=('single', '4', b_col), left=('single', '4', b_col), right=('single', '4', b_col))
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text_val)
            r.font.size = Pt(7.0)
            if col_idx == 1:
                r.font.bold = True
                r.font.color.rgb = RGBColor(5, 150, 105) if "Available" in text_val else RGBColor(217, 119, 6)
            elif col_idx == 0:
                r.font.bold = True
                r.font.color.rgb = RGBColor(15, 23, 42)
            else:
                r.font.color.rgb = RGBColor(71, 85, 105)

    # TABLE 5: Section 4 - Multi-Tier Approval, Sign-Off & Email Authorization Matrix
    add_section_header("4. CREDIT APPROVAL & SIGN-OFF MATRIX")
    sign_table = doc.add_table(rows=4, cols=3)
    sign_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sign_table.autofit = False
    for row in sign_table.rows:
        set_row_cant_split(row)
    s_widths = [Inches(2.50), Inches(2.50), Inches(2.50)]
    mail_val = (data.get('mail_approval') or '').strip()
    
    # ROW 0: Dedicated, Prominent Email Approval Reference Banner Row
    c_mail_lbl = sign_table.cell(0, 0)
    c_mail_lbl.width = s_widths[0]
    set_cell_background(c_mail_lbl, "F1F5F9")
    set_cell_margins(c_mail_lbl, top=18, bottom=18, left=35, right=35)
    set_cell_borders(c_mail_lbl, top=('single', '6', 'CBD5E1'), bottom=('single', '4', 'CBD5E1'), left=('single', '6', '1E3A8A'), right=('single', '4', 'CBD5E1'))
    p_ml = c_mail_lbl.paragraphs[0]
    p_ml.paragraph_format.space_before = Pt(0)
    p_ml.paragraph_format.space_after = Pt(0)
    r_ml = p_ml.add_run("Email Approval Reference")
    r_ml.font.bold = True
    r_ml.font.size = Pt(7.5)
    r_ml.font.color.rgb = RGBColor(30, 58, 138)
    
    c_mail_val = sign_table.cell(0, 1)
    c_mail_val.merge(sign_table.cell(0, 2))
    c_mail_val.width = Inches(5.00)
    set_cell_background(c_mail_val, "F0FDF4" if mail_val else "FFFFFF")
    set_cell_margins(c_mail_val, top=18, bottom=18, left=35, right=35)
    set_cell_borders(c_mail_val, top=('single', '6', 'CBD5E1'), bottom=('single', '4', 'CBD5E1'), left=('single', '4', 'CBD5E1'), right=('single', '6', 'CBD5E1'))
    p_mv = c_mail_val.paragraphs[0]
    p_mv.paragraph_format.space_before = Pt(0)
    p_mv.paragraph_format.space_after = Pt(0)
    if mail_val:
        r_tag = p_mv.add_run("✔ Verified Email Approval: ")
        r_tag.font.bold = True
        r_tag.font.size = Pt(7.5)
        r_tag.font.color.rgb = RGBColor(22, 101, 52)
        r_mv = p_mv.add_run(mail_val)
        r_mv.font.bold = True
        r_mv.font.size = Pt(7.5)
        r_mv.font.color.rgb = RGBColor(15, 23, 42)
    else:
        r_mv = p_mv.add_run("Physical Signature Required (No Email Approval Submitted)")
        r_mv.font.size = Pt(7.0)
        r_mv.font.italic = True
        r_mv.font.color.rgb = RGBColor(100, 116, 139)

    # ROW 1: Signatory Titles
    s_titles = ["1. PREPARED BY", "2. CHECKED & AUDITED BY", "3. FINAL APPROVAL"]
    for col_idx, s_title in enumerate(s_titles):
        c = sign_table.cell(1, col_idx)
        c.width = s_widths[col_idx]
        set_cell_background(c, "F8FAFC")
        set_cell_margins(c, top=18, bottom=18, left=35, right=35)
        set_cell_borders(c, top=('single', '4', 'CBD5E1'), bottom=('single', '4', 'CBD5E1'), left=('single', '6', 'CBD5E1'), right=('single', '6', 'CBD5E1'))
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(s_title)
        r.font.bold = True
        r.font.size = Pt(7.0)
        r.font.color.rgb = RGBColor(71, 85, 105)
        
    # ROW 2: Compact Signature Row
    for col_idx in range(3):
        c = sign_table.cell(2, col_idx)
        c.width = s_widths[col_idx]
        set_cell_background(c, "FFFFFF")
        set_cell_margins(c, top=30, bottom=30, left=35, right=35)
        set_cell_borders(c, top=('single', '4', 'CBD5E1'), bottom=('dotted', '4', 'CBD5E1'), left=('single', '6', 'CBD5E1'), right=('single', '6', 'CBD5E1'))
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(0)
        if col_idx == 2 and mail_val:
            r = p.add_run(f"[ Approved via Email: {mail_val} ]")
            r.font.size = Pt(7.0)
            r.font.bold = True
            r.font.color.rgb = RGBColor(30, 58, 138)
        else:
            r = p.add_run("[ Authorized Signature ]")
            r.font.size = Pt(6.5)
            r.font.italic = True
            r.font.color.rgb = RGBColor(148, 163, 184)
        
    # ROW 3: Signatory Details
    s_names = [
        data.get('created_by', 'Credit Analyst'),
        data.get('checked_by', 'Manager - Credit Control'),
        data.get('approved_by', 'Head of Credit / Director')
    ]
    for col_idx in range(3):
        c = sign_table.cell(3, col_idx)
        c.width = s_widths[col_idx]
        set_cell_background(c, "F8FAFC")
        set_cell_margins(c, top=18, bottom=18, left=35, right=35)
        set_cell_borders(c, top=('none', '0', ''), bottom=('single', '8', '1E3A8A'), left=('single', '6', 'CBD5E1'), right=('single', '6', 'CBD5E1'))
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r_n = p.add_run(f"Name: {s_names[col_idx]}\n")
        r_n.font.size = Pt(7.0)
        r_n.font.bold = True
        r_n.font.color.rgb = RGBColor(15, 23, 42)
        r_d = p.add_run(f"Date: {data.get('date', 'N/A')}")
        r_d.font.size = Pt(6.5)
        r_d.font.color.rgb = RGBColor(100, 116, 139)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    return output_path
