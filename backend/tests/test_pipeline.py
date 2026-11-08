import os
import sys
import unittest
import tempfile
import docx

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.parser import parse_rubix_pdf, _normalize_date, _format_inr
from backend.app.generator import build_crif_docx
from backend.app.database import init_db, save_appraisal, get_all_appraisals
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

        # Test download
        dl_res = client.get(data["download_url"])
        self.assertEqual(dl_res.status_code, 200)
        self.assertGreater(len(dl_res.content), 5000)

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
        res = client.post("/api/maintenance/cleanup")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("Auto-deleted after 3 hours", data["retention_policy"]["pdf"])
        self.assertIn("Auto-deleted weekly (7 days)", data["retention_policy"]["docx"])

    def test_normalize_date_and_inr_formatting(self):
        self.assertEqual(_normalize_date("01-Jan-2019"), "01-01-2019")
        self.assertEqual(_normalize_date("15-Aug-2022"), "15-08-2022")
        self.assertEqual(_normalize_date("31-12-2020"), "31-12-2020")
        
        self.assertEqual(_format_inr(500), "₹ 500")
        self.assertEqual(_format_inr(50000), "₹ 50,000")
        self.assertEqual(_format_inr(357000), "₹ 3,57,000")
        self.assertEqual(_format_inr(1416000), "₹ 14,16,000")
        self.assertEqual(_format_inr(12500000), "₹ 1,25,00,000")

if __name__ == '__main__':
    unittest.main()
