export interface KYCItem {
  id?: string;
  document: string;
  status: string;
  source: string;
  remarks: string;
}

export interface RubixExtractedData {
  customer_name: string;
  nature_of_business: string;
  type_of_company: string;
  date_of_incorporation: string;
  registered_address: string;
  other_address: string;
  additional_info?: string;
  
  rubix_credit_limit_lakhs: number;
  crif_credit_limit: string;
  recommended_credit_days: number;
  approved_credit_days: string;
  risk_score: number;
  risk_grade: string;
  risk_description: string;
  
  gst_delay_days: number;
  pf_delay_days: number;
  court_cases_count: number;
  external_rating: string;
  bureau_source?: string;
  
  salesperson: string;
  branch: string;
  commercial_mode?: 'Air' | 'Ocean' | 'Both';
  iata_credit_days: string;
  ocean_credit_days: string;
  customs_duty_terms: string;
  
  sec_138_cheque: boolean;
  caf_signed: boolean;
  mail_approval?: string;
  
  kyc_documents: KYCItem[];
  created_by: string;
  checked_by: string;
  approved_by: string;
  appraisal_date: string;
}

export interface AppraisalRecord {
  id: number;
  customer_name: string;
  crif_credit_limit: string;
  credit_days: string;
  salesperson: string;
  type_of_company: string;
  risk_grade: string;
  docx_filename: string;
  created_at: string;
}
