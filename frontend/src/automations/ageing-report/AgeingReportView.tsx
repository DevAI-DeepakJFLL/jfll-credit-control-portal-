import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  CalendarClock, 
  UploadCloud, 
  FileSpreadsheet, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle2, 
  Download, 
  Search, 
  Building2, 
  Users, 
  RefreshCw, 
  Clock,
  ChevronLeft,
  ChevronRight,
  Edit2,
  Check,
  X,
  FileText
} from 'lucide-react';
import { apiUrl, parseJsonResponse } from '../../config/api';

interface AgeingReportViewProps {
  activeTab?: 'upload' | 'dashboard' | 'customers';
  setActiveTab?: (tab: 'upload' | 'dashboard' | 'customers') => void;
}

interface BucketMetric {
  label: string;
  amount: number;
  percentage: number;
  formatted_amount: string;
}

interface BranchMetric {
  branch: string;
  outstanding: number;
  overdue: number;
  customer_count: number;
  share_pct: number;
  formatted_outstanding: string;
  formatted_overdue: string;
}

interface FUPersonMetric {
  fu_person: string;
  outstanding: number;
  received: number;
  balance: number;
  customer_count: number;
  share_pct: number;
  formatted_outstanding: string;
  formatted_balance: string;
}

interface AgeingBatchSummary {
  batch_uuid: string;
  filename: string;
  posting_cutoff_date?: string;
  total_receivable: number;
  total_overdue: number;
  this_iata: number;
  last_iata: number;
  critical_365: number;
  customer_count: number;
  invoice_count: number;
  formatted_total_receivable: string;
  formatted_total_overdue: string;
  formatted_this_iata: string;
  formatted_last_iata: string;
  formatted_critical_365: string;
  bucket_distribution: BucketMetric[];
  branch_distribution: BranchMetric[];
  fu_distribution: FUPersonMetric[];
  created_at?: string;
}

interface CustomerAgeingRecord {
  id: number;
  batch_uuid: string;
  customer_name: string;
  fu_person: string;
  sales_person: string;
  branch: string;
  payment_terms: string;
  outstanding: number;
  received: number;
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

interface BatchListItem {
  id: number;
  batch_uuid: string;
  filename: string;
  posting_cutoff_date?: string;
  total_receivable: number;
  total_overdue: number;
  customer_count: number;
  invoice_count: number;
  created_at: string;
}

export const AgeingReportView: React.FC<AgeingReportViewProps> = ({
  activeTab: externalActiveTab,
  setActiveTab: externalSetActiveTab
}) => {
  const [internalActiveTab, setInternalActiveTab] = useState<'upload' | 'dashboard' | 'customers'>('upload');
  const activeTab = externalActiveTab ?? internalActiveTab;
  const setActiveTab = externalSetActiveTab ?? setInternalActiveTab;

  // Batch and metadata states
  const [batches, setBatches] = useState<BatchListItem[]>([]);
  const [selectedBatchUuid, setSelectedBatchUuid] = useState<string>('');
  const [summary, setSummary] = useState<AgeingBatchSummary | null>(null);

  // Debtor table states
  const [customers, setCustomers] = useState<CustomerAgeingRecord[]>([]);
  const [totalCustomers, setTotalCustomers] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(25);
  const [selectedBranch, setSelectedBranch] = useState<string>('all');
  const [selectedFUPerson, setSelectedFUPerson] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // UI status states
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [, setIsLoadingSummary] = useState<boolean>(false);
  const [isLoadingCustomers, setIsLoadingCustomers] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Inline editing state
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editFUPerson, setEditFUPerson] = useState<string>('');
  const [editRemark, setEditRemark] = useState<string>('');
  const [isSavingEdit, setIsSavingEdit] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // 1. Fetch available batches on mount
  const fetchBatches = useCallback(async () => {
    try {
      const res = await fetch(apiUrl('/api/ageing/batches'));
      if (res.ok) {
        const data: BatchListItem[] = await parseJsonResponse(res);
        setBatches(data);
        if (data.length > 0 && !selectedBatchUuid) {
          setSelectedBatchUuid(data[0].batch_uuid);
        }
      }
    } catch (err: any) {
      console.error('Failed to fetch ageing batches:', err);
    }
  }, [selectedBatchUuid]);

  useEffect(() => {
    fetchBatches();
  }, [fetchBatches]);

  // 2. Load summary when batch changes
  const loadBatchSummary = useCallback(async (batchUuid: string) => {
    if (!batchUuid) return;
    setIsLoadingSummary(true);
    setErrorMessage(null);
    try {
      const res = await fetch(apiUrl(`/api/ageing/summary/${batchUuid}`));
      if (res.ok) {
        const data: AgeingBatchSummary = await parseJsonResponse(res);
        setSummary(data);
      } else {
        const errData = await res.json().catch(() => ({}));
        setErrorMessage(errData.detail || 'Failed to load batch summary.');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Error connecting to backend.');
    } finally {
      setIsLoadingSummary(false);
    }
  }, []);

  useEffect(() => {
    if (selectedBatchUuid) {
      loadBatchSummary(selectedBatchUuid);
    }
  }, [selectedBatchUuid, loadBatchSummary]);

  // 3. Load customer table records
  const loadCustomers = useCallback(async () => {
    if (!selectedBatchUuid) return;
    setIsLoadingCustomers(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString()
      });
      if (selectedBranch && selectedBranch !== 'all') {
        params.append('branch', selectedBranch);
      }
      if (selectedFUPerson && selectedFUPerson !== 'all') {
        params.append('fu_person', selectedFUPerson);
      }
      if (searchQuery.trim()) {
        params.append('search', searchQuery.trim());
      }

      const res = await fetch(apiUrl(`/api/ageing/customers/${selectedBatchUuid}?${params.toString()}`));
      if (res.ok) {
        const data = await parseJsonResponse(res);
        setCustomers(data.customers || []);
        setTotalCustomers(data.total || 0);
      }
    } catch (err: any) {
      console.error('Error fetching customer records:', err);
    } finally {
      setIsLoadingCustomers(false);
    }
  }, [selectedBatchUuid, page, pageSize, selectedBranch, selectedFUPerson, searchQuery]);

  useEffect(() => {
    if (selectedBatchUuid) {
      loadCustomers();
    }
  }, [selectedBatchUuid, loadCustomers]);

  // 4. File upload handler
  const handleFileUpload = async (file: File) => {
    if (!file) return;
    setIsUploading(true);
    setErrorMessage(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(apiUrl('/api/ageing/upload'), {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Upload failed with HTTP ${res.status}`);
      }

      const data = await parseJsonResponse(res);
      const newBatchUuid = data.batch_uuid;
      setSelectedBatchUuid(newBatchUuid);
      setSummary(data.summary);
      await fetchBatches();
      setActiveTab('dashboard');
    } catch (err: any) {
      setErrorMessage(err.message || 'Upload processing failed.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  // 5. Customer follow-up update handler
  const handleStartEdit = (record: CustomerAgeingRecord) => {
    setEditingId(record.id);
    setEditFUPerson(record.fu_person);
    setEditRemark(record.remark || '');
  };

  const handleSaveEdit = async (customerId: number) => {
    setIsSavingEdit(true);
    try {
      const res = await fetch(apiUrl(`/api/ageing/customer/${customerId}`), {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fu_person: editFUPerson,
          remark: editRemark
        })
      });

      if (res.ok) {
        setCustomers((prev) =>
          prev.map((c) =>
            c.id === customerId ? { ...c, fu_person: editFUPerson, remark: editRemark } : c
          )
        );
        setEditingId(null);
        // Refresh summary to reflect updated FU allocations
        if (selectedBatchUuid) {
          loadBatchSummary(selectedBatchUuid);
        }
      }
    } catch (err: any) {
      console.error('Failed to update debtor record:', err);
    } finally {
      setIsSavingEdit(false);
    }
  };

  // 6. Excel download trigger
  const handleDownloadExcel = () => {
    if (!selectedBatchUuid) return;
    window.open(apiUrl(`/api/ageing/export/${selectedBatchUuid}`), '_blank');
  };

  const totalPages = Math.max(1, Math.ceil(totalCustomers / pageSize));

  return (
    <div className="w-full">
      {/* Sub-header / Automation Context Bar */}
      <div className="bg-white border-b border-slate-200 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-100">
              <CalendarClock className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-bold text-slate-900 tracking-tight">Accounts Receivable Ageing Automation</h2>
                <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200">
                  ERP AR Engine
                </span>
                {summary?.posting_cutoff_date && (
                  <span className="text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                    Cutoff: {summary.posting_cutoff_date}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500">Master AR ledger parsing, dynamic age bucketing, follow-up mapping & automated Excel compilation</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {batches.length > 0 && (
              <select
                value={selectedBatchUuid}
                onChange={(e) => {
                  setSelectedBatchUuid(e.target.value);
                  setPage(1);
                }}
                className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-700 bg-white shadow-2xs hover:border-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
              >
                {batches.map((b) => (
                  <option key={b.batch_uuid} value={b.batch_uuid}>
                    {b.filename} ({b.posting_cutoff_date || 'Current'})
                  </option>
                ))}
              </select>
            )}

            <button
              onClick={() => setActiveTab('upload')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition ${
                activeTab === 'upload'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Upload AR Dump</span>
            </button>

            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition ${
                activeTab === 'dashboard'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <TrendingUp className="w-3.5 h-3.5" />
              <span>Ageing Summary</span>
            </button>

            <button
              onClick={() => setActiveTab('customers')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition ${
                activeTab === 'customers'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span>Customer Follow-Up</span>
            </button>
          </div>
        </div>
      </div>

      {/* Global Error Banner */}
      {errorMessage && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button onClick={() => setErrorMessage(null)} className="text-rose-500 hover:text-rose-700">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Main Workspace Body */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* KPI Metric Summary Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-8">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-1">
              <span className="text-xs font-medium">Total Receivables</span>
              <Building2 className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-xl font-bold text-slate-900">
              {summary ? summary.formatted_total_receivable : '₹ 0'}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              {summary ? `${summary.customer_count} Active Debtors` : 'Awaiting upload'}
            </p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-1">
              <span className="text-xs font-medium">Overdue Exposure (&gt;30d)</span>
              <AlertTriangle className="w-4 h-4 text-amber-500" />
            </div>
            <div className="text-xl font-bold text-amber-700">
              {summary ? summary.formatted_total_overdue : '₹ 0'}
            </div>
            <p className="text-[11px] text-amber-600/80 mt-1">
              {summary && summary.total_receivable > 0
                ? `${((summary.total_overdue / summary.total_receivable) * 100).toFixed(1)}% of Total Ledger`
                : 'Overdue balance'}
            </p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-1">
              <span className="text-xs font-medium">This IATA Cycle (31-45d)</span>
              <Clock className="w-4 h-4 text-blue-500" />
            </div>
            <div className="text-xl font-bold text-blue-700">
              {summary ? summary.formatted_this_iata : '₹ 0'}
            </div>
            <p className="text-[11px] text-blue-600/80 mt-1">Current Billing Cycle</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-1">
              <span className="text-xs font-medium">Last IATA (46-60d)</span>
              <Clock className="w-4 h-4 text-indigo-500" />
            </div>
            <div className="text-xl font-bold text-indigo-700">
              {summary ? summary.formatted_last_iata : '₹ 0'}
            </div>
            <p className="text-[11px] text-indigo-600/80 mt-1">Follow-Up Escalation</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-rose-200 bg-rose-50/30 shadow-xs col-span-2 md:col-span-4 lg:col-span-1">
            <div className="flex items-center justify-between text-rose-600 mb-1">
              <span className="text-xs font-medium">Critical (&gt;365 Days)</span>
              <AlertTriangle className="w-4 h-4 text-rose-600" />
            </div>
            <div className="text-xl font-bold text-rose-700">
              {summary ? summary.formatted_critical_365 : '₹ 0'}
            </div>
            <p className="text-[11px] text-rose-600/80 mt-1">Legal / Bad Debt Watch</p>
          </div>
        </div>

        {/* Tab 1: Upload View */}
        {activeTab === 'upload' && (
          <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs max-w-3xl mx-auto">
            <div className="text-center max-w-lg mx-auto mb-8">
              <div className="w-14 h-14 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-blue-100">
                <UploadCloud className="w-7 h-7" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 tracking-tight">Upload Master Accounts Receivable Dump</h3>
              <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
                Upload your ERP Accounts Receivable export (<code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">MASTER FILE - Copy.xlsx</code>). The engine automatically parses vouchers, aggregates age buckets, assigns Follow-Up Specialists, and compiles the executive Excel report with live formulas.
              </p>
            </div>

            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-blue-500 hover:bg-blue-50/20 transition cursor-pointer"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xlsm"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileUpload(e.target.files[0]);
                  }
                }}
              />
              <FileSpreadsheet className="w-10 h-10 text-slate-400 mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-700">Drag & drop your Master AR Excel file here</p>
              <p className="text-xs text-slate-400 mt-1">Supports .xlsx and .xlsm formats (ERP Ledger Dump)</p>
              
              <button
                type="button"
                disabled={isUploading}
                className="mt-5 inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer disabled:opacity-50"
              >
                {isUploading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Processing Transactions...</span>
                  </>
                ) : (
                  <>
                    <UploadCloud className="w-4 h-4" />
                    <span>Select Master AR File</span>
                  </>
                )}
              </button>
            </div>

            <div className="mt-6 pt-6 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>Automatic 8-Bucket Calculation (0-30d to &gt;365d)</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>Follow-Up & Sales Person Mapping</span>
              </div>
            </div>

            {/* Previous Batches List */}
            {batches.length > 0 && (
              <div className="mt-8 pt-6 border-t border-slate-200">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Recently Processed Reports</h4>
                <div className="space-y-2">
                  {batches.slice(0, 5).map((b) => (
                    <div
                      key={b.batch_uuid}
                      onClick={() => {
                        setSelectedBatchUuid(b.batch_uuid);
                        setActiveTab('dashboard');
                      }}
                      className="p-3 rounded-lg border border-slate-200 hover:border-blue-400 hover:bg-slate-50 flex items-center justify-between transition cursor-pointer"
                    >
                      <div className="flex items-center space-x-3">
                        <FileText className="w-4 h-4 text-blue-600" />
                        <div>
                          <p className="text-xs font-bold text-slate-800">{b.filename}</p>
                          <p className="text-[11px] text-slate-400">
                            {b.customer_count} debtors • {b.invoice_count} vouchers • Cutoff: {b.posting_cutoff_date || 'N/A'}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-bold text-slate-900">
                          ₹ {(b.total_receivable / 10000000).toFixed(2)} Cr
                        </span>
                        <p className="text-[10px] text-slate-400">{b.created_at.slice(0, 10)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Ageing Dashboard / Buckets */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Ageing Bucket Breakdown</h3>
                <p className="text-xs text-slate-500">
                  Accounts Receivable distributed across credit payment tenors ({summary?.customer_count || 0} active debtors)
                </p>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={handleDownloadExcel}
                  disabled={!selectedBatchUuid}
                  className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer disabled:opacity-50"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Final Ageing Excel (.xlsx)</span>
                </button>
              </div>
            </div>

            {/* 8-Bucket Cards Visualization */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
              {(summary?.bucket_distribution || [
                { label: '0-30 Days', formatted_amount: '₹ 0', percentage: 0 },
                { label: '31-45 Days', formatted_amount: '₹ 0', percentage: 0 },
                { label: '46-60 Days', formatted_amount: '₹ 0', percentage: 0 },
                { label: '61-90 Days', formatted_amount: '₹ 0', percentage: 0 },
                { label: '91-180 Days', formatted_amount: '₹ 0', percentage: 0 },
                { label: '181-240 Days', formatted_amount: '₹ 0', percentage: 0 },
                { label: '241-365 Days', formatted_amount: '₹ 0', percentage: 0 },
                { label: '> 365 Days', formatted_amount: '₹ 0', percentage: 0 }
              ]).map((b, idx) => {
                const colorMap = [
                  'bg-emerald-50 border-emerald-200 text-emerald-800',
                  'bg-blue-50 border-blue-200 text-blue-800',
                  'bg-indigo-50 border-indigo-200 text-indigo-800',
                  'bg-amber-50 border-amber-200 text-amber-800',
                  'bg-orange-50 border-orange-200 text-orange-800',
                  'bg-rose-50 border-rose-200 text-rose-800',
                  'bg-rose-100 border-rose-300 text-rose-900',
                  'bg-red-100 border-red-300 text-red-950 font-bold'
                ];
                const cardColor = colorMap[idx] || colorMap[0];
                return (
                  <div key={idx} className={`p-3 rounded-xl border ${cardColor} flex flex-col justify-between`}>
                    <span className="text-[11px] font-semibold">{b.label}</span>
                    <div className="my-2">
                      <span className="text-sm font-bold block">{b.formatted_amount}</span>
                      <span className="text-[10px] opacity-75">{b.percentage}% share</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Distribution Grid: Branch Exposure + FU Specialists */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Branch Ledger Exposure */}
              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4">Branch Ledger Exposure</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {(summary?.branch_distribution || []).map((item, idx) => (
                    <div key={idx} className="p-3 rounded-lg border border-slate-100 bg-slate-50/50 flex items-center justify-between">
                      <div>
                        <p className="text-xs font-bold text-slate-800">{item.branch}</p>
                        <p className="text-[11px] text-slate-500">Overdue: {item.formatted_overdue}</p>
                        <p className="text-[10px] text-slate-400">{item.customer_count} debtors</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs font-bold text-blue-700">{item.formatted_outstanding}</p>
                        <span className="text-[10px] text-slate-500 font-medium">{item.share_pct}% share</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Follow-Up Specialist Workload */}
              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4">Follow-Up Specialist Workload</h4>
                <div className="space-y-3">
                  {(summary?.fu_distribution || []).map((fu, idx) => (
                    <div key={idx} className="p-3 rounded-lg border border-slate-100 bg-slate-50/50">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-bold text-slate-800">{fu.fu_person}</span>
                        <span className="font-bold text-slate-900">{fu.formatted_outstanding} ({fu.customer_count} debtors)</span>
                      </div>
                      <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${Math.min(100, fu.share_pct)}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                        <span>{fu.share_pct}% of total overdue exposure</span>
                        <span>Balance: {fu.formatted_balance}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Customer Follow-up Table */}
        {activeTab === 'customers' && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            {/* Filter toolbar */}
            <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center space-x-3 flex-1 min-w-[280px]">
                <div className="relative flex-1 max-w-md">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setPage(1);
                    }}
                    placeholder="Search debtor name, sales rep, or remark..."
                    className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-800 bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <select
                    value={selectedBranch}
                    onChange={(e) => {
                      setSelectedBranch(e.target.value);
                      setPage(1);
                    }}
                    className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-700 bg-white shadow-2xs"
                  >
                    <option value="all">All Branches</option>
                    <option value="Mumbai">Mumbai</option>
                    <option value="Delhi">Delhi</option>
                    <option value="Banglore">Banglore</option>
                    <option value="Kerala">Kerala</option>
                    <option value="Ahmedabad">Ahmedabad</option>
                    <option value="Chennai">Chennai</option>
                    <option value="Hyderabad">Hyderabad</option>
                    <option value="Kolkata">Kolkata</option>
                  </select>

                  <select
                    value={selectedFUPerson}
                    onChange={(e) => {
                      setSelectedFUPerson(e.target.value);
                      setPage(1);
                    }}
                    className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-700 bg-white shadow-2xs"
                  >
                    <option value="all">All Follow-Up Persons</option>
                    <option value="Nikita">Nikita</option>
                    <option value="Vaibhav">Vaibhav</option>
                    <option value="Siddhesh">Siddhesh</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <span className="text-xs text-slate-500">
                  Showing {customers.length} of {totalCustomers} debtors
                </span>
                <button
                  onClick={handleDownloadExcel}
                  disabled={!selectedBatchUuid}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer disabled:opacity-50"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Export Excel</span>
                </button>
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="py-2.5 px-3">Follow-Up</th>
                    <th className="py-2.5 px-3">Customer Name</th>
                    <th className="py-2.5 px-3">Branch</th>
                    <th className="py-2.5 px-3">Sales Person</th>
                    <th className="py-2.5 px-3 text-right">Outstanding</th>
                    <th className="py-2.5 px-3 text-right">This IATA</th>
                    <th className="py-2.5 px-3 text-right">Last IATA</th>
                    <th className="py-2.5 px-3 text-right">&gt; 90 Days</th>
                    <th className="py-2.5 px-3 text-right">Grand Total</th>
                    <th className="py-2.5 px-3">Remark</th>
                    <th className="py-2.5 px-3 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {isLoadingCustomers ? (
                    <tr>
                      <td colSpan={11} className="py-8 text-center text-slate-400">
                        <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-600" />
                        <span>Loading debtors...</span>
                      </td>
                    </tr>
                  ) : customers.length === 0 ? (
                    <tr>
                      <td colSpan={11} className="py-8 text-center text-slate-400">
                        No debtor records found matching the criteria.
                      </td>
                    </tr>
                  ) : (
                    customers.map((row) => {
                      const isEditing = editingId === row.id;
                      const above90 = row.bucket_91_180 + row.bucket_181_240 + row.bucket_241_365 + row.bucket_above_365;

                      return (
                        <tr key={row.id} className="hover:bg-slate-50 transition">
                          <td className="py-2 px-3 font-semibold text-slate-800">
                            {isEditing ? (
                              <select
                                value={editFUPerson}
                                onChange={(e) => setEditFUPerson(e.target.value)}
                                className="px-2 py-1 rounded border border-blue-400 text-xs bg-white"
                              >
                                <option value="Nikita">Nikita</option>
                                <option value="Vaibhav">Vaibhav</option>
                                <option value="Siddhesh">Siddhesh</option>
                                <option value="Other">Other</option>
                              </select>
                            ) : (
                              <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold ${
                                row.fu_person === 'Nikita' ? 'bg-purple-50 text-purple-700 border border-purple-200' :
                                row.fu_person === 'Vaibhav' ? 'bg-blue-50 text-blue-700 border border-blue-200' :
                                row.fu_person === 'Siddhesh' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                                'bg-slate-100 text-slate-600'
                              }`}>
                                {row.fu_person}
                              </span>
                            )}
                          </td>
                          <td className="py-2 px-3 font-semibold text-slate-900 max-w-xs truncate" title={row.customer_name}>
                            {row.customer_name}
                          </td>
                          <td className="py-2 px-3">{row.branch}</td>
                          <td className="py-2 px-3 text-slate-600">{row.sales_person}</td>
                          <td className="py-2 px-3 text-right font-bold text-slate-900">
                            ₹ {row.outstanding.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                          </td>
                          <td className="py-2 px-3 text-right text-blue-700 font-semibold">
                            ₹ {row.this_iata.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                          </td>
                          <td className="py-2 px-3 text-right text-indigo-700 font-semibold">
                            ₹ {row.last_iata.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                          </td>
                          <td className="py-2 px-3 text-right text-rose-700 font-semibold">
                            ₹ {above90.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                          </td>
                          <td className="py-2 px-3 text-right font-semibold text-slate-800">
                            ₹ {row.grand_total.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                          </td>
                          <td className="py-2 px-3 text-slate-500 italic max-w-xs">
                            {isEditing ? (
                              <input
                                type="text"
                                value={editRemark}
                                onChange={(e) => setEditRemark(e.target.value)}
                                className="w-full px-2 py-1 rounded border border-blue-400 text-xs bg-white"
                                placeholder="Add follow-up notes..."
                              />
                            ) : (
                              <span className="truncate block" title={row.remark || 'No remark'}>
                                {row.remark || '-'}
                              </span>
                            )}
                          </td>
                          <td className="py-2 px-3 text-center">
                            {isEditing ? (
                              <div className="flex items-center justify-center space-x-1">
                                <button
                                  onClick={() => handleSaveEdit(row.id)}
                                  disabled={isSavingEdit}
                                  className="p-1 rounded bg-emerald-600 text-white hover:bg-emerald-700 cursor-pointer"
                                  title="Save Changes"
                                >
                                  <Check className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  onClick={() => setEditingId(null)}
                                  className="p-1 rounded bg-slate-200 text-slate-600 hover:bg-slate-300 cursor-pointer"
                                  title="Cancel"
                                >
                                  <X className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            ) : (
                              <button
                                onClick={() => handleStartEdit(row)}
                                className="p-1 text-slate-400 hover:text-blue-600 transition cursor-pointer"
                                title="Edit Follow-up assignment or remark"
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination controls */}
            {totalPages > 1 && (
              <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-600">
                <span>
                  Page {page} of {totalPages} ({totalCustomers} total debtors)
                </span>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="p-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-40 cursor-pointer"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="px-2 font-medium">Page {page}</span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="p-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-40 cursor-pointer"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
