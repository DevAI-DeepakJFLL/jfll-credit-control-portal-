import React, { useEffect, useState, useMemo, useDeferredValue, useCallback } from 'react';
import { Download, Search, FileText, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { AppraisalRecord } from '../types';
import { apiUrl, parseJsonResponse } from '../../../config/api';

export const AppraisalHistory: React.FC = () => {
  const [appraisals, setAppraisals] = useState<AppraisalRecord[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Pagination state: default 10 rows per page
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Non-blocking deferred search for buttery smooth typing
  const deferredSearch = useDeferredValue(search);

  const fetchHistory = useCallback(async (searchQuery?: string) => {
    try {
      setLoading(true);
      setFetchError(null);
      const query = (searchQuery !== undefined ? searchQuery : deferredSearch).trim();
      const endpoint = query
        ? `/api/appraisals?search=${encodeURIComponent(query)}`
        : '/api/appraisals';
      const res = await fetch(apiUrl(endpoint));
      if (!res.ok) {
        const errJson = await parseJsonResponse(res).catch(() => ({ detail: 'Failed to retrieve credit records from server' }));
        throw new Error(errJson.detail || 'Failed to retrieve credit records from server');
      }
      const data = await parseJsonResponse<AppraisalRecord[]>(res);
      setAppraisals(data);
    } catch (err: any) {
      setFetchError(err.message || 'Unable to connect to database');
    } finally {
      setLoading(false);
    }
  }, [deferredSearch]);

  useEffect(() => {
    fetchHistory(deferredSearch);
  }, [deferredSearch, fetchHistory]);

  // O(N) optimized memoized filter: avoids re-evaluating query per record
  const filtered = useMemo(() => {
    const query = deferredSearch.trim().toLowerCase();
    if (!query) return appraisals;
    return appraisals.filter((a) =>
      a.customer_name.toLowerCase().includes(query) ||
      a.salesperson.toLowerCase().includes(query)
    );
  }, [appraisals, deferredSearch]);

  // Reset to page 1 whenever search query changes
  useEffect(() => {
    setCurrentPage(1);
  }, [deferredSearch]);

  // Derived pagination calculations
  const totalItems = filtered.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safeCurrentPage = Math.min(currentPage, totalPages);
  const startIndex = (safeCurrentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalItems);

  const paginatedItems = useMemo(() => {
    return filtered.slice(startIndex, endIndex);
  }, [filtered, startIndex, endIndex]);

  return (
    <div className="max-w-6xl mx-auto my-8 px-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Credit Memo Records & Approval Audit Trail</h2>
          <p className="text-xs text-slate-500 mt-1">
            Searchable ledger of all finalized and sanctioned customer credit memorandums.
          </p>
        </div>

        {/* Search with Deferred Value & Clear Button */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
          <input
            type="text"
            placeholder="Search by customer or sales executive..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-8 py-2 rounded-lg border border-slate-300 text-xs focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1 bg-white transition"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-2.5 top-2.5 p-0.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition cursor-pointer"
              aria-label="Clear search query"
              title="Clear search"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-400 text-xs">Loading records...</div>
      ) : fetchError ? (
        <div className="bg-white rounded-xl border border-rose-200 p-8 text-center">
          <p className="text-xs text-rose-700 font-semibold mb-2">{fetchError}</p>
          <button
            onClick={() => fetchHistory()}
            className="px-3 py-1.5 rounded-lg bg-rose-50 text-rose-700 hover:bg-rose-100 text-xs font-bold border border-rose-200 transition cursor-pointer"
          >
            Retry Connection
          </button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-700">No Credit Memos Found</h3>
          <p className="text-xs text-slate-400 mt-1">
            {search ? 'No customer records match your search criteria.' : 'Upload a customer Rubix report to generate your first credit approval memo.'}
          </p>
          {search && (
            <button
              onClick={() => setSearch('')}
              className="mt-3 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer"
            >
              Clear Search Filter
            </button>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs min-w-[840px]">
              <thead>
                <tr className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                  <th className="py-3.5 px-4 w-20">Memo #</th>
                  <th className="py-3.5 px-4 min-w-[200px]">Customer Name</th>
                  <th className="py-3.5 px-4 min-w-[130px]">Sanctioned Limit</th>
                  <th className="py-3.5 px-4 min-w-[130px]">Credit Terms (Tenor)</th>
                  <th className="py-3.5 px-4 min-w-[140px]">Sales Executive</th>
                  <th className="py-3.5 px-5 min-w-[150px]">Risk Rating</th>
                  <th className="py-3.5 px-4 min-w-[120px]">Sanction Date</th>
                  <th className="py-3.5 px-4 text-center w-20">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {paginatedItems.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3.5 px-4 font-mono text-slate-400">#{item.id}</td>
                    <td className="py-3.5 px-4 font-bold text-slate-900 min-w-[200px] max-w-[280px] truncate" title={item.customer_name}>{item.customer_name}</td>
                    <td className="py-3.5 px-4 font-semibold text-blue-900 tabular-nums">{item.crif_credit_limit}</td>
                    <td className="py-3.5 px-4 text-slate-700">{item.credit_days}</td>
                    <td className="py-3.5 px-4 text-slate-700">{item.salesperson}</td>
                    <td className="py-3.5 px-5 whitespace-nowrap">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md font-semibold text-xs bg-amber-50 text-amber-800 border border-amber-200/80 shadow-2xs">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                        {item.risk_grade}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 whitespace-nowrap">{item.created_at}</td>
                    <td className="py-3.5 px-4 text-center whitespace-nowrap">
                      <a
                        href={apiUrl(`/api/download/${item.access_token || item.id}`)}
                        download
                        aria-label={`Download Credit Memo for ${item.customer_name}`}
                        title={`Download Credit Memo (.docx) for ${item.customer_name}`}
                        className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-blue-600 hover:text-blue-800 bg-blue-50/80 hover:bg-blue-100 border border-blue-200 hover:border-blue-300 shadow-2xs hover:shadow-xs transition-all active:scale-95 cursor-pointer group focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-1"
                      >
                        <Download className="w-4 h-4 text-blue-600 group-hover:translate-y-0.5 transition-transform" />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination & Ledger Stats Footer */}
          <div className="px-4 py-3 bg-slate-50/80 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs text-slate-600">
            <div className="flex items-center gap-1.5">
              <span>
                Showing <strong className="text-slate-900">{totalItems === 0 ? 0 : startIndex + 1}</strong> to <strong className="text-slate-900">{endIndex}</strong> of <strong className="text-slate-900">{totalItems}</strong> records
              </span>
              {deferredSearch && totalItems !== appraisals.length && (
                <span className="text-slate-400">
                  (filtered from {appraisals.length} total)
                </span>
              )}
            </div>

            <div className="flex items-center space-x-4">
              {/* Rows Per Page Dropdown */}
              <div className="flex items-center space-x-1.5">
                <span className="text-slate-500">Rows per page:</span>
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                  className="px-2 py-1 rounded-md border border-slate-300 bg-white text-xs font-semibold text-slate-800 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-600 cursor-pointer shadow-2xs"
                >
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                </select>
              </div>

              {/* Page Navigation Controls */}
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={safeCurrentPage <= 1}
                  className="p-1.5 rounded-md border border-slate-200 bg-white text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition shadow-2xs"
                  title="Previous page"
                  aria-label="Previous page"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                </button>

                <div className="flex items-center space-x-1 px-1">
                  {Array.from({ length: totalPages }, (_, i) => i + 1)
                    .filter((p) => p === 1 || p === totalPages || Math.abs(p - safeCurrentPage) <= 1)
                    .map((p, idx, arr) => {
                      const showEllipsisBefore = idx > 0 && p - arr[idx - 1] > 1;
                      return (
                        <React.Fragment key={p}>
                          {showEllipsisBefore && <span className="text-slate-400 px-1 select-none">…</span>}
                          <button
                            onClick={() => setCurrentPage(p)}
                            className={`w-7 h-7 rounded-md text-xs font-semibold cursor-pointer transition ${
                              safeCurrentPage === p
                                ? 'bg-blue-600 text-white shadow-2xs'
                                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-100'
                            }`}
                          >
                            {p}
                          </button>
                        </React.Fragment>
                      );
                    })}
                </div>

                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={safeCurrentPage >= totalPages}
                  className="p-1.5 rounded-md border border-slate-200 bg-white text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition shadow-2xs"
                  title="Next page"
                  aria-label="Next page"
                >
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
