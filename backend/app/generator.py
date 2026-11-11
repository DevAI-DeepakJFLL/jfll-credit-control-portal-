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

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
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

_LOGO_CANDIDATES = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "jfll-logo.jpeg")),
    os.path.abspath("jfll-logo.jpeg"),
    os.path.abspath("frontend/public/jfll-logo.jpeg"),
]
_RESOLVED_LOGO_PATH = next((p for p in _LOGO_CANDIDATES if os.path.exists(p)), None)

def build_crif_docx(data: Dict[str, Any], output_path: str):
    doc = docx.Document()
    
    # Page setup
    for section in doc.sections:
        section.top_margin = Inches(0.65)
        section.bottom_margin = Inches(0.65)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(9.5)
    normal_style.font.color.rgb = RGBColor(30, 41, 59)
    
    # 1. Executive Corporate Letterhead & Document Title Header
    logo_path = _RESOLVED_LOGO_PATH if (_RESOLVED_LOGO_PATH and os.path.exists(_RESOLVED_LOGO_PATH)) else next((p for p in _LOGO_CANDIDATES if os.path.exists(p)), None)

    cols = 3 if logo_path else 2
    header_table = doc.add_table(rows=2, cols=cols)
    header_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    header_table.autofit = False
    col_widths = [Inches(0.95), Inches(3.75), Inches(2.30)] if logo_path else [Inches(4.65), Inches(2.35)]
    
    for i, cell in enumerate(header_table.rows[0].cells):
        cell.width = col_widths[i]
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_margins(cell, top=60, bottom=60, left=40, right=40)
        set_cell_borders(cell, bottom=('single', '14', '1E3A8A'))
        
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
    r_brand.font.size = Pt(13.5)
    r_brand.font.bold = True
    r_brand.font.color.rgb = RGBColor(15, 47, 100)
    
    p_dept = mid_cell.add_paragraph()
    p_dept.paragraph_format.space_before = Pt(0)
    p_dept.paragraph_format.space_after = Pt(2)
    r_dept = p_dept.add_run("Credit Risk & Underwriting Division  |  Commercial Appraisal")
    r_dept.font.size = Pt(8.5)
    r_dept.font.bold = True
    r_dept.font.color.rgb = RGBColor(71, 85, 105)
    
    p_cin = mid_cell.add_paragraph()
    p_cin.paragraph_format.space_before = Pt(0)
    p_cin.paragraph_format.space_after = Pt(0)
    r_cin = p_cin.add_run("An NSE Listed Company  •  ISO 9001:2015 Certified  •  CIN: L63090MH2006PLC161114")
    r_cin.font.size = Pt(7)
    r_cin.font.color.rgb = RGBColor(148, 163, 184)
    
    right_cell = header_table.cell(0, 2 if logo_path else 1)
    p_date = right_cell.paragraphs[0]
    p_date.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_date.paragraph_format.space_before = Pt(0)
    p_date.paragraph_format.space_after = Pt(1)
    r_date_lbl = p_date.add_run("Date: ")
    r_date_lbl.font.bold = True
    r_date_lbl.font.size = Pt(8.5)
    r_date_lbl.font.color.rgb = RGBColor(71, 85, 105)
    r_date_val = p_date.add_run(data.get('date', 'N/A'))
    r_date_val.font.size = Pt(8.5)
    r_date_val.font.color.rgb = RGBColor(15, 23, 42)
    
    p_src = right_cell.add_paragraph()
    p_src.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_src.paragraph_format.space_before = Pt(0)
    p_src.paragraph_format.space_after = Pt(3)
    bureau_source = data.get('bureau_source') or "Rubix Data Sciences"
    r_ref_lbl = p_src.add_run("Source: ")
    r_ref_lbl.font.bold = True
    r_ref_lbl.font.size = Pt(8.5)
    r_ref_lbl.font.color.rgb = RGBColor(71, 85, 105)
    r_ref_val = p_src.add_run(bureau_source)
    r_ref_val.font.size = Pt(8.5)
    r_ref_val.font.color.rgb = RGBColor(15, 23, 42)
    
    p_status = right_cell.add_paragraph()
    p_status.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_status.paragraph_format.space_before = Pt(1)
    p_status.paragraph_format.space_after = Pt(0)
    r_status = p_status.add_run("  ✔ SANCTIONED & APPROVED  ")
    r_status.font.bold = True
    r_status.font.size = Pt(8)
    r_status.font.color.rgb = RGBColor(5, 150, 105)
    rPr = r_status._r.get_or_add_rPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="ECFDF5"/>')
    bdr = parse_xml(f'<w:bdr {nsdecls("w")} w:val="single" w:sz="4" w:space="2" w:color="A7F3D0"/>')
    rPr.append(shd)
    rPr.append(bdr)
    
    # Row 1: Merged Prominent Document Title Band
    title_cell = header_table.cell(1, 0)
    title_cell.merge(header_table.cell(1, cols - 1))
    title_cell.width = Inches(7.0)
    set_cell_background(title_cell, "F8FAFC")
    set_cell_margins(title_cell, top=65, bottom=65, left=100, right=100)
    set_cell_borders(title_cell,
        top=('single', '4', 'E2E8F0'),
        bottom=('single', '8', 'CBD5E1'),
        left=('single', '18', '1E3A8A'),
        right=('single', '4', 'E2E8F0')
    )
    
    p_title = title_cell.paragraphs[0]
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(1)
    r_title = p_title.add_run("CREDIT APPRAISAL MEMORANDUM (CRIF / CAM)")
    r_title.font.size = Pt(12)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(15, 23, 42)
    
    p_subtitle = title_cell.add_paragraph()
    p_subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_subtitle.paragraph_format.space_before = Pt(0)
    p_subtitle.paragraph_format.space_after = Pt(0)
    r_sub = p_subtitle.add_run("Underwriting Evaluation, Credit Limit Sanction & Statutory Risk Assessment")
    r_sub.font.size = Pt(7.5)
    r_sub.font.color.rgb = RGBColor(100, 116, 139)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    
    # 2. Key Metrics 4-Box Grid
    metric_table = doc.add_table(rows=2, cols=4)
    metric_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    metric_table.autofit = False
    m_widths = [Inches(1.85), Inches(1.65), Inches(1.85), Inches(1.65)]
    bureau_risk_header = "CRIF EVALUATION" if "CRIF" in bureau_source.upper() else "RUBIX RISK GRADE"
    labels = ["CRIF CREDIT LIMIT", "APPROVED CREDIT DAYS", bureau_risk_header, "SALESPERSON"]
    values = [
        data.get('crif_credit_limit', '₹ 0.00'),
        data.get('credit_days', '30 Days'),
        data.get('risk_grade_score', 'Rx5 (58)'),
        data.get('salesperson', 'N/A')
    ]
    sub_notes = [
        "Sanctioned Exposure",
        "Terms: CSR Standard",
        data.get('risk_description', 'Counterparty Risk'),
        "Account Executive"
    ]
    
    for i in range(4):
        c = metric_table.cell(0, i)
        c.width = m_widths[i]
        set_cell_background(c, "F1F5F9")
        set_cell_margins(c, top=60, bottom=30, left=80, right=80)
        set_cell_borders(c, top=('single', '6', 'CBD5E1'), left=('single', '6', 'CBD5E1'), right=('single', '6', 'CBD5E1'))
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(labels[i])
        r.font.size = Pt(7.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(71, 85, 105)
        
    for i in range(4):
        c = metric_table.cell(1, i)
        c.width = m_widths[i]
        set_cell_background(c, "FFFFFF")
        set_cell_margins(c, top=40, bottom=60, left=80, right=80)
        set_cell_borders(c, bottom=('single', '8', '1E3A8A' if i==0 else 'CBD5E1'), left=('single', '6', 'CBD5E1'), right=('single', '6', 'CBD5E1'))
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        r_val = p.add_run(values[i])
        r_val.font.bold = True
        if i == 0:
            r_val.font.size = Pt(13)
            r_val.font.color.rgb = RGBColor(30, 58, 138)
        elif i == 1:
            if len(values[1]) > 16:
                r_val.font.size = Pt(8.5)
            else:
                r_val.font.size = Pt(10.5)
            r_val.font.color.rgb = RGBColor(15, 23, 42)
        elif i == 2:
            r_val.font.size = Pt(11)
            r_val.font.color.rgb = RGBColor(217, 119, 6)
        else:
            r_val.font.size = Pt(10.5)
            r_val.font.color.rgb = RGBColor(15, 23, 42)
            
        p_sub = c.add_paragraph()
        p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_sub.paragraph_format.space_before = Pt(0)
        p_sub.paragraph_format.space_after = Pt(0)
        r_sub = p_sub.add_run(sub_notes[i])
        r_sub.font.size = Pt(7)
        r_sub.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def add_section_header(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title)
        r.font.size = Pt(10.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(15, 23, 42)

    # 3. Customer Profile
    add_section_header("1. CUSTOMER IDENTITY & BUSINESS PROFILE")
    profile_rows = [
        ("Customer Legal Name", data.get('customer_name', 'N/A')),
        ("Type of Company", data.get('type_of_company', 'N/A')),
        ("Date of Incorporation", data.get('date_of_incorporation', 'N/A')),
        ("Registered / Business Address", data.get('registered_address', 'N/A'))
    ]
    if data.get('additional_info'):
        profile_rows.append(("Additional Information", data['additional_info']))

    profile_table = doc.add_table(rows=len(profile_rows), cols=2)
    profile_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    profile_table.autofit = False
    p_widths = [Inches(2.0), Inches(5.0)]
    
    for row_idx, (lbl, val) in enumerate(profile_rows):
        c_lbl = profile_table.cell(row_idx, 0)
        c_val = profile_table.cell(row_idx, 1)
        c_lbl.width = p_widths[0]
        c_val.width = p_widths[1]
        set_cell_background(c_lbl, "F8FAFC")
        set_cell_background(c_val, "FFFFFF")
        set_cell_margins(c_lbl, top=45, bottom=45, left=80, right=80)
        set_cell_margins(c_val, top=45, bottom=45, left=80, right=80)
        b_color = "E2E8F0"
        set_cell_borders(c_lbl, top=('single', '4', b_color), bottom=('single', '4', b_color), left=('single', '6', '1E3A8A' if row_idx==0 else b_color), right=('single', '4', b_color))
        set_cell_borders(c_val, top=('single', '4', b_color), bottom=('single', '4', b_color), left=('single', '4', b_color), right=('single', '4', b_color))
        
        p_l = c_lbl.paragraphs[0]
        p_l.paragraph_format.space_before = Pt(0)
        p_l.paragraph_format.space_after = Pt(0)
        r_l = p_l.add_run(lbl)
        r_l.font.bold = True
        r_l.font.size = Pt(8.5)
        r_l.font.color.rgb = RGBColor(71, 85, 105)
        
        p_v = c_val.paragraphs[0]
        p_v.paragraph_format.space_before = Pt(0)
        p_v.paragraph_format.space_after = Pt(0)
        r_v = p_v.add_run(val)
        if row_idx == 0:
            r_v.font.bold = True
        r_v.font.size = Pt(8.5)

    # 4. Nature of Business
    add_section_header("2. NATURE OF BUSINESS & OPERATIONS")
    nob_table = doc.add_table(rows=1, cols=1)
    nob_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    nob_cell = nob_table.cell(0, 0)
    nob_cell.width = Inches(7.0)
    set_cell_background(nob_cell, "F8FAFC")
    set_cell_margins(nob_cell, top=70, bottom=70, left=110, right=110)
    set_cell_borders(nob_cell, top=('single', '4', 'E2E8F0'), bottom=('single', '4', 'E2E8F0'), left=('single', '14', '1E3A8A'), right=('single', '4', 'E2E8F0'))
    p_nob = nob_cell.paragraphs[0]
    p_nob.paragraph_format.space_before = Pt(0)
    p_nob.paragraph_format.space_after = Pt(0)
    r_nob = p_nob.add_run(data.get('nature_of_business', 'N/A'))
    r_nob.font.size = Pt(8.5)
    r_nob.font.color.rgb = RGBColor(30, 41, 59)
    r_nob.font.italic = True

    # 5. KYC Checklist
    add_section_header("3. KYC VERIFICATION & STATUTORY COMPLIANCE CHECKLIST")
    kyc_items = data.get('kyc_documents', [])
    if not kyc_items:
        kyc_items = [
            {"document": "Permanent Account Number (PAN)", "status": "Available", "source": "Income Tax / Rubix", "remarks": "Active & Linked"},
            {"document": "GST Registration Certificate", "status": "Available", "source": "GSTN Portal / Rubix", "remarks": "Active (0 Days Delay)"},
            {"document": "Tax Deduction Account (TAN)", "status": "Available", "source": "Statutory Records", "remarks": "Verified"},
            {"document": "Certificate of Incorporation (COI)", "status": "Available", "source": "MCA Master Data", "remarks": "Active Compliant"}
        ]
        
    kyc_table = doc.add_table(rows=len(kyc_items) + 1, cols=4)
    kyc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    kyc_table.autofit = False
    kyc_widths = [Inches(2.2), Inches(1.3), Inches(1.5), Inches(2.0)]
    kyc_headers = ["Document Description", "Status", "Verification Source", "Compliance Remarks"]
    
    for col_idx, h_text in enumerate(kyc_headers):
        c = kyc_table.cell(0, col_idx)
        c.width = kyc_widths[col_idx]
        set_cell_background(c, "1E3A8A")
        set_cell_margins(c, top=50, bottom=50, left=60, right=60)
        set_cell_borders(c, top=('single', '4', '1E3A8A'), bottom=('single', '4', '1E3A8A'), left=('single', '4', '1E3A8A'), right=('single', '4', '1E3A8A'))
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h_text)
        r.font.bold = True
        r.font.size = Pt(8.0)
        r.font.color.rgb = RGBColor(255, 255, 255)
        
    for row_idx, item in enumerate(kyc_items, start=1):
        bg = "FFFFFF" if row_idx % 2 != 0 else "F8FAFC"
        row_vals = [
            item.get('document', ''),
            item.get('status', 'Available'),
            item.get('source', 'Bureau Verified'),
            item.get('remarks', 'Active')
        ]
        for col_idx, text_val in enumerate(row_vals):
            c = kyc_table.cell(row_idx, col_idx)
            c.width = kyc_widths[col_idx]
            set_cell_background(c, bg)
            set_cell_margins(c, top=40, bottom=40, left=60, right=60)
            set_cell_borders(c, top=('single', '4', 'E2E8F0'), bottom=('single', '4', 'E2E8F0'), left=('single', '4', 'E2E8F0'), right=('single', '4', 'E2E8F0'))
            p = c.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text_val)
            r.font.size = Pt(8.0)
            if col_idx == 1:
                r.font.bold = True
                r.font.color.rgb = RGBColor(5, 150, 105)
            else:
                r.font.color.rgb = RGBColor(51, 65, 85)

    # 6. Multi-Tier Authorization
    add_section_header("4. MULTI-TIER CREDIT APPROVAL & SIGN-OFF")
    sign_table = doc.add_table(rows=3, cols=3)
    sign_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sign_table.autofit = False
    s_widths = [Inches(2.33), Inches(2.33), Inches(2.34)]
    s_titles = ["CREATED / REVIEWED BY", "CHECKED & AUDITED BY", "FINAL APPROVAL BY"]
    s_names = [
        data.get('created_by', 'Credit Analyst'),
        data.get('checked_by', 'Manager - Credit Control'),
        data.get('approved_by', 'Head of Credit / Director')
    ]
    
    for col_idx, s_title in enumerate(s_titles):
        c = sign_table.cell(0, col_idx)
        c.width = s_widths[col_idx]
        set_cell_background(c, "F1F5F9")
        set_cell_margins(c, top=45, bottom=45, left=60, right=60)
        set_cell_borders(c, top=('single', '6', 'CBD5E1'), bottom=('single', '6', 'CBD5E1'), left=('single', '6', 'CBD5E1'), right=('single', '6', 'CBD5E1'))
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(s_title)
        r.font.bold = True
        r.font.size = Pt(7.5)
        r.font.color.rgb = RGBColor(71, 85, 105)
        
    for col_idx in range(3):
        c = sign_table.cell(1, col_idx)
        c.width = s_widths[col_idx]
        set_cell_background(c, "FFFFFF")
        set_cell_margins(c, top=120, bottom=120, left=60, right=60)
        set_cell_borders(c, top=('single', '4', 'CBD5E1'), bottom=('dotted', '4', 'CBD5E1'), left=('single', '6', 'CBD5E1'), right=('single', '6', 'CBD5E1'))
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(0)
        if col_idx == 2 and data.get('mail_approval'):
            r = p.add_run(f"[ Approved via Email: {data['mail_approval']} ]")
            r.font.size = Pt(7.0)
            r.font.italic = True
            r.font.color.rgb = RGBColor(71, 85, 105)
        else:
            r = p.add_run("[ Authorized Signature ]")
            r.font.size = Pt(7.0)
            r.font.italic = True
            r.font.color.rgb = RGBColor(203, 213, 225)
        
    for col_idx in range(3):
        c = sign_table.cell(2, col_idx)
        c.width = s_widths[col_idx]
        set_cell_background(c, "F8FAFC")
        set_cell_margins(c, top=45, bottom=45, left=60, right=60)
        set_cell_borders(c, top=('none', '0', ''), bottom=('single', '8', '1E3A8A'), left=('single', '6', 'CBD5E1'), right=('single', '6', 'CBD5E1'))
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r_n = p.add_run(f"Name: {s_names[col_idx]}\n")
        r_n.font.size = Pt(7.5)
        r_n.font.bold = True
        r_n.font.color.rgb = RGBColor(15, 23, 42)
        r_d = p.add_run(f"Date: {data.get('date', 'N/A')}")
        r_d.font.size = Pt(7.0)
        r_d.font.color.rgb = RGBColor(100, 116, 139)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    return output_path
