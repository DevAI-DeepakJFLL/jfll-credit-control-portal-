from pydantic import BaseModel, Field
from typing import Optional, List

class KYCItem(BaseModel):
    document: str
    status: str = "Available"
    source: str = "Statutory / Bureau Verified"
    remarks: str = "Active & Verified"

class BaseAppraisalData(BaseModel):
    customer_name: str
    nature_of_business: str
    type_of_company: str
    date_of_incorporation: str
    registered_address: str
    other_address: str = "N/A"
    salesperson: str = ""
    bureau_source: Optional[str] = "Rubix Data Sciences"
    
    # Standard flags and commercial terms
    sec_138_cheque: bool = True
    caf_signed: bool = True
    iata_credit_days: str = "21 Days"
    ocean_credit_days: str = "30 Days"
    commercial_mode: str = "Both"
    customs_duty_terms: str = "0 Days (Immediate / COD)"
    additional_info: str = ""
    mail_approval: str = ""
    
    # Statutory bureau compliance highlights
    gst_delay_days: int = 0
    pf_delay_days: int = 0
    active_gst_count: int = 1
    court_cases_count: int = 0
    external_rating: str = "Not Found"
    
    # Workflow sign-offs & KYC
    kyc_documents: List[KYCItem] = Field(default_factory=list)
    created_by: str = "Credit Analyst"
    checked_by: str = "Manager - Credit Control"
    approved_by: str = "Head of Credit / Director"

class RubixExtractedData(BaseAppraisalData):
    # Credit & Risk Metrics
    rubix_credit_limit_lakhs: float = 0.0
    crif_credit_limit: str = "₹ 0.00"
    recommended_credit_days: int = 30
    approved_credit_days: str = "30 Days"
    risk_score: int = 0
    risk_grade: str = "Rx5"
    risk_description: str = "Above Average Counterparty Risk"
    
    # Form specifics
    branch: str = "Mumbai Air Cargo"
    appraisal_date: str = ""

class GenerateDocxRequest(BaseAppraisalData):
    crif_credit_limit: str
    credit_days: str
    risk_grade_score: str
    risk_description: str
    date: str
    source_pdf: Optional[str] = None

BureauExtractedData = RubixExtractedData

class AppraisalRecord(BaseModel):
    id: int
    customer_name: str
    crif_credit_limit: str
    credit_days: str
    salesperson: str
    risk_grade: str
    created_at: str
    docx_filename: str
