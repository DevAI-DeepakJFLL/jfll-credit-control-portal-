import React, { useState } from 'react';
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
  Clock 
} from 'lucide-react';

export const AgeingReportView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'upload' | 'dashboard' | 'customers'>('upload');
  const [selectedBranch, setSelectedBranch] = useState<string>('all');
  const [selectedFUPerson, setSelectedFUPerson] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [, setHasData] = useState<boolean>(false);

  // Sample initial metrics for preview
  const sampleMetrics = {
    totalOutstanding: '₹ 14.82 Cr',
    totalOverdue: '₹ 8.45 Cr',
    thisIATA: '₹ 3.12 Cr',
    lastIATA: '₹ 1.84 Cr',
    critical365: '₹ 94.20 Lacs',
    totalCustomers: 432
  };

  const handleSimulateUpload = () => {
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
      setHasData(true);
      setActiveTab('dashboard');
    }, 1200);
  };

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
                  ERP AR Pipeline
                </span>
              </div>
              <p className="text-xs text-slate-500">Master AR transaction aggregation, dynamic age bucketing, follow-up mapping & automated Excel compilation</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
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

      {/* Main Workspace Body */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* KPI Metric Summary Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-8">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-1">
              <span className="text-xs font-medium">Total Receivables</span>
              <Building2 className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-xl font-bold text-slate-900">{sampleMetrics.totalOutstanding}</div>
            <p className="text-[11px] text-slate-400 mt-1">432 Active Debtors</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-1">
              <span className="text-xs font-medium">Overdue Exposure</span>
              <AlertTriangle className="w-4 h-4 text-amber-500" />
            </div>
            <div className="text-xl font-bold text-amber-700">{sampleMetrics.totalOverdue}</div>
            <p className="text-[11px] text-amber-600/80 mt-1">57.1% of Total Ledger</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-1">
              <span className="text-xs font-medium">This IATA Cycle (31-45d)</span>
              <Clock className="w-4 h-4 text-blue-500" />
            </div>
            <div className="text-xl font-bold text-blue-700">{sampleMetrics.thisIATA}</div>
            <p className="text-[11px] text-blue-600/80 mt-1">Immediate Settlement Focus</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 mb-1">
              <span className="text-xs font-medium">Last IATA (46-60d)</span>
              <Clock className="w-4 h-4 text-indigo-500" />
            </div>
            <div className="text-xl font-bold text-indigo-700">{sampleMetrics.lastIATA}</div>
            <p className="text-[11px] text-indigo-600/80 mt-1">Follow-Up Escalation</p>
          </div>

          <div className="bg-white p-4 rounded-xl border border-rose-200 bg-rose-50/30 shadow-xs col-span-2 md:col-span-4 lg:col-span-1">
            <div className="flex items-center justify-between text-rose-600 mb-1">
              <span className="text-xs font-medium">Critical (&gt;365 Days)</span>
              <AlertTriangle className="w-4 h-4 text-rose-600" />
            </div>
            <div className="text-xl font-bold text-rose-700">{sampleMetrics.critical365}</div>
            <p className="text-[11px] text-rose-600/80 mt-1">Legal / Bad Debt Review</p>
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
                Upload your raw ERP Accounts Receivable transaction export (<code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">MASTER FILE - Copy.xlsx</code>). The engine will parse transaction rows, compute aging buckets, map follow-up personnel, and generate executive summaries with zero formula errors.
              </p>
            </div>

            <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-blue-500 hover:bg-blue-50/20 transition cursor-pointer">
              <FileSpreadsheet className="w-10 h-10 text-slate-400 mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-700">Drag & drop your Master AR Excel file here</p>
              <p className="text-xs text-slate-400 mt-1">Supports .xlsx and .xlsm formats (Posting Date / Due Date analysis)</p>
              <button
                onClick={handleSimulateUpload}
                disabled={isProcessing}
                className="mt-5 inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer disabled:opacity-50"
              >
                {isProcessing ? (
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
          </div>
        )}

        {/* Tab 2: Ageing Dashboard / Buckets */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Ageing Bucket Breakdown</h3>
                <p className="text-xs text-slate-500">Accounts Receivable distributed across credit payment tenors</p>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Final Ageing Excel (.xlsx)</span>
                </button>
              </div>
            </div>

            {/* Bucket Cards Visualization */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
              {[
                { label: '0-30 Days', amt: '₹ 6.37 Cr', pct: '43.0%', color: 'bg-emerald-50 border-emerald-200 text-emerald-800' },
                { label: '31-45 Days', amt: '₹ 3.12 Cr', pct: '21.1%', color: 'bg-blue-50 border-blue-200 text-blue-800' },
                { label: '46-60 Days', amt: '₹ 1.84 Cr', pct: '12.4%', color: 'bg-indigo-50 border-indigo-200 text-indigo-800' },
                { label: '61-90 Days', amt: '₹ 1.15 Cr', pct: '7.8%', color: 'bg-amber-50 border-amber-200 text-amber-800' },
                { label: '91-180 Days', amt: '₹ 88.5 L', pct: '6.0%', color: 'bg-orange-50 border-orange-200 text-orange-800' },
                { label: '181-240 Days', amt: '₹ 32.1 L', pct: '2.2%', color: 'bg-rose-50 border-rose-200 text-rose-800' },
                { label: '241-365 Days', amt: '₹ 19.4 L', pct: '1.3%', color: 'bg-rose-100 border-rose-300 text-rose-900' },
                { label: '> 365 Days', amt: '₹ 94.2 L', pct: '6.4%', color: 'bg-red-100 border-red-300 text-red-950 font-bold' }
              ].map((b, idx) => (
                <div key={idx} className={`p-3 rounded-xl border ${b.color} flex flex-col justify-between`}>
                  <span className="text-[11px] font-semibold">{b.label}</span>
                  <div className="my-2">
                    <span className="text-sm font-bold block">{b.amt}</span>
                    <span className="text-[10px] opacity-75">{b.pct} share</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Branch-wise Distribution Overview */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4">Branch Ledger Exposure</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { branch: 'Mumbai Hub', outstanding: '₹ 9.15 Cr', overdue: '₹ 4.82 Cr', share: '61.7%' },
                  { branch: 'Delhi (DEL)', outstanding: '₹ 3.42 Cr', overdue: '₹ 2.15 Cr', share: '23.1%' },
                  { branch: 'Ahmedabad (AMD)', outstanding: '₹ 1.25 Cr', overdue: '₹ 88.2 L', share: '8.4%' },
                  { branch: 'Kerala & South', outstanding: '₹ 62.4 L', overdue: '₹ 38.1 L', share: '4.2%' },
                  { branch: 'Bangalore (BLR)', outstanding: '₹ 24.1 L', overdue: '₹ 14.5 L', share: '1.6%' },
                  { branch: 'Other Seaports', outstanding: '₹ 14.0 L', overdue: '₹ 7.2 L', share: '1.0%' }
                ].map((item, idx) => (
                  <div key={idx} className="p-3.5 rounded-lg border border-slate-100 bg-slate-50/50 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-bold text-slate-800">{item.branch}</p>
                      <p className="text-[11px] text-slate-500">Overdue: {item.overdue}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-bold text-blue-700">{item.outstanding}</p>
                      <span className="text-[10px] text-slate-400">{item.share}</span>
                    </div>
                  </div>
                ))}
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
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by customer name, voucher or representative..."
                    className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-800 bg-white focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-500"
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <select
                    value={selectedBranch}
                    onChange={(e) => setSelectedBranch(e.target.value)}
                    className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-700 bg-white"
                  >
                    <option value="all">All Branches</option>
                    <option value="Mumbai">Mumbai</option>
                    <option value="Delhi">Delhi</option>
                    <option value="Ahmedabad">Ahmedabad</option>
                    <option value="Kerala">Kerala</option>
                  </select>

                  <select
                    value={selectedFUPerson}
                    onChange={(e) => setSelectedFUPerson(e.target.value)}
                    className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-700 bg-white"
                  >
                    <option value="all">All Follow-Up Persons</option>
                    <option value="Siddhesh">Siddhesh</option>
                    <option value="Nikita">Nikita</option>
                    <option value="Vaibhav">Vaibhav</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <button
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export Filtered Table</span>
              </button>
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
                    <th className="py-2.5 px-3">Remark</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {[
                    { fu: 'Other', customer: 'A ENTERPRISES HOLDING INC.', branch: 'Mumbai', sales: 'Sweety Soni', out: '₹ 10.49 Cr', thisIata: '₹ 0', lastIata: '₹ 0', above90: '₹ 10.49 Cr', remark: 'As per confirm 25 Lacs' },
                    { fu: 'Siddhesh', customer: 'FAIR EXPORTS (I) PVT LTD.', branch: 'Mumbai', sales: 'Irfan Shaikh', out: '₹ 1.15 Cr', thisIata: '₹ 82.4 L', lastIata: '₹ 32.1 L', above90: '₹ 0', remark: 'Payment scheduled this week' },
                    { fu: 'Siddhesh', customer: 'DHARAMPAL SATYAPAL LIMITED', branch: 'Mumbai', sales: 'Irfan Shaikh', out: '₹ 1.02 Cr', thisIata: '₹ 54.0 L', lastIata: '₹ 47.8 L', above90: '₹ 0', remark: 'Regular paying client' },
                    { fu: 'Nikita', customer: 'FLOMIC GLOBAL LOGISTICS LIMITED', branch: 'Mumbai', sales: 'Narendra Gupta', out: '₹ 83.1 L', thisIata: '₹ 45.2 L', lastIata: '₹ 22.0 L', above90: '₹ 15.9 L', remark: 'Cheque issued' },
                    { fu: 'Vaibhav', customer: 'COMMITTED CARGO SOLUTIONS PVT LTD', branch: 'Delhi', sales: 'Rahul Vasawa', out: '₹ 74.1 L', thisIata: '₹ 38.0 L', lastIata: '₹ 20.1 L', above90: '₹ 16.0 L', remark: 'Follow up done on 11-Nov' }
                  ].map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition">
                      <td className="py-2.5 px-3 font-semibold text-slate-800">{row.fu}</td>
                      <td className="py-2.5 px-3 font-semibold text-slate-900">{row.customer}</td>
                      <td className="py-2.5 px-3">{row.branch}</td>
                      <td className="py-2.5 px-3">{row.sales}</td>
                      <td className="py-2.5 px-3 text-right font-bold text-slate-900">{row.out}</td>
                      <td className="py-2.5 px-3 text-right text-blue-700 font-semibold">{row.thisIata}</td>
                      <td className="py-2.5 px-3 text-right text-indigo-700 font-semibold">{row.lastIata}</td>
                      <td className="py-2.5 px-3 text-right text-rose-700 font-semibold">{row.above90}</td>
                      <td className="py-2.5 px-3 text-slate-500 italic max-w-xs truncate">{row.remark}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
