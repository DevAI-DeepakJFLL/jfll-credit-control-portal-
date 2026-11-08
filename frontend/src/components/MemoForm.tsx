import React from 'react';
import { Building2, FileCheck2, ShieldAlert, Award, Download, Loader2, CheckSquare } from 'lucide-react';
import { RubixExtractedData, KYCItem } from '../types';

interface MemoFormProps {
  data: RubixExtractedData;
  onChange: (updated: Partial<RubixExtractedData>) => void;
  onGenerate: () => void;
  isGenerating: boolean;
}

export const MemoForm: React.FC<MemoFormProps> = ({ data, onChange, onGenerate, isGenerating }) => {
  const updateKYC = (index: number, field: keyof KYCItem, value: string) => {
    const updated = [...data.kyc_documents];
    updated[index] = { ...updated[index], [field]: value };
    onChange({ kyc_documents: updated });
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
            <select
              value={data.type_of_company}
              onChange={(e) => onChange({ type_of_company: e.target.value })}
              className="w-full px-3.5 py-2 rounded-lg border border-slate-300 text-sm text-slate-800 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1 bg-white transition"
            >
              <option value="Proprietorship">Proprietorship</option>
              <option value="Partnership">Partnership</option>
              <option value="PRIVATE LIMITED">PRIVATE LIMITED</option>
              <option value="Public Limited">Public Limited</option>
              <option value="LLP">Limited Liability Partnership (LLP)</option>
            </select>
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

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">IATA Air Freight Tenor</label>
            <select
              value={data.iata_credit_days}
              onChange={(e) => onChange({ iata_credit_days: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 bg-white focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1 transition"
            >
              <option value="15 Days">15 Days (Strict CASS)</option>
              <option value="21 Days">21 Days (Rubix Aligned)</option>
              <option value="30 Days">30 Days (Extended)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Ocean / Multimodal Tenor</label>
            <select
              value={data.ocean_credit_days}
              onChange={(e) => onChange({ ocean_credit_days: e.target.value })}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs text-slate-800 bg-white focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1 transition"
            >
              <option value="30 Days">30 Days (Standard CSR)</option>
              <option value="45 Days">45 Days (Key Account)</option>
            </select>
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
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.kyc_documents.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50/80 transition">
                  <td className="py-2 px-3 font-medium text-slate-900">
                    <input
                      type="text"
                      value={item.document}
                      onChange={(e) => updateKYC(idx, 'document', e.target.value)}
                      className="w-full px-2 py-1 rounded bg-transparent hover:bg-slate-100 focus:bg-white focus:ring-1 focus:ring-blue-600 focus:outline-hidden transition text-xs"
                    />
                  </td>
                  <td className="py-2 px-3">
                    <select
                      value={item.status}
                      onChange={(e) => updateKYC(idx, 'status', e.target.value)}
                      className={`px-2.5 py-1 rounded font-semibold text-[11px] border transition cursor-pointer ${
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
                  </td>
                  <td className="py-2 px-3 text-slate-600">
                    <input
                      type="text"
                      value={item.source}
                      onChange={(e) => updateKYC(idx, 'source', e.target.value)}
                      className="w-full px-2 py-1 rounded bg-transparent hover:bg-slate-100 focus:bg-white focus:ring-1 focus:ring-blue-600 focus:outline-hidden transition text-xs"
                    />
                  </td>
                  <td className="py-2 px-3 text-slate-600">
                    <input
                      type="text"
                      value={item.remarks}
                      onChange={(e) => updateKYC(idx, 'remarks', e.target.value)}
                      className="w-full px-2 py-1 rounded bg-transparent hover:bg-slate-100 focus:bg-white focus:ring-1 focus:ring-blue-600 focus:outline-hidden transition text-xs"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. Sign-off & Audit Meta Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <div className="flex items-center space-x-2 text-sm font-bold text-slate-800 mb-4 pb-2 border-b border-slate-100">
          <Award className="w-4 h-4 text-blue-600" />
          <span>5. Credit Approval & Sign-Off Matrix</span>
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
