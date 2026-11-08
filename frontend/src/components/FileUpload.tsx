import React, { useState, useRef } from 'react';
import { Upload, AlertCircle, Loader2 } from 'lucide-react';

interface FileUploadProps {
  onFileExtracted: (file: File) => void;
  isLoading: boolean;
  error: string | null;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileExtracted,
  isLoading,
  error
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
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

  return (
    <div className="max-w-3xl mx-auto my-10 px-4">
      <div className="text-center mb-8 flex flex-col items-center">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold mb-3.5 shadow-2xs">
          <img src="/jfll-logo.jpeg" alt="Jet Freight" className="w-4 h-4 rounded-full object-contain" />
          <span>Jet Freight Logistics • Credit Control</span>
        </div>
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight sm:text-4xl">
          Customer Credit Assessment & Sanction Engine
        </h2>
        <p className="text-sm text-slate-500 mt-2 max-w-xl mx-auto leading-relaxed">
          Upload any official Rubix Business Check report. The engine automatically extracts company financial health, statutory compliance, and recommended limits to prepare an executive Credit Approval Memorandum.
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
              Drop your Rubix PDF here, or <span className="text-blue-600 underline font-semibold">browse files</span>
            </h3>
            <p className="text-xs text-slate-400 mt-2">
              Supports verified Rubix Business Check PDFs up to 25MB
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
    </div>
  );
};
