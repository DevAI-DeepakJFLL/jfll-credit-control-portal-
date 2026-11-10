import React from 'react';
import { IndianRupee, Clock, AlertTriangle, UserCheck, Pencil } from 'lucide-react';
import { RubixExtractedData } from '../types';

interface MetricCardsProps {
  data: RubixExtractedData;
  onChange: (updated: Partial<RubixExtractedData>) => void;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ data, onChange }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      
      {/* 1. Sanctioned Credit Limit */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs relative overflow-hidden group hover:border-blue-400 transition">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[11px] font-semibold tracking-wider text-slate-500 uppercase">Sanctioned Credit Limit</span>
          <div className="flex items-center space-x-1.5">
            <span className="text-[10px] text-slate-400 font-medium hidden group-hover:inline-block transition">Edit</span>
            <span className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
              <IndianRupee className="w-4 h-4" />
            </span>
          </div>
        </div>
        <div className="mt-1 relative">
          <input
            type="text"
            value={data.crif_credit_limit}
            onChange={(e) => onChange({ crif_credit_limit: e.target.value })}
            className="text-xl font-extrabold text-blue-900 px-2 py-1 -mx-2 rounded-lg bg-transparent hover:bg-slate-50 focus:bg-white border border-transparent hover:border-slate-300 focus:border-blue-600 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600/30 w-full tabular-nums transition"
          />
        </div>
        <div className="text-[11px] text-slate-500 mt-1.5 pt-1.5 border-t border-slate-100 flex items-center justify-between">
          <span className="text-slate-400">Bureau Suggested:</span>
          <span className="font-semibold text-slate-700">
            {data.rubix_credit_limit_lakhs > 0
              ? `₹ ${data.rubix_credit_limit_lakhs} Lakhs`
              : data.crif_credit_limit !== '₹ 0.00'
              ? data.crif_credit_limit
              : 'Manual Underwriting'}
          </span>
        </div>
      </div>

      {/* 2. Approved Credit Period (Tenor) */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs relative overflow-hidden group hover:border-blue-400 transition">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[11px] font-semibold tracking-wider text-slate-500 uppercase">Approved Credit Period</span>
          <div className="flex items-center space-x-1.5">
            <span className="text-[10px] text-slate-400 font-medium hidden group-hover:inline-block transition">Edit</span>
            <span className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
              <Clock className="w-4 h-4" />
            </span>
          </div>
        </div>
        <div className="mt-1">
          <input
            type="text"
            value={data.approved_credit_days}
            onChange={(e) => onChange({ approved_credit_days: e.target.value })}
            className="text-xl font-extrabold text-slate-900 px-2 py-1 -mx-2 rounded-lg bg-transparent hover:bg-slate-50 focus:bg-white border border-transparent hover:border-slate-300 focus:border-blue-600 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600/30 w-full transition"
          />
        </div>
        <div className="text-[11px] text-slate-500 mt-1.5 pt-1.5 border-t border-slate-100 flex items-center justify-between">
          <span className="text-slate-400">Bureau Suggested:</span>
          <span className="font-semibold text-slate-700">{data.recommended_credit_days} Days</span>
        </div>
      </div>

      {/* 3. Bureau Risk Rating */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs relative overflow-hidden">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
            {data.bureau_source?.includes('CRIF') ? 'CRIF Rating' : 'Rubix Risk Grade'}
          </span>
          <span className="p-1.5 rounded-lg bg-amber-50 text-amber-600">
            <AlertTriangle className="w-4 h-4" />
          </span>
        </div>
        <div className="mt-1 flex items-baseline space-x-2">
          <span className="text-xl font-extrabold text-amber-600">{data.risk_grade}</span>
          <span className="text-sm font-semibold text-slate-500">(Score: {data.risk_score}/100)</span>
        </div>
        <div className="text-[11px] text-slate-500 mt-1.5 pt-1.5 border-t border-slate-100 truncate" title={data.risk_description}>
          {data.risk_description}
        </div>
      </div>

      {/* 4. Sales Executive / Account Manager */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs relative overflow-hidden group hover:border-blue-400 transition">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[11px] font-semibold tracking-wider text-slate-500 uppercase">Sales Executive</span>
          <div className="flex items-center space-x-1.5">
            <Pencil className="w-3 h-3 text-slate-400 group-hover:text-blue-600 transition" />
            <span className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">
              <UserCheck className="w-4 h-4" />
            </span>
          </div>
        </div>
        <div className="mt-1">
          <input
            type="text"
            placeholder="Enter sales executive..."
            value={data.salesperson}
            onChange={(e) => onChange({ salesperson: e.target.value })}
            className="text-base font-bold text-slate-900 px-2 py-1 -mx-2 rounded-lg bg-transparent hover:bg-slate-50 focus:bg-white border border-transparent hover:border-slate-300 focus:border-blue-600 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600/30 w-full transition placeholder:text-slate-400"
          />
        </div>
        <div className="text-[11px] text-slate-500 mt-1.5 pt-1.5 border-t border-slate-100">
          Commercial Account Representative
        </div>
      </div>

    </div>
  );
};
