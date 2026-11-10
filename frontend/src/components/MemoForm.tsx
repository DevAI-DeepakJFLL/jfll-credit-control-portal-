import React, { useEffect } from 'react';
import {
  Building2,
  FileCheck2,
  ShieldAlert,
  Award,
  Download,
  Loader2,
  CheckSquare,
  ChevronDown,
  Plus,
  Trash2,
  Plane,
  Ship,
  Layers,
  MailCheck,
} from 'lucide-react';
import { RubixExtractedData, KYCItem } from '../types';

interface MemoFormProps {
  data: RubixExtractedData;
  onChange: (updated: Partial<RubixExtractedData>) => void;
  onGenerate: () => void;
  isGenerating: boolean;
}

const CREDIT_TENOR_OPTIONS = [
  '7 Days',
  '10 Days',
  '15 Days',
  '21 Days',
  '30 Days',
  '45 Days',
  '60 Days',
];

export const MemoForm: React.FC<MemoFormProps> = ({ data, onChange, onGenerate, isGenerating }) => {
  const currentMode = data.commercial_mode || 'Both';
  const isAirDisabled = currentMode === 'Ocean';
  const isOceanDisabled = currentMode === 'Air';

  // Ensure all KYC items have a stable client-side id so editing document titles does not cause key changes and unmount inputs
  useEffect(() => {
    if (data.kyc_documents && data.kyc_documents.some((item) => !item.id)) {
      const withIds = data.kyc_documents.map((item, idx) => ({
        ...item,
        id: item.id || `kyc-${idx}-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      }));
      onChange({ kyc_documents: withIds });
    }
  }, [data.kyc_documents, onChange]);

  const updateKYC = (index: number, field: keyof KYCItem, value: string) => {
    const updated = [...(data.kyc_documents || [])];
    updated[index] = { ...updated[index], [field]: value };
    onChange({ kyc_documents: updated });
  };

  const addKYCItem = () => {
    const newItem: KYCItem = {
      id: `kyc-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      document: '',
      status: 'Available',
      source: 'Customer Submission',
      remarks: '',
    };
    onChange({ kyc_documents: [...(data.kyc_documents || []), newItem] });
  };

  const deleteKYCItem = (index: number) => {
    const item = data.kyc_documents?.[index];
    const docName = item?.document?.trim() ? `"${item.document.trim()}"` : 'this document';
    if (window.confirm(`Are you sure you want to remove ${docName} from the KYC checklist?`)) {
      const updated = (data.kyc_documents || []).filter((_, idx) => idx !== index);
      onChange({ kyc_documents: updated });
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Risk Alert Banner if PF delay or litigation exists */}
      {(data.pf_delay_days > 30 || data.court_cases_count > 0) && (
        <div className="bg-amber-50/90 border border-amber-200 rounded-xl p-4 shadow-xs">
          <div className="flex items-start space-x-3">
            <div className="p-2 rounded-lg bg-amber-100 text-amber-700 flex-shrink-0">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-amber-900">Bureau Statutory Compliance Alerts Detected</h4>
              <ul className="text-xs text-amber-800 mt-1.5 list-disc list-inside space-y-1">
                {data.pf_delay_days > 30 && (
                  <li><strong>Critical PF Delay:</strong> Statutory Employees' Provident Fund filing is delayed by <strong className="underline decoration-amber-400">{data.pf_delay_days} days</strong>. High cash-flow stress signal.</li>
                )}
                {data.court_cases_count > 0 && (
                  <li><strong>Litigation Record:</strong> Found <strong className="underline decoration-amber-400">{data.court_cases_count} High Court</strong> court case(s) on record. Verify non-defaulter status.</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* 1. Customer Identity & Profile Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <div className="flex items-center space-x-2 text-sm font-bold text-slate-800 mb-4 pb-2 border-b border-slate-100">
          <Building2 className="w-4 h-4 text-blue-600" />
          <span>1. Customer Identity & Entity Profile</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-slate-600 mb-1">Customer Legal Name</label>
            <input
              type="text"
              value={data.customer_name}
              onChange={(e) => onChange({ customer_name: e.target.value.toUpperCase() })}
              className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-sm font-bold text-slate-900 bg-white focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1 transition"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Company Constitution / Class</label>
            <div className="relative">
              <select
                value={data.type_of_company}
                onChange={(e) => onChange({ type_of_company: e.target.value })}
                className="w-full appearance-none pr-8 px-3.5 py-2 rounded-lg border border-slate-300 text-sm text-slate-800 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1 bg-white transition cursor-pointer"
              >
                <option value="Proprietorship">Proprietorship</option>
                <option value="Partnership">Partnership</option>
                <option value="PRIVATE LIMITED">PRIVATE LIMITED</option>
                <option value="Public Limited">Public Limited</option>
                <option value="LLP">Limited Liability Partnership (LLP)</option>
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Date of Incorporation / Registration</label>
            <input
              type="text"
              value={data.date_of_incorporation}
              onChange={(e) => onChange({ date_of_incorporation: e.target.value })}
              className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-sm text-slate-800 bg-white focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1 transition"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-slate-600 mb-1">Registered / Business Address</label>
            <textarea
              rows={2}
              value={data.registered_address}
              onChange={(e) => onChange({ registered_address: e.target.value })}
              className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 bg-white focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1 transition"
            />
          </div>

          <div className="md:col-span-2">
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-600">
                Additional Information (Special Notes / Group Background)
              </label>
              <span className="text-[11px] text-slate-400">Optional · Appended to Memorandum Profile</span>
            </div>
            <textarea
              rows={2}
              value={data.additional_info || ''}
              onChange={(e) => onChange({ additional_info: e.target.value })}
              placeholder="e.g. Group company affiliations, parent entity financials, promoter background, or key customer covenants..."
              className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 bg-white placeholder:text-slate-400 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1 transition"
            />
          </div>
        </div>
      </div>

      {/* 2. Nature of Business Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <div className="flex items-center space-x-2 text-sm font-bold text-slate-800 mb-3 pb-2 border-b border-slate-100">
          <Award className="w-4 h-4 text-blue-600" />
          <span>2. Nature of Business & Operational Scope</span>
        </div>
        <textarea
          rows={3}
          value={data.nature_of_business}
          onChange={(e) => onChange({ nature_of_business: e.target.value })}
          className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-xs leading-relaxed text-slate-800 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1 bg-slate-50/50 transition"
        />
      </div>

      {/* 3. Logistics-Specific Credit Terms & Safeguards */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <div className="flex items-center justify-between text-sm font-bold text-slate-800 mb-4 pb-2 border-b border-slate-100">
          <div className="flex items-center space-x-2">
            <CheckSquare className="w-4 h-4 text-blue-600" />
            <span>3. Logistics Commercial Terms & Risk Controls</span>
          </div>
          <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
            Jet Freight Standard
          </span>
        </div>

        {/* Commercial Mode Segmented Toggle Pills */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 p-3 bg-slate-50/70 rounded-xl border border-slate-200/80">
          <div>
            <span className="text-xs font-bold text-slate-700 block">Commercial Shipment Mode</span>
            <span className="text-[11px] text-slate-500">Select active freight mode to calibrate credit tenors</span>
          </div>
          <div className="inline-flex p-1 bg-slate-100 rounded-lg border border-slate-200 gap-1 self-start sm:self-auto">
            {(['Air', 'Ocean', 'Both'] as const).map((mode) => {
              const isActive = currentMode === mode;
              return (
                <button
                  key={mode}
                  type="button"
                  onClick={() => onChange({ commercial_mode: mode })}
                  className={`px-3.5 py-1.5 rounded-md text-xs transition cursor-pointer flex items-center space-x-1.5 ${
                    isActive
                      ? 'bg-blue-600 text-white font-bold shadow-xs'
                      : 'bg-slate-100 text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {mode === 'Air' && <Plane className="w-3.5 h-3.5" />}
                  {mode === 'Ocean' && <Ship className="w-3.5 h-3.5" />}
                  {mode === 'Both' && <Layers className="w-3.5 h-3.5" />}
                  <span>{mode}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-600">IATA Air Freight Tenor</label>
              {isAirDisabled && (
                <span className="text-[10px] text-amber-700 font-semibold bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                  Inactive (Ocean Only)
                </span>
              )}
            </div>
            <div className="relative">
              <select
                disabled={isAirDisabled}
                value={data.iata_credit_days || '15 Days'}
                onChange={(e) => onChange({ iata_credit_days: e.target.value })}
                className={`w-full appearance-none pr-8 px-3 py-2 rounded-lg border text-xs transition ${
                  isAirDisabled
                    ? 'bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed opacity-60'
                    : 'bg-white text-slate-800 border-slate-300 cursor-pointer focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1'
                }`}
              >
                {(!CREDIT_TENOR_OPTIONS.includes(data.iata_credit_days) && data.iata_credit_days) && (
                  <option value={data.iata_credit_days}>{data.iata_credit_days}</option>
                )}
                {CREDIT_TENOR_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
              <ChevronDown className={`pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 ${
                isAirDisabled ? 'text-slate-300' : 'text-slate-400'
              }`} />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-semibold text-slate-600">Ocean / Multimodal Tenor</label>
              {isOceanDisabled && (
                <span className="text-[10px] text-amber-700 font-semibold bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                  Inactive (Air Only)
                </span>
              )}
            </div>
            <div className="relative">
              <select
                disabled={isOceanDisabled}
                value={data.ocean_credit_days || '30 Days'}
                onChange={(e) => onChange({ ocean_credit_days: e.target.value })}
                className={`w-full appearance-none pr-8 px-3 py-2 rounded-lg border text-xs transition ${
                  isOceanDisabled
                    ? 'bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed opacity-60'
                    : 'bg-white text-slate-800 border-slate-300 cursor-pointer focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1'
                }`}
              >
                {(!CREDIT_TENOR_OPTIONS.includes(data.ocean_credit_days) && data.ocean_credit_days) && (
                  <option value={data.ocean_credit_days}>{data.ocean_credit_days}</option>
                )}
                {CREDIT_TENOR_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
              <ChevronDown className={`pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 ${
                isOceanDisabled ? 'text-slate-300' : 'text-slate-400'
              }`} />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Customs Duty & Handling</label>
            <input
              type="text"
              readOnly
              value="0 Days (Immediate / COD)"
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-xs font-semibold text-slate-500 bg-slate-100 cursor-not-allowed"
            />
          </div>
        </div>

        {/* Security Instruments */}
        <div className="pt-3 border-t border-slate-100 flex flex-wrap gap-4 text-xs">
          <label className="flex items-center space-x-2.5 cursor-pointer">
            <input
              type="checkbox"
              checked={data.sec_138_cheque}
              onChange={(e) => onChange({ sec_138_cheque: e.target.checked })}
              className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4 cursor-pointer"
            />
            <span className="font-medium text-slate-700">Security Cheque Collected (Section 138 NI Act)</span>
          </label>

          <label className="flex items-center space-x-2.5 cursor-pointer">
            <input
              type="checkbox"
              checked={data.caf_signed}
              onChange={(e) => onChange({ caf_signed: e.target.checked })}
              className="rounded text-blue-600 focus:ring-blue-500 w-4 h-4 cursor-pointer"
            />
            <span className="font-medium text-slate-700">Credit Application Form (CAF) with Cargo Lien Signed</span>
          </label>
        </div>
      </div>

      {/* 4. KYC Checklist Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <div className="flex items-center space-x-2 text-sm font-bold text-slate-800 mb-3 pb-2 border-b border-slate-100">
          <FileCheck2 className="w-4 h-4 text-blue-600" />
          <span>4. KYC Verification & Statutory Checklist</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                <th className="py-2.5 px-3">Document</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Source</th>
                <th className="py-2.5 px-3">Remarks</th>
                <th className="py-2.5 px-2 text-center w-12">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {(data.kyc_documents || []).map((item, idx) => {
                const itemKey = item.id || `kyc-row-${idx}`;
                return (
                  <tr key={itemKey} className="hover:bg-slate-50/80 transition group">
                    <td className="py-2 px-3 font-medium text-slate-900">
                      <input
                        type="text"
                        value={item.document}
                        placeholder="e.g. GST Certificate, PAN Card..."
                        onChange={(e) => updateKYC(idx, 'document', e.target.value)}
                        className="w-full px-2 py-1.5 rounded-md bg-transparent hover:bg-slate-100 focus:bg-white focus:ring-1 focus:ring-blue-600 focus:outline-hidden transition text-xs font-medium text-slate-900 placeholder:text-slate-400"
                      />
                    </td>
                    <td className="py-2 px-3">
                      <div className="relative inline-block w-full min-w-[110px]">
                        <select
                          value={item.status}
                          onChange={(e) => updateKYC(idx, 'status', e.target.value)}
                          className={`w-full appearance-none pr-8 pl-2.5 py-1.5 rounded-md font-semibold text-[11px] border transition cursor-pointer focus:outline-hidden focus:ring-1 focus:ring-blue-500 ${
                            item.status === 'Available'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : item.status === 'Pending'
                              ? 'bg-amber-50 text-amber-700 border-amber-200'
                              : 'bg-slate-100 text-slate-600 border-slate-200'
                          }`}
                        >
                          <option value="Available">Available</option>
                          <option value="Pending">Pending</option>
                          <option value="Waived">Waived</option>
                        </select>
                        <ChevronDown className={`pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 ${
                          item.status === 'Available' ? 'text-emerald-600' : item.status === 'Pending' ? 'text-amber-600' : 'text-slate-400'
                        }`} />
                      </div>
                    </td>
                    <td className="py-2 px-3 text-slate-600">
                      <input
                        type="text"
                        value={item.source}
                        placeholder="e.g. Rubix BIR / Customer"
                        onChange={(e) => updateKYC(idx, 'source', e.target.value)}
                        className="w-full px-2 py-1.5 rounded-md bg-transparent hover:bg-slate-100 focus:bg-white focus:ring-1 focus:ring-blue-600 focus:outline-hidden transition text-xs text-slate-700 placeholder:text-slate-400"
                      />
                    </td>
                    <td className="py-2 px-3 text-slate-600">
                      <input
                        type="text"
                        value={item.remarks}
                        placeholder="e.g. Verified via portal"
                        onChange={(e) => updateKYC(idx, 'remarks', e.target.value)}
                        className="w-full px-2 py-1.5 rounded-md bg-transparent hover:bg-slate-100 focus:bg-white focus:ring-1 focus:ring-blue-600 focus:outline-hidden transition text-xs text-slate-700 placeholder:text-slate-400"
                      />
                    </td>
                    <td className="py-2 px-2 text-center">
                      <button
                        type="button"
                        onClick={() => deleteKYCItem(idx)}
                        title="Remove document row"
                        aria-label={`Remove ${item.document || 'document row'}`}
                        className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition cursor-pointer"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Add Custom Document Action */}
        <div className="mt-3 flex items-center justify-between pt-2 border-t border-slate-100">
          <button
            type="button"
            onClick={addKYCItem}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Custom Document</span>
          </button>
          <span className="text-[11px] text-slate-400">
            {(data.kyc_documents || []).length} document{(data.kyc_documents || []).length === 1 ? '' : 's'} in checklist
          </span>
        </div>
      </div>

      {/* 5. Sign-off & Audit Meta Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <div className="flex items-center space-x-2 text-sm font-bold text-slate-800 mb-4 pb-2 border-b border-slate-100">
          <Award className="w-4 h-4 text-blue-600" />
          <span>5. Credit Approval & Sign-Off Matrix</span>
        </div>

        <div className="space-y-4">
          {/* Email Approval Reference Field */}
          <div className="bg-slate-50/70 border border-slate-200/80 rounded-lg p-3.5">
            <div className="flex items-center space-x-2 mb-1.5">
              <MailCheck className="w-4 h-4 text-blue-600" />
              <label className="text-xs font-bold text-slate-700">
                Email Approval Reference / Sanction Note (e.g., Approved via email by Director on 10/11/2026)
              </label>
            </div>
            <input
              type="text"
              value={data.mail_approval || ''}
              onChange={(e) => onChange({ mail_approval: e.target.value })}
              placeholder="e.g. Email approval from Director Mr. XYZ dated 10-Nov-2026"
              className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 bg-white placeholder:text-slate-400 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1 transition"
            />
            <p className="text-[11px] text-slate-500 mt-1.5">
              If approved over email, this reference replaces the physical signature in the generated memorandum.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Created / Reviewed By</label>
              <input
                type="text"
                value={data.created_by}
                onChange={(e) => onChange({ created_by: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Checked & Audited By</label>
              <input
                type="text"
                value={data.checked_by}
                onChange={(e) => onChange({ checked_by: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Approved By</label>
              <input
                type="text"
                value={data.approved_by}
                onChange={(e) => onChange({ approved_by: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Approval / Memo Date</label>
              <input
                type="text"
                value={data.appraisal_date}
                onChange={(e) => onChange({ appraisal_date: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1 transition"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Action Footer */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
        <div className="text-xs text-slate-500">
          Ready to export official <strong>Credit Approval Memorandum (CRIF Format .docx)</strong>
        </div>
        <button
          onClick={onGenerate}
          disabled={isGenerating}
          className="flex items-center space-x-2.5 px-6 py-3 rounded-xl bg-blue-700 hover:bg-blue-800 text-white font-bold text-sm shadow-sm hover:shadow-md transition disabled:opacity-50 cursor-pointer focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Generating Credit Memo...</span>
            </>
          ) : (
            <>
              <Download className="w-5 h-5" />
              <span>Generate & Download Credit Memo (.docx)</span>
              <kbd className="hidden sm:inline-block ml-1 px-1.5 py-0.5 text-[10px] bg-blue-800/80 rounded border border-blue-600 text-blue-200">
                ⌘↵
              </kbd>
            </>
          )}
        </button>
      </div>

    </div>
  );
};
