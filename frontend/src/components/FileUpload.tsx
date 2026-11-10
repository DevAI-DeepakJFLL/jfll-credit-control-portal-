import React, { useState, useRef } from 'react';
import { Upload, AlertCircle, Loader2, Sparkles, ArrowRight } from 'lucide-react';
import { RubixExtractedData } from '../types';

interface FileUploadProps {
  onFileExtracted: (file: File) => void;
  onSampleLoaded?: (data: RubixExtractedData) => void;
  isLoading: boolean;
  error: string | null;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileExtracted,
  onSampleLoaded,
  isLoading,
  error
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [loadingSample, setLoadingSample] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
        onFileExtracted(file);
      }
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileExtracted(e.target.files[0]);
    }
  };

  const loadSample = async (filename: string) => {
    if (!onSampleLoaded) return;
    setLoadingSample(filename);
    try {
      const res = await fetch(`/api/sample/${encodeURIComponent(filename)}`);
      if (!res.ok) {
        throw new Error('Failed to load sample from server');
      }
      const data: RubixExtractedData = await res.json();
      onSampleLoaded(data);
    } catch (err: any) {
      alert(err.message || 'Error loading sample');
    } finally {
      setLoadingSample(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto my-10 px-4">
      <div className="text-center mb-8 flex flex-col items-center">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold mb-3.5 shadow-2xs">
          <img src="/jfll-logo.jpeg" alt="Jet Freight" className="w-4 h-4 rounded-full object-contain" />
          <span>Jet Freight Logistics • Credit Control</span>
        </div>
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight sm:text-4xl">
          Customer Credit Assessment & Sanction Engine
        </h2>
        <p className="text-sm text-slate-500 mt-2 max-w-xl mx-auto leading-relaxed">
          Upload any official Rubix Business Check or CRIF High Mark (BIR / BIRL) report. The engine automatically extracts company profile, statutory filings, and risk limits to prepare an executive Credit Approval Memorandum.
        </p>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200 ${
          isDragOver
            ? 'border-blue-600 bg-blue-50/60 scale-[1.01] shadow-md'
            : 'border-slate-300 hover:border-blue-500 bg-white hover:bg-slate-50/50 shadow-xs'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleFileInput}
          disabled={isLoading}
        />

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-6">
            <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-3" />
            <h3 className="font-bold text-slate-800 text-base">Analyzing Customer Credit & Bureau Profile...</h3>
            <p className="text-xs text-slate-500 mt-1">Extracting company financial health, credit limits, and statutory filings</p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-4">
            <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600 mb-4 shadow-xs border border-blue-100 group-hover:scale-105 transition-transform">
              <Upload className="w-7 h-7" />
            </div>
            <h3 className="font-bold text-slate-900 text-base">
              Drop your Rubix or CRIF (BIR / BIRL) PDF here, or <span className="text-blue-600 underline font-semibold">browse files</span>
            </h3>
            <p className="text-xs text-slate-400 mt-2">
              Supports official Rubix Business Check & CRIF High Mark BIR/BIRL reports up to 25MB
            </p>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 flex items-center space-x-2 text-rose-700 text-xs text-left">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Quick Load Test Samples */}
      {onSampleLoaded && (
        <div className="mt-8 bg-slate-100/80 rounded-2xl p-5 border border-slate-200/80">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2 text-xs font-bold text-slate-700">
              <Sparkles className="w-4 h-4 text-amber-500" />
              <span>Instant Test Bureau Samples (Rubix & CRIF):</span>
            </div>
            <span className="text-[11px] text-slate-400 font-medium">Click to test instant extraction</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { name: "LADE EXPORTS", file: "LADE EXPORTS (2).pdf", bureau: "Rubix", subtitle: "Proprietorship", limit: "₹3.57L / 21D" },
              { name: "PRIMEX INDUSTRIES", file: "PRIMEX INDUSTRIES_BIR_15-Oct-2026.pdf", bureau: "CRIF BIR", subtitle: "Partnership (Score 56)", limit: "Manual Limit" },
              { name: "Y & H CARGO", file: "Y & H CARGO PRIVATE LIMITED-BIRL-06-Nov-2026.pdf", bureau: "CRIF BIRL", subtitle: "Pvt Ltd (Rating 4/5)", limit: "₹35.00L Limit" },
              { name: "SEPIO PRODUCTS", file: "SEPIO PRODUCTS PRIVATE LIMITED-1.pdf", bureau: "Rubix", subtitle: "Pvt Ltd (114D PF Alert)", limit: "₹14.16L / 24D" }
            ].map((sample, idx) => (
              <button
                key={idx}
                disabled={loadingSample === sample.file || isLoading}
                onClick={(e) => {
                  e.stopPropagation();
                  loadSample(sample.file);
                }}
                className="text-left p-3.5 rounded-xl bg-white border border-slate-200 hover:border-blue-500 hover:shadow-xs transition group relative overflow-hidden cursor-pointer"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-xs text-slate-900 group-hover:text-blue-600 transition truncate">
                    {sample.name}
                  </span>
                  {loadingSample === sample.file ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-600" />
                  ) : (
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
                  )}
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-[10px] text-slate-500 truncate max-w-[110px]">{sample.subtitle}</span>
                  <span className="text-[9px] font-semibold px-1.5 py-0.2 rounded bg-blue-50 text-blue-700 border border-blue-200/60">
                    {sample.bureau}
                  </span>
                </div>
                <div className="text-[11px] font-semibold text-blue-800 mt-1 tabular-nums">{sample.limit}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
