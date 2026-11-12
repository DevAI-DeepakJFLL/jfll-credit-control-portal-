export interface AgeingCustomerSummary {
  fu_person: string;
  sales_person: string;
  branch: string;
  customer: string;
  payment_terms: string;
  outstanding: number;
  receive: number;
  balance: number;
  advance: number;
  remark: string;
  bucket_0_30: number;
  bucket_31_45: number;
  bucket_46_60: number;
  bucket_61_90: number;
  bucket_91_180: number;
  bucket_181_240: number;
  bucket_241_365: number;
  bucket_above_365: number;
  grand_total: number;
  this_iata: number;
  last_iata: number;
  on_ac: number;
}

export interface AgeingBatchSummary {
  batch_uuid: string;
  filename: string;
  posting_cutoff_date?: string;
  total_receivable: number;
  total_overdue: number;
  total_balance: number;
  customer_count: number;
  invoice_count: number;
  created_at: string;
  branch_breakdown: Record<string, { count: number; total: number; balance: number }>;
  fu_breakdown: Record<string, { count: number; total: number; balance: number }>;
}
