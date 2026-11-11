import os
import sys
import time
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock
import docx

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.parser import (
    parse_rubix_pdf,
    parse_crif_bir_pdf,
    parse_crif_birl_pdf,
    detect_bureau_format,
    extract_bureau_pdf,
    _normalize_date,
    _format_inr
)
from backend.app.models import RubixExtractedData, GenerateDocxRequest
from backend.app.generator import build_crif_docx
from backend.app.database import init_db, save_appraisal, get_all_appraisals, get_db
from backend.app.main import app, prune_storage_files, UPLOADS_DIR, MEMOS_DIR
from fastapi.testclient import TestClient

class TestCreditControlPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.rubix_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'fixtures', 'rubix_samples'
        )
        cls.crif_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'fixtures', 'crif_samples'
        )

    def test_lade_exports_extraction(self):
        pdf_path = os.path.join(self.rubix_dir, 'LADE EXPORTS (2).pdf')
        data = parse_rubix_pdf(pdf_path)
        self.assertEqual(data['customer_name'], 'LADE EXPORTS')
        self.assertEqual(data['type_of_company'], 'Proprietorship')
        self.assertEqual(data['crif_credit_limit'], '₹ 3,57,000')
        self.assertEqual(data['recommended_credit_days'], 21)
        self.assertEqual(data['risk_grade'], 'Rx5')
        self.assertTrue('engineering goods' in data['nature_of_business'].lower())

    def test_pure_weave_extraction(self):
        pdf_path = os.path.join(self.rubix_dir, 'PURE WEAVE FABRICS-1.pdf')
        data = parse_rubix_pdf(pdf_path)
        self.assertEqual(data['customer_name'], 'PURE WEAVE FABRICS')
        self.assertEqual(data['type_of_company'], 'Proprietorship')
        self.assertEqual(data['crif_credit_limit'], '₹ 3,88,000')
        self.assertEqual(data['recommended_credit_days'], 21)
        self.assertTrue('garments' in data['nature_of_business'].lower())

    def test_sepio_products_extraction(self):
        pdf_path = os.path.join(self.rubix_dir, 'SEPIO PRODUCTS PRIVATE LIMITED-1.pdf')
        data = parse_rubix_pdf(pdf_path)
        self.assertEqual(data['customer_name'], 'SEPIO PRODUCTS PRIVATE LIMITED')
        self.assertEqual(data['type_of_company'], 'PRIVATE LIMITED')
        self.assertEqual(data['crif_credit_limit'], '₹ 14,16,000')
        self.assertEqual(data['recommended_credit_days'], 24)
        self.assertEqual(data['pf_delay_days'], 114) # Caught statutory delay

    def test_primex_industries_bir_extraction(self):
        pdf_path = os.path.join(self.crif_dir, 'PRIMEX INDUSTRIES_BIR_15-Oct-2026.pdf')
        data = parse_crif_bir_pdf(pdf_path)
        self.assertEqual(data['customer_name'], 'PRIMEX INDUSTRIES')
        self.assertEqual(data['type_of_company'], 'Partnership')
        self.assertEqual(data['date_of_incorporation'], '2016')
        self.assertEqual(data['registered_address'], '5Th Floor, 503, Neo Corporate Plaza, Ramchandra Lane, Malad West, Mumbai, Mumbai Suburban, Maharashtra, 400064')
        self.assertEqual(data['nature_of_business'], 'Primex Industries is a partnership firm, engaged as trader: wholesaler/distributor for plastics polymers products')
        self.assertEqual(data['bureau_source'], 'CRIF Solutions (BIR)')
        self.assertEqual(data['risk_score'], 56)
        self.assertEqual(data['risk_grade'], 'Normal')
        self.assertEqual(data['risk_description'], 'Score: 56/99 (Normal Index)')
        self.assertEqual(data['crif_credit_limit'], '₹ 0.00')
        self.assertEqual(data['recommended_credit_days'], 30)
        self.assertEqual(data['gst_delay_days'], 0)
        self.assertEqual(data['pf_delay_days'], 0)
        self.assertEqual(data['court_cases_count'], 0)
        self.assertTrue(any(d['document'] == 'Certificate of Incorporation / Deed' for d in data['kyc_documents']))

    def test_yh_cargo_birl_extraction(self):
        pdf_path = os.path.join(self.crif_dir, 'Y & H CARGO PRIVATE LIMITED-BIRL-06-Nov-2026.pdf')
        data = parse_crif_birl_pdf(pdf_path)
        self.assertEqual(data['customer_name'], 'Y & H CARGO PRIVATE LIMITED')
        self.assertEqual(data['type_of_company'], 'PRIVATE LIMITED')
        self.assertEqual(data['date_of_incorporation'], '18-01-2011')
        self.assertEqual(data['registered_address'], '1/2, Block-1, 3Rd Floor, Landmark, Whs, Kirti Nagar Industrial Area, New Delhi - 110015, Delhi, India')
        self.assertTrue('international logistics service provider' in data['nature_of_business'])
        self.assertEqual(data['bureau_source'], 'CRIF Solutions (BIRL)')
        self.assertEqual(data['risk_score'], 80)
        self.assertEqual(data['risk_grade'], 'Rating 4/5')
        self.assertEqual(data['risk_description'], 'Rating 4/5, Low Risk (Business trend: activity increase)')
        self.assertEqual(data['crif_credit_limit'], '₹ 35,00,000')
        self.assertEqual(data['recommended_credit_days'], 30)
        self.assertEqual(data['court_cases_count'], 2)
        self.assertEqual(data['pf_delay_days'], 0)
        self.assertTrue(any(d['document'] == 'Certificate of Incorporation (COI)' for d in data['kyc_documents']))

    def test_detect_bureau_format_and_extract_dispatch(self):
        rubix_pdf = os.path.join(self.rubix_dir, 'LADE EXPORTS (2).pdf')
        bir_pdf = os.path.join(self.crif_dir, 'PRIMEX INDUSTRIES_BIR_15-Oct-2026.pdf')
        birl_pdf = os.path.join(self.crif_dir, 'Y & H CARGO PRIVATE LIMITED-BIRL-06-Nov-2026.pdf')

        self.assertEqual(detect_bureau_format(rubix_pdf), 'RUBIX')
        self.assertEqual(detect_bureau_format(bir_pdf), 'CRIF_BIR')
        self.assertEqual(detect_bureau_format(birl_pdf), 'CRIF_BIRL')

        data_rubix = extract_bureau_pdf(rubix_pdf)
        self.assertEqual(data_rubix['customer_name'], 'LADE EXPORTS')
        self.assertEqual(data_rubix['bureau_source'], 'Rubix Data Sciences')

        data_bir = extract_bureau_pdf(bir_pdf)
        self.assertEqual(data_bir['customer_name'], 'PRIMEX INDUSTRIES')
        self.assertEqual(data_bir['bureau_source'], 'CRIF Solutions (BIR)')

        data_birl = extract_bureau_pdf(birl_pdf)
        self.assertEqual(data_birl['customer_name'], 'Y & H CARGO PRIVATE LIMITED')
        self.assertEqual(data_birl['bureau_source'], 'CRIF Solutions (BIRL)')

    def test_docx_generation(self):
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp_path = tmp.name

        sample_data = {
            'customer_name': 'TEST LOGISTICS CLIENT',
            'nature_of_business': 'Freight forwarding, supply chain and cross-border transport.',
            'type_of_company': 'PRIVATE LIMITED',
            'date_of_incorporation': '15-05-2018',
            'crif_credit_limit': '₹ 5,00,000',
            'credit_days': '30 Days',
            'salesperson': 'Test Rep',
            'registered_address': 'Unit 101, Cargo Complex, Mumbai 400099',
            'other_address': 'N/A',
            'risk_grade_score': 'Rx4 (65)',
            'risk_description': 'Average Counterparty Risk',
            'kyc_documents': [
                {'document': 'PAN', 'status': 'Available', 'source': 'IT Portal', 'remarks': 'Active'},
                {'document': 'GST', 'status': 'Available', 'source': 'GSTN', 'remarks': 'Active'}
            ],
            'created_by': 'Test Analyst',
            'checked_by': 'Test Manager',
            'approved_by': 'Test Director',
            'date': '07/11/2026'
        }

        output_path = build_crif_docx(sample_data, tmp_path)
        self.assertTrue(os.path.exists(output_path))
        self.assertGreater(os.path.getsize(output_path), 5000)

        # Verify it parses cleanly as a valid Word doc
        doc = docx.Document(output_path)
        self.assertGreater(len(doc.tables), 3)
        os.remove(tmp_path)

    def test_enhanced_fields_docx_generation(self):
        # 1. Verify GenerateDocxRequest and RubixExtractedData validation
        rubix_data = RubixExtractedData(
            customer_name="TEST EXTRACTED CORP",
            nature_of_business="Freight Forwarding",
            type_of_company="Private Limited",
            date_of_incorporation="01-01-2015",
            registered_address="Mumbai Cargo Terminal",
            additional_info="High priority client with seasonal volume spikes.",
            commercial_mode="Air",
            mail_approval="director@jetfreight.com",
            iata_credit_days="21 Days",
            ocean_credit_days="30 Days"
        )
        self.assertEqual(rubix_data.additional_info, "High priority client with seasonal volume spikes.")
        self.assertEqual(rubix_data.commercial_mode, "Air")
        self.assertEqual(rubix_data.mail_approval, "director@jetfreight.com")
        self.assertEqual(rubix_data.iata_credit_days, "21 Days")
        self.assertEqual(rubix_data.ocean_credit_days, "30 Days")

        req = GenerateDocxRequest(
            customer_name="TEST ENHANCED CORP",
            nature_of_business="Logistics & Cold Chain",
            type_of_company="Private Limited",
            date_of_incorporation="12-05-2016",
            crif_credit_limit="₹ 25,00,000",
            credit_days="30 Days",
            salesperson="Jane Doe",
            registered_address="Plot 45, Andheri East, Mumbai 400069",
            other_address="N/A",
            risk_grade_score="Rx3 (72)",
            risk_description="Low Risk",
            kyc_documents=[{"document": "PAN", "status": "Available", "source": "ITD", "remarks": "Active"}],
            created_by="Analyst A",
            checked_by="Manager B",
            approved_by="Director C",
            date="10/11/2026",
            additional_info="Special seasonal credit extension approved for Q4.",
            commercial_mode="Air",
            mail_approval="mgmt@jetfreight.com",
            iata_credit_days="21 Days",
            ocean_credit_days="30 Days"
        )
        self.assertEqual(req.additional_info, "Special seasonal credit extension approved for Q4.")
        self.assertEqual(req.commercial_mode, "Air")
        self.assertEqual(req.mail_approval, "mgmt@jetfreight.com")
        self.assertEqual(req.iata_credit_days, "21 Days")
        self.assertEqual(req.ocean_credit_days, "30 Days")

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
            output_path = build_crif_docx(payload, tmp_path)
            self.assertTrue(os.path.exists(output_path))

            doc = docx.Document(output_path)
            table_texts = [cell.text for table in doc.tables for row in table.rows for cell in row.cells]
            combined_text = " ".join(table_texts)

            self.assertIn("Additional Information", combined_text)
            self.assertIn("Special seasonal credit extension approved for Q4.", combined_text)
            self.assertIn("[ Approved via Email: mgmt@jetfreight.com ]", combined_text)
            self.assertIn("Commercial Shipment Mode", combined_text)
            self.assertIn("IATA Air Freight Tenor", combined_text)
            self.assertIn("Sec. 138 NI Act Cheque", combined_text)
            self.assertIn("CAF with Cargo Lien Signed", combined_text)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_database_audit_record(self):
        appraisal_id = save_appraisal(
            customer_name='UNIT TEST CORP',
            crif_credit_limit='₹ 1,00,000',
            credit_days='30 Days',
            salesperson='Tester',
            type_of_company='Proprietorship',
            risk_grade='Rx5',
            docx_filename='unit_test.docx'
        )
        self.assertIsInstance(appraisal_id, int)
        all_records = get_all_appraisals()
        self.assertTrue(any(r['customer_name'] == 'UNIT TEST CORP' for r in all_records))

    def test_api_appraisals_server_side_search(self):
        client = TestClient(app)

        # Seed records for server-side search testing
        uid = f"SEARCH_TEST_{int(time.time() * 1000)}"
        save_appraisal(
            customer_name=f"ALPHA LOGISTICS {uid}",
            crif_credit_limit="₹ 5,00,000",
            credit_days="30 Days",
            salesperson="Vikram Malhotra",
            type_of_company="Private Limited",
            risk_grade="Rx3",
            docx_filename=f"alpha_{uid}.docx"
        )
        save_appraisal(
            customer_name=f"BETA TRADERS {uid}",
            crif_credit_limit="₹ 2,00,000",
            credit_days="15 Days",
            salesperson="Sunita Rao",
            type_of_company="Proprietorship",
            risk_grade="Rx4",
            docx_filename=f"beta_{uid}.docx"
        )
        save_appraisal(
            customer_name=f"GAMMA FREIGHT {uid}",
            crif_credit_limit="₹ 10,00,000",
            credit_days="45 Days",
            salesperson="Vikram Malhotra",
            type_of_company="Partnership",
            risk_grade="Rx2",
            docx_filename=f"gamma_{uid}.docx"
        )

        # 1. Search by customer name (partial, case-insensitive)
        res_customer = client.get(f"/api/appraisals?search=alpha%20logistics%20{uid.lower()}")
        self.assertEqual(res_customer.status_code, 200)
        customer_items = res_customer.json()
        self.assertEqual(len(customer_items), 1)
        self.assertEqual(customer_items[0]["customer_name"], f"ALPHA LOGISTICS {uid}")
        self.assertEqual(res_customer.headers.get("X-Total-Count"), "1")

        # 2. Search by salesperson
        res_rep = client.get(f"/api/appraisals?search=Sunita%20Rao")
        self.assertEqual(res_rep.status_code, 200)
        rep_items = res_rep.json()
        self.assertTrue(any(item["customer_name"] == f"BETA TRADERS {uid}" for item in rep_items))
        self.assertTrue(all("sunita" in item["salesperson"].lower() or "sunita" in item["customer_name"].lower() for item in rep_items))

        # 3. Search matching multiple records (salesperson Vikram Malhotra)
        res_multi = client.get(f"/api/appraisals?search=Vikram%20Malhotra")
        self.assertEqual(res_multi.status_code, 200)
        multi_items = res_multi.json()
        matched_customers = [item["customer_name"] for item in multi_items]
        self.assertIn(f"ALPHA LOGISTICS {uid}", matched_customers)
        self.assertIn(f"GAMMA FREIGHT {uid}", matched_customers)
        self.assertNotIn(f"BETA TRADERS {uid}", matched_customers)

        # 4. Search with no matches
        res_none = client.get("/api/appraisals?search=NONEXISTENT_CUSTOMER_XYZ_99999")
        self.assertEqual(res_none.status_code, 200)
        self.assertEqual(res_none.json(), [])
        self.assertEqual(res_none.headers.get("X-Total-Count"), "0")

    def test_generator_long_credit_days_scaled_font(self):
        # When len(credit_days) > 16, generator should scale font size to 8.5pt
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            tmp_path = tmp.name

        sample_data = {
            'customer_name': 'LONG TENOR CLIENT',
            'nature_of_business': 'Freight Forwarding',
            'type_of_company': 'PRIVATE LIMITED',
            'date_of_incorporation': '01-01-2020',
            'crif_credit_limit': '₹ 10,00,000',
            'credit_days': '30 Days IATA / 45 Days Ocean',  # Length is 28 > 16
            'salesperson': 'Sales Executive',
            'registered_address': 'Cargo Hub',
            'risk_grade_score': 'Rx3 (70)',
            'risk_description': 'Low Risk',
            'kyc_documents': [],
            'created_by': 'Analyst',
            'checked_by': 'Manager',
            'approved_by': 'Director',
            'date': '10/11/2026'
        }

        try:
            output_path = build_crif_docx(sample_data, tmp_path)
            self.assertTrue(os.path.exists(output_path))
            doc = docx.Document(output_path)
            # Metric table is table index 1 (or 0 is header table)
            metric_table = doc.tables[1]
            credit_days_cell = metric_table.cell(1, 1)
            first_run = credit_days_cell.paragraphs[0].runs[0]
            self.assertEqual(first_run.font.size.pt, 8.5)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_api_health(self):
        client = TestClient(app)
        res = client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

    def test_api_extract_non_pdf_rejected(self):
        client = TestClient(app)
        res = client.post("/api/extract", files={"file": ("test.txt", b"plain text", "text/plain")})
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid file type", res.json()["detail"])

    def test_api_extract_bad_magic_bytes(self):
        client = TestClient(app)
        res = client.post("/api/extract", files={"file": ("fake.pdf", b"NOTAPDFHEADER", "application/pdf")})
        self.assertEqual(res.status_code, 400)
        self.assertIn("Magic bytes", res.json()["detail"])

    def test_api_generate_and_download(self):
        client = TestClient(app)
        payload = {
            'customer_name': 'API INTEGRATION TEST CLIENT',
            'nature_of_business': 'Logistics and freight forwarding services.',
            'type_of_company': 'PRIVATE LIMITED',
            'date_of_incorporation': '10-10-2020',
            'crif_credit_limit': '₹ 10,00,000',
            'credit_days': '30 Days',
            'salesperson': 'Integration Tester',
            'registered_address': 'Terminal 2, Mumbai Airport',
            'other_address': 'N/A',
            'risk_grade_score': 'Rx3 (78)',
            'risk_description': 'Low Counterparty Risk',
            'kyc_documents': [{'document': 'PAN', 'status': 'VERIFIED', 'source': 'ITD', 'remarks': 'Active'}],
            'created_by': 'Analyst',
            'checked_by': 'Manager',
            'approved_by': 'Director',
            'date': '08/11/2026'
        }
        res = client.post("/api/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("appraisal_id", data)
        self.assertIn("access_token", data)

        # Test download with secure access_token
        dl_res = client.get(data["download_url"])
        self.assertEqual(dl_res.status_code, 200)
        self.assertGreater(len(dl_res.content), 5000)

        # Test backwards compatibility with numeric ID
        dl_res_id = client.get(f"/api/download/{data['appraisal_id']}")
        self.assertEqual(dl_res_id.status_code, 200)
        self.assertGreater(len(dl_res_id.content), 5000)

    def test_api_download_not_found(self):
        client = TestClient(app)
        res = client.get("/api/download/999999")
        self.assertEqual(res.status_code, 404)

    def test_empty_customer_name_fallback(self):
        client = TestClient(app)
        payload = {
            'customer_name': '###$$$',
            'nature_of_business': 'Testing name fallback.',
            'type_of_company': 'Proprietorship',
            'date_of_incorporation': '01-01-2020',
            'crif_credit_limit': '₹ 1,00,000',
            'credit_days': '30 Days',
            'salesperson': 'Tester',
            'registered_address': 'N/A',
            'other_address': 'N/A',
            'risk_grade_score': 'Rx5',
            'risk_description': 'Risk',
            'kyc_documents': [],
            'created_by': 'A',
            'checked_by': 'B',
            'approved_by': 'C',
            'date': '08/11/2026'
        }
        res = client.post("/api/generate", json=payload)
        self.assertEqual(res.status_code, 200)
        filename = res.json()["filename"]
        self.assertTrue("CUSTOMER" in filename)

    def test_storage_retention_pruning(self):
        import time

        now = time.time()
        old_pdf = os.path.join(UPLOADS_DIR, "test_old_3h.pdf")
        fresh_pdf = os.path.join(UPLOADS_DIR, "test_fresh_pdf.pdf")
        old_docx = os.path.join(MEMOS_DIR, "test_old_8d.docx")
        fresh_docx = os.path.join(MEMOS_DIR, "test_fresh_memo.docx")

        for f in (old_pdf, fresh_pdf, old_docx, fresh_docx):
            with open(f, "wb") as fp:
                fp.write(b"test retention content")

        # Set mtime: old_pdf = 4 hours ago, old_docx = 8 days ago
        os.utime(old_pdf, (now - 4 * 3600, now - 4 * 3600))
        os.utime(fresh_pdf, (now, now))
        os.utime(old_docx, (now - 8 * 24 * 3600, now - 8 * 24 * 3600))
        os.utime(fresh_docx, (now, now))

        stats = prune_storage_files()
        self.assertGreaterEqual(stats["pruned_pdfs"], 1)
        self.assertGreaterEqual(stats["pruned_docs"], 1)

        # Verify old files deleted, fresh files kept
        self.assertFalse(os.path.exists(old_pdf))
        self.assertFalse(os.path.exists(old_docx))
        self.assertTrue(os.path.exists(fresh_pdf))
        self.assertTrue(os.path.exists(fresh_docx))

        # Cleanup test files
        if os.path.exists(fresh_pdf):
            os.remove(fresh_pdf)
        if os.path.exists(fresh_docx):
            os.remove(fresh_docx)

    def test_maintenance_cleanup_endpoint(self):
        client = TestClient(app)
        from backend.app import main
        orig_key = main.ADMIN_SECRET_KEY
        try:
            main.ADMIN_SECRET_KEY = "test-cleanup-key"
            res = client.post("/api/maintenance/cleanup", headers={"X-Admin-Key": "test-cleanup-key"})
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "ok")
            self.assertIn("Auto-deleted after 3 hours", data["retention_policy"]["pdf"])
            self.assertIn("Auto-deleted weekly (7 days)", data["retention_policy"]["docx"])
        finally:
            main.ADMIN_SECRET_KEY = orig_key

    def test_security_headers_present(self):
        client = TestClient(app)
        res = client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("Strict-Transport-Security"), "max-age=31536000; includeSubDomains")
        self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(res.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(res.headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertEqual(
            res.headers.get("Content-Security-Policy"),
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none';"
        )
        self.assertEqual(
            res.headers.get("Permissions-Policy"),
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

    def test_admin_key_guard(self):
        client = TestClient(app)
        from backend.app import main
        orig_key = main.ADMIN_SECRET_KEY
        try:
            main.ADMIN_SECRET_KEY = "super-secret-key-123"
            # Without key -> 401
            res_no_key = client.post("/api/maintenance/cleanup")
            self.assertEqual(res_no_key.status_code, 401)
            # With wrong key -> 401
            res_bad_key = client.post("/api/maintenance/cleanup", headers={"X-Admin-Key": "wrong-key"})
            self.assertEqual(res_bad_key.status_code, 401)
            # With correct key -> 200
            res_good_key = client.post("/api/maintenance/cleanup", headers={"X-Admin-Key": "super-secret-key-123"})
            self.assertEqual(res_good_key.status_code, 200)

            # When key is unset/empty, fail-closed (401)
            main.ADMIN_SECRET_KEY = ""
            res_unset = client.post("/api/maintenance/cleanup", headers={"X-Admin-Key": "any-key"})
            self.assertEqual(res_unset.status_code, 401)
            res_unset_no_header = client.post("/api/maintenance/cleanup")
            self.assertEqual(res_unset_no_header.status_code, 401)
        finally:
            main.ADMIN_SECRET_KEY = orig_key

    def test_normalize_date_and_inr_formatting(self):
        self.assertEqual(_normalize_date("01-Jan-2019"), "01-01-2019")
        self.assertEqual(_normalize_date("15-Aug-2022"), "15-08-2022")
        self.assertEqual(_normalize_date("31-12-2020"), "31-12-2020")
        
        self.assertEqual(_format_inr(500), "₹ 500")
        self.assertEqual(_format_inr(50000), "₹ 50,000")
        self.assertEqual(_format_inr(357000), "₹ 3,57,000")
        self.assertEqual(_format_inr(1416000), "₹ 14,16,000")
        self.assertEqual(_format_inr(12500000), "₹ 1,25,00,000")

    def test_security_hardening(self):
        client = TestClient(app)

        # 1. Fail-closed admin auth for cleanup endpoint
        from backend.app import main
        orig_key = main.ADMIN_SECRET_KEY
        try:
            main.ADMIN_SECRET_KEY = ""
            res_no_key = client.post("/api/maintenance/cleanup")
            self.assertEqual(res_no_key.status_code, 401, "Cleanup must fail-closed if ADMIN_SECRET_KEY is unset")
            res_with_key = client.post("/api/maintenance/cleanup", headers={"X-Admin-Key": "some-key"})
            self.assertEqual(res_with_key.status_code, 401, "Cleanup must fail-closed if ADMIN_SECRET_KEY is unset even with header")

            main.ADMIN_SECRET_KEY = "test-secret-value-123"
            res_wrong = client.post("/api/maintenance/cleanup", headers={"X-Admin-Key": "wrong-secret"})
            self.assertEqual(res_wrong.status_code, 401, "Cleanup must return 401 on mismatched key")
            res_correct = client.post("/api/maintenance/cleanup", headers={"X-Admin-Key": "test-secret-value-123"})
            self.assertEqual(res_correct.status_code, 200, "Cleanup must succeed with valid key")
        finally:
            main.ADMIN_SECRET_KEY = orig_key

        # 2. Content-Security-Policy & Permissions-Policy headers
        health_res = client.get("/api/health")
        self.assertEqual(health_res.status_code, 200)
        self.assertEqual(
            health_res.headers.get("Content-Security-Policy"),
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none';"
        )
        self.assertEqual(
            health_res.headers.get("Permissions-Policy"),
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        # 3. S3 reconciliation restores access_token
        from backend.app import s3_storage
        with patch("backend.app.s3_storage.is_s3_enabled", return_value=True), \
             patch("backend.app.s3_storage.get_s3_client") as mock_get_client:
            mock_s3 = MagicMock()
            mock_get_client.return_value = mock_s3
            mock_paginator = MagicMock()
            mock_s3.get_paginator.return_value = mock_paginator
            mock_paginator.paginate.return_value = [
                {"Contents": [{"Key": "records/RECON_SEC_TEST.json"}]}
            ]
            record_payload = {
                "customer_name": "SECURITY TEST CORP",
                "crif_credit_limit": "₹ 15,00,000",
                "credit_days": "30",
                "salesperson": "Sec Analyst",
                "type_of_company": "Private Limited",
                "risk_grade": "Rx2",
                "docx_filename": "RECON_SEC_TEST.docx",
                "source_pdf": "sec_test.pdf",
                "access_token": "token-sec-verify-xyz987",
                "created_at": "2026-11-10T15:00:00"
            }
            body_mock = MagicMock()
            body_mock.read.return_value = json.dumps(record_payload).encode("utf-8")
            mock_s3.get_object.return_value = {"Body": body_mock}

            with get_db() as conn:
                conn.cursor().execute("DELETE FROM appraisals WHERE docx_filename = 'RECON_SEC_TEST.docx'")
                conn.commit()
                reconciled_count = s3_storage.reconcile_records_from_s3(conn)
                self.assertEqual(reconciled_count, 1)

                cursor = conn.cursor()
                cursor.execute("SELECT access_token FROM appraisals WHERE docx_filename = 'RECON_SEC_TEST.docx'")
                row = cursor.fetchone()
                self.assertIsNotNone(row)
                token_val = row["access_token"] if hasattr(row, "keys") else row[0]
                self.assertEqual(token_val, "token-sec-verify-xyz987")

        # 4. Rate limiting: excess requests trigger 429
        # 30 requests/minute per client IP
        from backend.app.main import _ip_request_timestamps, _rate_limit_lock
        with _rate_limit_lock:
            _ip_request_timestamps.clear()

        # Generate payload
        gen_payload = {
            'customer_name': 'RATE LIMIT TEST',
            'nature_of_business': 'Testing rate limit.',
            'type_of_company': 'Proprietorship',
            'date_of_incorporation': '01-01-2020',
            'crif_credit_limit': '₹ 1,00,000',
            'credit_days': '30 Days',
            'salesperson': 'Tester',
            'registered_address': 'N/A',
            'other_address': 'N/A',
            'risk_grade_score': 'Rx5',
            'risk_description': 'Risk',
            'kyc_documents': [],
            'created_by': 'A',
            'checked_by': 'B',
            'approved_by': 'C',
            'date': '08/11/2026'
        }
        # Fire 30 requests - should succeed (200)
        for _ in range(30):
            r = client.post("/api/generate", json=gen_payload)
            self.assertEqual(r.status_code, 200)
        # 31st request should be rate limited (429)
        r_limited = client.post("/api/generate", json=gen_payload)
        self.assertEqual(r_limited.status_code, 429)

        # Clear rate limiter state for clean environment
        with _rate_limit_lock:
            _ip_request_timestamps.clear()

        # 5. Guard /api/sample/{filename}
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            res_prod = client.get("/api/sample/some_sample.pdf")
            self.assertIn(res_prod.status_code, (403, 404))

if __name__ == '__main__':
    unittest.main()
