import React, { useState, useEffect, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { FileUpload } from './components/FileUpload';
import { MetricCards } from './components/MetricCards';
import { MemoForm } from './components/MemoForm';
import { AppraisalHistory } from './components/AppraisalHistory';
import { RubixExtractedData } from './types';
import { apiUrl } from './config/api';
import { CheckCircle2, X, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'create' | 'history'>('create');
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
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Failed to extract data from Rubix PDF');
      }

      const data: RubixExtractedData = await res.json();
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
      const payload = {
        customer_name: extractedData.customer_name,
        nature_of_business: extractedData.nature_of_business,
        type_of_company: extractedData.type_of_company,
        date_of_incorporation: extractedData.date_of_incorporation,
        crif_credit_limit: extractedData.crif_credit_limit,
        credit_days: extractedData.approved_credit_days,
        salesperson: extractedData.salesperson || 'Unassigned',
        registered_address: extractedData.registered_address,
        other_address: extractedData.other_address || 'N/A',
        risk_grade_score: `${extractedData.risk_grade} (${extractedData.risk_score})`,
        risk_description: extractedData.risk_description,
        bureau_source: extractedData.bureau_source || 'Rubix Data Sciences',
        kyc_documents: extractedData.kyc_documents,
        created_by: extractedData.created_by,
        checked_by: extractedData.checked_by,
        approved_by: extractedData.approved_by,
        date: extractedData.appraisal_date,
        sec_138_cheque: extractedData.sec_138_cheque,
        caf_signed: extractedData.caf_signed,
      };

      const res = await fetch(apiUrl('/api/generate'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || 'Failed to generate CRIF docx');
      }

      const result = await res.json();

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
        if (extractedData && !isGenerating && currentTab === 'create') {
          e.preventDefault();
          handleGenerate();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [extractedData, isGenerating, currentTab, handleGenerate]);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        onReset={() => setExtractedData(null)}
        hasData={!!extractedData}
      />

      <main className="flex-1 pb-16">
        {currentTab === 'history' ? (
          <AppraisalHistory />
        ) : !extractedData ? (
          <FileUpload
            onFileExtracted={handleFileExtracted}
            onSampleLoaded={(data) => setExtractedData(data)}
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
      </main>

      {/* Floating Success Toast (No Layout Shift) */}
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
            className="p-1 text-slate-400 hover:text-white rounded-md transition"
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
            className="p-1 text-rose-300 hover:text-white rounded-md transition"
            aria-label="Dismiss error toast"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
