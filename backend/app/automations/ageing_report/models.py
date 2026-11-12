"""
Pydantic Models and Data Schemas for Ageing Report Automation.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class RawTransaction(BaseModel):
    row_num: int = 0
    customer: str = ""
    voucher_no: str = ""
    voucher_type: str = ""
    posting_date: Optional[str] = None
    currency: str = "INR"
    ex_rate: float = 1.0
    invoice_amount: float = 0.0
    allocated_amount: float = 0.0
    credit_note: float = 0.0
    outstanding_amount: float = 0.0
    overdue: float = 0.0
    on_account_amount: float = 0.0
    net_outstanding_inr: float = 0.0
    due_date: Optional[str] = None
    age_days: int = 0
    payment_terms: str = ""
    sales_person: str = ""
    branch: str = ""
    remarks: str = ""

class CustomerAgeingSummary(BaseModel):
    id: Optional[int] = None
    batch_uuid: str = ""
    customer_name: str
    fu_person: str = "Other"
    sales_person: str = ""
    branch: str = ""
    payment_terms: str = ""
    outstanding: float = 0.0
    received: float = 0.0
    balance: float = 0.0
    advance: float = 0.0
    remark: str = ""
    bucket_0_30: float = 0.0
    bucket_31_45: float = 0.0
    bucket_46_60: float = 0.0
    bucket_61_90: float = 0.0
    bucket_91_180: float = 0.0
    bucket_181_240: float = 0.0
    bucket_241_365: float = 0.0
    bucket_above_365: float = 0.0
    grand_total: float = 0.0
    this_iata: float = 0.0
    last_iata: float = 0.0
    on_ac: float = 0.0

class BucketMetric(BaseModel):
    label: str
    amount: float
    percentage: float
    formatted_amount: str

class BranchMetric(BaseModel):
    branch: str
    outstanding: float
    overdue: float
    customer_count: int
    share_pct: float
    formatted_outstanding: str
    formatted_overdue: str

class FUPersonMetric(BaseModel):
    fu_person: str
    outstanding: float
    received: float
    balance: float
    customer_count: int
    share_pct: float
    formatted_outstanding: str
    formatted_balance: str

class AgeingBatchSummary(BaseModel):
    batch_uuid: str
    filename: str
    posting_cutoff_date: Optional[str] = None
    total_receivable: float = 0.0
    total_overdue: float = 0.0
    this_iata: float = 0.0
    last_iata: float = 0.0
    critical_365: float = 0.0
    customer_count: int = 0
    invoice_count: int = 0
    formatted_total_receivable: str = "₹ 0"
    formatted_total_overdue: str = "₹ 0"
    formatted_this_iata: str = "₹ 0"
    formatted_last_iata: str = "₹ 0"
    formatted_critical_365: str = "₹ 0"
    bucket_distribution: List[BucketMetric] = Field(default_factory=list)
    branch_distribution: List[BranchMetric] = Field(default_factory=list)
    fu_distribution: List[FUPersonMetric] = Field(default_factory=list)
    created_at: str = ""

class UpdateCustomerRequest(BaseModel):
    fu_person: Optional[str] = None
    remark: Optional[str] = None
    received: Optional[float] = None
