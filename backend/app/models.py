from pydantic import BaseModel, Field
from typing import Optional, List

class KYCItem(BaseModel):
    document: str
    status: str = "Available"
    source: str = "Statutory / Bureau Verified"
    remarks: str = "Active & Verified"

class RubixExtractedData(BaseModel):
    customer_name: str
    nature_of_business: str
    type_of_company: str
    date_of_incorporation: str
    registered_address: str
    other_address: str = "N/A"
    
    # Credit & Risk Metrics
    rubix_credit_limit_lakhs: float = 0.0
    crif_credit_limit: str = "₹ 0.00"
    recommended_credit_days: int = 30
    approved_credit_days: str = "30 Days"
    risk_score: int = 0
    risk_grade: str = "Rx5"
    risk_description: str = "Above Average Counterparty Risk"
    
    # Statutory Compliance Highlights
    gst_delay_days: int = 0
    pf_delay_days: int = 0
    active_gst_count: int = 1
    court_cases_count: int = 0
    external_rating: str = "Not Found"
    
    # Defaults for form
    salesperson: str = ""
    branch: str = "Mumbai Air Cargo"
    iata_credit_days: str = "21 Days"
    ocean_credit_days: str = "30 Days"
    customs_duty_terms: str = "0 Days (Advance COD)"
    
    sec_138_cheque: bool = True
    caf_signed: bool = True
    
    kyc_documents: List[KYCItem] = Field(default_factory=list)
    created_by: str = "Credit Analyst"
    checked_by: str = "Manager - Credit Control"
    approved_by: str = "Head of Credit / Director"
    appraisal_date: str = ""

class GenerateDocxRequest(BaseModel):
    customer_name: str
    nature_of_business: str
    type_of_company: str
    date_of_incorporation: str
    crif_credit_limit: str
    credit_days: str
    salesperson: str
    registered_address: str
    other_address: str = "N/A"
    risk_grade_score: str
    risk_description: str
    
    kyc_documents: List[KYCItem]
    
    created_by: str
    checked_by: str
    approved_by: str
    date: str
    
    # Additional flags
    sec_138_cheque: bool = True
    caf_signed: bool = True
    source_pdf: Optional[str] = None

class AppraisalRecord(BaseModel):
    id: int
    customer_name: str
    crif_credit_limit: str
    credit_days: str
    salesperson: str
    risk_grade: str
    created_at: str
    docx_filename: str
