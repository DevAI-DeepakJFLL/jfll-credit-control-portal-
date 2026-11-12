import React, { useState, useEffect, useCallback } from 'react';
import { FileUpload } from './components/FileUpload';
import { MetricCards } from './components/MetricCards';
import { MemoForm } from './components/MemoForm';
import { AppraisalHistory } from './components/AppraisalHistory';
import { RubixExtractedData } from './types';
import { apiUrl, parseJsonResponse } from '../../config/api';
import { CheckCircle2, X, AlertCircle, FileText, History, PlusCircle } from 'lucide-react';

interface CreditAppraisalViewProps {
  subTab?: 'create' | 'history';
  setSubTab?: (tab: 'create' | 'history') => void;
}

export const CreditAppraisalView: React.FC<CreditAppraisalViewProps> = ({
  subTab: externalSubTab,
  setSubTab: externalSetSubTab
}) => {
  const [internalSubTab, setInternalSubTab] = useState<'create' | 'history'>('create');
  const subTab = externalSubTab ?? internalSubTab;
  const setSubTab = externalSetSubTab ?? setInternalSubTab;
  const [extractedData, setExtractedData] = useState<RubixExtractedData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);
  const [errorToast, setErrorToast] = useState<string | null>(null);

  const handleFileExtracted = async (file: File) => {
    setIsLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(apiUrl('/api/extract'), {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errJson = await parseJsonResponse(res).catch(() => ({ detail: 'Failed to extract data from PDF report' }));
        throw new Error(errJson.detail || 'Failed to extract data from PDF report');
      }

      const data: RubixExtractedData = await parseJsonResponse<RubixExtractedData>(res);
      setExtractedData(data);
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred during extraction');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerate = useCallback(async () => {
    if (!extractedData || isGenerating) return;
    setIsGenerating(true);
    try {
      let creditDays = `Air: ${extractedData.iata_credit_days || '15 Days'} | Ocean: ${extractedData.ocean_credit_days || '30 Days'}`;
      if (extractedData.commercial_mode === 'Air') {
        creditDays = extractedData.iata_credit_days || '15 Days';
      } else if (extractedData.commercial_mode === 'Ocean') {
        creditDays = extractedData.ocean_credit_days || '30 Days';
      }

      const payload = {
        customer_name: extractedData.customer_name,
        nature_of_business: extractedData.nature_of_business,
        type_of_company: extractedData.type_of_company,
        date_of_incorporation: extractedData.date_of_incorporation,
        crif_credit_limit: extractedData.crif_credit_limit,
        credit_days: creditDays,
        iata_credit_days: extractedData.iata_credit_days || '15 Days',
        ocean_credit_days: extractedData.ocean_credit_days || '30 Days',
        commercial_mode: extractedData.commercial_mode || 'Both',
        additional_info: extractedData.additional_info || '',
        mail_approval: extractedData.mail_approval || '',
        salesperson: extractedData.salesperson || 'Unassigned',
        registered_address: extractedData.registered_address,
        other_address: extractedData.other_address || 'N/A',
        risk_grade_score: `${extractedData.risk_grade} (${extractedData.risk_score})`,
        risk_description: extractedData.risk_description,
        bureau_source: extractedData.bureau_source || 'Rubix Data Sciences',
        kyc_documents: (extractedData.kyc_documents || []).filter(
          (item) => item.document && item.document.trim() !== ''
        ),
        created_by: extractedData.created_by,
        checked_by: extractedData.checked_by,
        approved_by: extractedData.approved_by,
        date: extractedData.appraisal_date,
        branch: extractedData.branch || 'Mumbai Air Cargo',
        sec_138_cheque: extractedData.sec_138_cheque,
        caf_signed: extractedData.caf_signed,
        customs_duty_terms: extractedData.customs_duty_terms || '0 Days (Immediate / COD)',
        gst_delay_days: extractedData.gst_delay_days ?? 0,
        pf_delay_days: extractedData.pf_delay_days ?? 0,
        court_cases_count: extractedData.court_cases_count ?? 0,
      };

      const res = await fetch(apiUrl('/api/generate'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await parseJsonResponse(res).catch(() => ({ detail: 'Failed to generate CRIF docx' }));
        throw new Error(errJson.detail || 'Failed to generate CRIF docx');
      }

      const result = await parseJsonResponse(res);

      // Trigger automatic browser download
      const link = document.createElement('a');
      link.href = apiUrl(result.download_url);
      link.download = result.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      setSuccessToast(`Successfully generated ${result.filename}!`);
      setTimeout(() => setSuccessToast(null), 5000);
    } catch (err: any) {
      setErrorToast(`Generation Failed: ${err.message || 'Server error'}`);
      setTimeout(() => setErrorToast(null), 6000);
    } finally {
      setIsGenerating(false);
    }
  }, [extractedData, isGenerating]);

  // Global keyboard shortcut: Cmd+Enter (Mac) or Ctrl+Enter (Win/Linux) to generate CRIF Memo
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        if (extractedData && !isGenerating && subTab === 'create') {
          e.preventDefault();
          handleGenerate();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [extractedData, isGenerating, subTab, handleGenerate]);

  return (
    <div className="w-full">
      {/* Sub-header / Automation Context Bar */}
      <div className="bg-white border-b border-slate-200 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-blue-50 text-blue-700 border border-blue-100">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-bold text-slate-900 tracking-tight">Credit Appraisal Memorandum (CAM)</h2>
                <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                  Rubix & CRIF Parser
                </span>
              </div>
              <p className="text-xs text-slate-500">Automated underwriting report ingestion, risk scoring & 1-page executive memo generator</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setSubTab('create')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition ${
                subTab === 'create'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Assessment Form</span>
            </button>

            <button
              onClick={() => setSubTab('history')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer transition ${
                subTab === 'history'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              <span>Appraisal History</span>
            </button>

            {extractedData && subTab === 'create' && (
              <button
                onClick={() => setExtractedData(null)}
                className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-500 hover:text-slate-900 hover:bg-slate-100 border border-slate-200 transition cursor-pointer"
                title="Upload another customer report"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                <span>New Customer Check</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Workspace Body */}
      <div className="pb-16">
        {subTab === 'history' ? (
          <AppraisalHistory />
        ) : !extractedData ? (
          <FileUpload
            onFileExtracted={handleFileExtracted}
            isLoading={isLoading}
            error={error}
          />
        ) : (
          <div className="max-w-5xl mx-auto my-8 px-4 sm:px-6">
            <div className="flex items-center justify-between mb-6 pb-3 border-b border-slate-200">
              <div>
                <span className="text-xs font-semibold text-blue-600 uppercase tracking-wider">Customer Credit Assessment & Sanction Review</span>
                <h1 className="text-2xl font-bold text-slate-900 tracking-tight mt-0.5">{extractedData.customer_name}</h1>
              </div>
              <button
                onClick={() => setExtractedData(null)}
                className="text-xs font-medium text-slate-500 hover:text-slate-800 underline transition cursor-pointer"
              >
                Upload Different Report
              </button>
            </div>

            <MetricCards
              data={extractedData}
              onChange={(updated) => setExtractedData({ ...extractedData, ...updated })}
            />

            <MemoForm
              data={extractedData}
              onChange={(updated) => setExtractedData({ ...extractedData, ...updated })}
              onGenerate={handleGenerate}
              isGenerating={isGenerating}
            />
          </div>
        )}
      </div>

      {/* Floating Success Toast */}
      {successToast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center space-x-3 px-4 py-3 rounded-xl bg-slate-900 text-white shadow-2xl border border-slate-800 transition-all">
          <div className="p-1 rounded-full bg-emerald-500/20 text-emerald-400">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div className="text-xs">
            <p className="font-semibold">{successToast}</p>
            <p className="text-[11px] text-slate-400">Document saved to SQLite history and downloaded.</p>
          </div>
          <button
            onClick={() => setSuccessToast(null)}
            className="p-1 text-slate-400 hover:text-white rounded-md transition cursor-pointer"
            aria-label="Dismiss toast"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Floating Error Toast */}
      {errorToast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center space-x-3 px-4 py-3 rounded-xl bg-rose-950 text-white shadow-2xl border border-rose-800 transition-all">
          <div className="p-1 rounded-full bg-rose-500/20 text-rose-400">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div className="text-xs">
            <p className="font-semibold text-rose-200">{errorToast}</p>
            <p className="text-[11px] text-rose-300/80">Please verify input parameters and retry.</p>
          </div>
          <button
            onClick={() => setErrorToast(null)}
            className="p-1 text-rose-300 hover:text-white rounded-md transition cursor-pointer"
            aria-label="Dismiss error toast"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
