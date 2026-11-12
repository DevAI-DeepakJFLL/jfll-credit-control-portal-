"""
Unit and Integration Tests for Ageing Report Automation Module.
Tests parser, calculation engine, Excel generator with formulas, and REST API endpoints.
"""
import os
import io
import unittest
from fastapi.testclient import TestClient
import openpyxl

from backend.app.main import app
from backend.app.core.database import init_db, get_db
from backend.app.automations.ageing_report.parser import (
    normalize_branch_name,
    parse_master_ar_file
)
from backend.app.automations.ageing_report.engine import (
    aggregate_customer_ageing,
    calculate_batch_summary,
    resolve_fu_person,
    resolve_overdue_start,
    format_crores_lacs
)
from backend.app.automations.ageing_report.generator import generate_ageing_report_excel
from backend.app.automations.ageing_report.models import RawTransaction, CustomerAgeingSummary

class TestAgeingReportModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)
        cls.sample_master_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "Ageing Report",
            "MASTER FILE - Copy.xlsx"
        )

    def test_branch_name_normalization(self):
        self.assertEqual(normalize_branch_name("BOM - Mumbai - JFL"), "Mumbai")
        self.assertEqual(normalize_branch_name("AMD - Ahmedabad - JFL"), "Ahmedabad")
        self.assertEqual(normalize_branch_name("DEL - Delhi - JFL"), "Delhi")
        self.assertEqual(normalize_branch_name("GGN - Haryana - JFL"), "Delhi")
        self.assertEqual(normalize_branch_name("BLR - Bangalore - JFL"), "Banglore")
        self.assertEqual(normalize_branch_name("COK - Cochin - JFL"), "Kerala")
        self.assertEqual(normalize_branch_name("CCJ - Calicut - JFL"), "Kerala")
        self.assertEqual(normalize_branch_name("TRV - Trivandrum - JFL"), "Kerala")
        self.assertEqual(normalize_branch_name("MAA - Chennai - JFL"), "Chennai")
        self.assertEqual(normalize_branch_name("HYD - Hyderabad - JFL"), "Hyderabad")
        self.assertEqual(normalize_branch_name("CCU - Kolkata - JFL"), "Kolkata")

    def test_fu_person_resolution(self):
        self.assertEqual(resolve_fu_person("Irfan Shaikh", "Mumbai", "ACME LOGISTICS"), "Siddhesh")
        self.assertEqual(resolve_fu_person("Richard Theknath", "Mumbai", "GLOBAL SHIPPER"), "Siddhesh")
        self.assertEqual(resolve_fu_person("Chetna Morye", "Mumbai", "DELTA FREIGHT"), "Vaibhav")
        self.assertEqual(resolve_fu_person("Unknown Rep", "Banglore", "BANGALORE CARGO"), "Nikita")
        self.assertEqual(resolve_fu_person("Unknown Rep", "Kolkata", "EASTERN CARGO"), "Vaibhav")
        # Override takes precedence
        self.assertEqual(
            resolve_fu_person("Irfan Shaikh", "Mumbai", "OVERRIDE CUST", overrides={"OVERRIDE CUST": "Nikita"}),
            "Nikita"
        )

    def test_crores_lacs_formatting(self):
        self.assertEqual(format_crores_lacs(148_200_000), "₹ 14.82 Cr")
        self.assertEqual(format_crores_lacs(9_420_000), "₹ 94.20 Lacs")
        self.assertEqual(format_crores_lacs(24_150), "₹ 24,150")

    def test_engine_bucketing_and_formulas(self):
        tx1 = RawTransaction(
            customer="TEST ENTERPRISES",
            voucher_no="V001",
            voucher_type="Sales Invoice",
            net_outstanding_inr=100_000,
            age_days=20,  # 0-30
            sales_person="Irfan Shaikh",
            branch="Mumbai"
        )
        tx2 = RawTransaction(
            customer="TEST ENTERPRISES",
            voucher_no="V002",
            voucher_type="Sales Invoice",
            net_outstanding_inr=50_000,
            age_days=40,  # 31-45 (This IATA)
            sales_person="Irfan Shaikh",
            branch="Mumbai"
        )
        tx3 = RawTransaction(
            customer="TEST ENTERPRISES",
            voucher_no="V003",
            voucher_type="Sales Invoice",
            net_outstanding_inr=30_000,
            age_days=55,  # 46-60 (Last IATA)
            sales_person="Irfan Shaikh",
            branch="Mumbai"
        )
        tx4 = RawTransaction(
            customer="TEST ENTERPRISES",
            voucher_no="V004",
            voucher_type="Sales Invoice",
            net_outstanding_inr=20_000,
            age_days=400,  # >365
            sales_person="Irfan Shaikh",
            branch="Mumbai"
        )

        customers = aggregate_customer_ageing([tx1, tx2, tx3, tx4], batch_uuid="test-b1")
        self.assertEqual(len(customers), 1)
        c = customers[0]
        self.assertEqual(c.customer_name, "TEST ENTERPRISES")
        self.assertEqual(c.fu_person, "Siddhesh")
        self.assertEqual(c.bucket_0_30, 100_000)
        self.assertEqual(c.bucket_31_45, 50_000)
        self.assertEqual(c.bucket_46_60, 30_000)
        self.assertEqual(c.bucket_above_365, 20_000)
        self.assertEqual(c.this_iata, 50_000)
        self.assertEqual(c.last_iata, 30_000)
        # Outstanding is sum of overdue (>30d): 50k + 30k + 20k = 100k
        self.assertEqual(c.outstanding, 100_000)
        # Grand total is 0-30 + overdue = 200k
        self.assertEqual(c.grand_total, 200_000)

    def test_dynamic_payment_terms_overdue_bucketing(self):
        # 1. Net 15 / Immediate terms -> overdue starts at 0-30 (Col K)
        idx_15, col_15 = resolve_overdue_start("Net 15")
        self.assertEqual(idx_15, 0)
        self.assertEqual(col_15, "K")

        idx_imm, col_imm = resolve_overdue_start("Immediate")
        self.assertEqual(idx_imm, 0)
        self.assertEqual(col_imm, "K")

        # 2. Net 30 -> overdue starts at 31-45 (Col L)
        idx_30, col_30 = resolve_overdue_start("Net 30")
        self.assertEqual(idx_30, 1)
        self.assertEqual(col_30, "L")

        # 3. Net 45 -> overdue starts at 46-60 (Col M)
        idx_45, col_45 = resolve_overdue_start("Net 45")
        self.assertEqual(idx_45, 2)
        self.assertEqual(col_45, "M")

        # 4. Net 60 -> overdue starts at 61-90 (Col N)
        idx_60, col_60 = resolve_overdue_start("Net 60")
        self.assertEqual(idx_60, 3)
        self.assertEqual(col_60, "N")

        # Check aggregation with Net 15
        tx_net15 = RawTransaction(
            customer="IMMEDIATE CUSTOMER",
            net_outstanding_inr=50_000,
            age_days=10,
            payment_terms="Net 15",
            branch="Mumbai"
        )
        res_15 = aggregate_customer_ageing([tx_net15])
        # Under Net 15, even 0-30 days balance is overdue
        self.assertEqual(res_15[0].outstanding, 50_000)

        # Check aggregation with Net 45
        tx_net45 = RawTransaction(
            customer="RELAXED CUSTOMER",
            net_outstanding_inr=50_000,
            age_days=40,  # 31-45 bucket
            payment_terms="Net 45",
            branch="Mumbai"
        )
        res_45 = aggregate_customer_ageing([tx_net45])
        # Under Net 45, 31-45 bucket is NOT overdue yet
        self.assertEqual(res_45[0].outstanding, 0.0)
        self.assertEqual(res_45[0].grand_total, 50_000)

    def test_excel_generator_structure_and_subtotals(self):
        c1 = CustomerAgeingSummary(
            customer_name="ALPHA LOGISTICS",
            fu_person="Nikita",
            sales_person="Ankit Srivastava",
            branch="Banglore",
            payment_terms="Net 30",
            outstanding=150_000,
            received=50_000,
            balance=100_000,
            bucket_0_30=50_000,
            bucket_31_45=80_000,
            bucket_46_60=70_000,
            grand_total=200_000,
            this_iata=80_000,
            last_iata=70_000
        )
        c2 = CustomerAgeingSummary(
            customer_name="BETA EXPORTS",
            fu_person="Nikita",
            sales_person="Ankit Srivastava",
            branch="Mumbai",
            payment_terms="Net 15",
            outstanding=100_000,
            received=0,
            balance=100_000,
            bucket_0_30=60_000,
            bucket_31_45=40_000,
            grand_total=100_000
        )
        excel_buf = generate_ageing_report_excel([c1, c2], batch_title="Test")
        wb = openpyxl.load_workbook(excel_buf, data_only=False)
        self.assertIn("FINAL", wb.sheetnames)
        self.assertIn("Sheet2", wb.sheetnames)

        ws_final = wb["FINAL"]
        # Row 1 subtotal formula
        self.assertEqual(ws_final.cell(1, 6).value, "=SUBTOTAL(9,F3:F4)")
        # Row 3 customer row (Net 30 -> starts at Col L)
        self.assertEqual(ws_final.cell(3, 6).value, "=SUM(L3:R3)")
        self.assertEqual(ws_final.cell(3, 8).value, "=+F3-G3")
        self.assertEqual(ws_final.cell(3, 19).value, "=SUM(K3:R3)")
        self.assertEqual(ws_final.cell(3, 21).value, "=L3")
        self.assertEqual(ws_final.cell(3, 22).value, "=M3")
        # Row 4 customer row (Net 15 -> starts at Col K)
        self.assertEqual(ws_final.cell(4, 6).value, "=SUM(K4:R4)")

        # Sheet2 dynamic formula checks
        ws_s2 = wb["Sheet2"]
        # Section 1 Grand Total uses dynamic SUM
        self.assertEqual(ws_s2.cell(5, 1).value, "Grand Total")
        self.assertEqual(ws_s2.cell(5, 2).value, "=SUM(B4:B4)")
        # Section 2 Nikita parent row uses dynamic SUM over its branches
        self.assertEqual(ws_s2.cell(8, 1).value, "Nikita")
        self.assertEqual(ws_s2.cell(8, 2).value, "=SUM(B9:B10)")
        # Section 2 Grand total row uses dynamic SUM over parent rows
        self.assertEqual(ws_s2.cell(11, 1).value, "Grand Total")
        self.assertEqual(ws_s2.cell(11, 2).value, "=SUM(B8)")

    def test_sqlite_foreign_key_enforcement(self):
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO ageing_customer_summaries (
                        batch_uuid, customer_name, fu_person
                    ) VALUES ('non-existent-batch-uuid-999', 'GHOST CUSTOMER', 'Nikita')
                    """
                )
                conn.commit()

    def test_api_upload_and_retrieve_pipeline(self):
        if not os.path.exists(self.sample_master_path):
            self.skipTest("Sample master file not found")

        # 1. Upload
        with open(self.sample_master_path, "rb") as f:
            resp = self.client.post(
                "/api/ageing/upload",
                files={"file": ("MASTER_TEST.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        batch_uuid = data["batch_uuid"]
        self.assertTrue(batch_uuid)

        # Verify summary payload
        summary = data["summary"]
        self.assertGreater(summary["customer_count"], 0)
        self.assertGreater(summary["total_receivable"], 0)
        self.assertEqual(len(summary["bucket_distribution"]), 8)
        self.assertGreater(len(summary["branch_distribution"]), 0)
        self.assertGreater(len(summary["fu_distribution"]), 0)

        # 2. Get batch summary
        sum_resp = self.client.get(f"/api/ageing/summary/{batch_uuid}")
        self.assertEqual(sum_resp.status_code, 200)
        self.assertEqual(sum_resp.json()["batch_uuid"], batch_uuid)

        # 3. Get customers with pagination & filters
        cust_resp = self.client.get(f"/api/ageing/customers/{batch_uuid}?page=1&page_size=10")
        self.assertEqual(cust_resp.status_code, 200)
        cust_data = cust_resp.json()
        self.assertEqual(len(cust_data["customers"]), 10)
        self.assertGreater(cust_data["total"], 10)

        # Test branch filter
        mumbai_resp = self.client.get(f"/api/ageing/customers/{batch_uuid}?branch=Mumbai&page=1&page_size=5")
        self.assertEqual(mumbai_resp.status_code, 200)
        for c in mumbai_resp.json()["customers"]:
            self.assertEqual(c["branch"], "Mumbai")

        # 4. Patch customer follow-up
        cust_id = cust_data["customers"][0]["id"]
        patch_resp = self.client.patch(
            f"/api/ageing/customer/{cust_id}",
            json={"fu_person": "Siddhesh", "remark": "Automated test payment follow up", "received": 25000}
        )
        self.assertEqual(patch_resp.status_code, 200)

        # 5. Export Excel
        exp_resp = self.client.get(f"/api/ageing/export/{batch_uuid}")
        self.assertEqual(exp_resp.status_code, 200)
        self.assertEqual(
            exp_resp.headers["content-type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        wb_exp = openpyxl.load_workbook(io.BytesIO(exp_resp.content))
        self.assertIn("FINAL", wb_exp.sheetnames)
        self.assertIn("Sheet2", wb_exp.sheetnames)

if __name__ == "__main__":
    unittest.main()
