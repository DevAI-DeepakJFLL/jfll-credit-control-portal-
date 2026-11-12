import React from 'react';
import { CRMAutomationId } from '../../types/shared';
import { 
  ShieldCheck, 
  CalendarClock, 
  BellRing, 
  FileText, 
  History, 
  UploadCloud, 
  TrendingUp, 
  Users, 
  ChevronDown, 
  ChevronRight, 
  PanelLeftClose, 
  PanelLeft, 
  X,
  ExternalLink
} from 'lucide-react';

interface CRMSidebarProps {
  activeAutomation: CRMAutomationId;
  setActiveAutomation: (id: CRMAutomationId) => void;
  creditSubTab: 'create' | 'history';
  setCreditSubTab: (tab: 'create' | 'history') => void;
  ageingSubTab: 'upload' | 'dashboard' | 'customers';
  setAgeingSubTab: (tab: 'upload' | 'dashboard' | 'customers') => void;
  isCollapsed: boolean;
  setIsCollapsed: React.Dispatch<React.SetStateAction<boolean>>;
  isMobileOpen: boolean;
  setIsMobileOpen: (open: boolean) => void;
}

export const CRMSidebar: React.FC<CRMSidebarProps> = ({
  activeAutomation,
  setActiveAutomation,
  creditSubTab,
  setCreditSubTab,
  ageingSubTab,
  setAgeingSubTab,
  isCollapsed,
  setIsCollapsed,
  isMobileOpen,
  setIsMobileOpen
}) => {
  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isMobileOpen && (
        <div 
          onClick={() => setIsMobileOpen(false)}
          className="fixed inset-0 bg-slate-900/60 z-40 md:hidden backdrop-blur-xs transition-opacity"
        />
      )}

      {/* WordPress-Style Dark Sidebar */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 bg-[#1e2327] text-slate-200 border-r border-[#2c3338] flex flex-col transition-all duration-200 ease-in-out ${
          isMobileOpen ? 'translate-x-0 w-64' : '-translate-x-full md:translate-x-0'
        } ${isCollapsed ? 'md:w-16' : 'md:w-64'}`}
      >
        {/* Sidebar Brand Header */}
        <div className="h-16 flex items-center justify-between px-3.5 border-b border-[#2c3338] bg-[#15191c]">
          <div 
            onClick={() => {
              setActiveAutomation('credit-appraisal');
              setCreditSubTab('create');
            }}
            className="flex items-center space-x-3 cursor-pointer overflow-hidden"
          >
            <img
              src="/jfll-logo.jpeg"
              alt="Jet Freight Logistics Limited"
              className="w-9 h-9 rounded-md object-contain bg-white p-0.5 shrink-0 shadow-xs border border-slate-700/60"
            />
            {!isCollapsed && (
              <div className="min-w-0">
                <span className="font-bold text-xs tracking-wide text-white block truncate">
                  JET FREIGHT
                </span>
                <span className="text-[10px] text-blue-400 font-semibold tracking-wider uppercase block truncate">
                  Credit Control CRM
                </span>
              </div>
            )}
          </div>

          {/* Mobile Close Button */}
          <button
            onClick={() => setIsMobileOpen(false)}
            className="md:hidden p-1.5 text-slate-400 hover:text-white rounded-md transition"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Sidebar Navigation Menu Items */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-1.5 text-xs font-medium">
          {!isCollapsed && (
            <div className="px-2 pb-1 text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Department Automations
            </div>
          )}

          {/* ITEM 1: Credit Appraisal */}
          <div>
            <button
              onClick={() => setActiveAutomation('credit-appraisal')}
              className={`w-full flex items-center justify-between px-2.5 py-2.5 rounded-md transition cursor-pointer ${
                activeAutomation === 'credit-appraisal'
                  ? 'bg-[#2271b1] text-white font-bold shadow-xs'
                  : 'text-slate-300 hover:bg-[#2c3338] hover:text-white'
              }`}
              title="Credit Appraisal Memorandum (CRIF & Rubix)"
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <ShieldCheck className="w-4 h-4 shrink-0 text-blue-300" />
                {!isCollapsed && (
                  <span className="truncate">Credit Appraisal</span>
                )}
              </div>
              {!isCollapsed && (
                <div className="flex items-center space-x-1 shrink-0">
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-900/60 text-blue-200 border border-blue-400/30">
                    CAM
                  </span>
                  {activeAutomation === 'credit-appraisal' ? (
                    <ChevronDown className="w-3.5 h-3.5 text-white/80" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                  )}
                </div>
              )}
            </button>

            {/* Sub-items for Credit Appraisal */}
            {activeAutomation === 'credit-appraisal' && !isCollapsed && (
              <div className="ml-5 mt-1 pl-2.5 border-l border-slate-700/80 space-y-1 py-1">
                <button
                  onClick={() => setCreditSubTab('create')}
                  className={`w-full flex items-center space-x-2 px-2 py-1.5 rounded-md text-[11px] transition cursor-pointer ${
                    creditSubTab === 'create'
                      ? 'text-white font-bold bg-[#2c3338]'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#2c3338]/50'
                  }`}
                >
                  <FileText className="w-3.5 h-3.5 text-slate-400" />
                  <span>Assessment Form</span>
                </button>
                <button
                  onClick={() => setCreditSubTab('history')}
                  className={`w-full flex items-center space-x-2 px-2 py-1.5 rounded-md text-[11px] transition cursor-pointer ${
                    creditSubTab === 'history'
                      ? 'text-white font-bold bg-[#2c3338]'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#2c3338]/50'
                  }`}
                >
                  <History className="w-3.5 h-3.5 text-slate-400" />
                  <span>Appraisal History</span>
                </button>
              </div>
            )}
          </div>

          {/* ITEM 2: Ageing Report */}
          <div>
            <button
              onClick={() => setActiveAutomation('ageing-report')}
              className={`w-full flex items-center justify-between px-2.5 py-2.5 rounded-md transition cursor-pointer ${
                activeAutomation === 'ageing-report'
                  ? 'bg-[#2271b1] text-white font-bold shadow-xs'
                  : 'text-slate-300 hover:bg-[#2c3338] hover:text-white'
              }`}
              title="Accounts Receivable Ageing Report"
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <CalendarClock className="w-4 h-4 shrink-0 text-emerald-300" />
                {!isCollapsed && (
                  <span className="truncate">Ageing Report</span>
                )}
              </div>
              {!isCollapsed && (
                <div className="flex items-center space-x-1 shrink-0">
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    New
                  </span>
                  {activeAutomation === 'ageing-report' ? (
                    <ChevronDown className="w-3.5 h-3.5 text-white/80" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                  )}
                </div>
              )}
            </button>

            {/* Sub-items for Ageing Report */}
            {activeAutomation === 'ageing-report' && !isCollapsed && (
              <div className="ml-5 mt-1 pl-2.5 border-l border-slate-700/80 space-y-1 py-1">
                <button
                  onClick={() => setAgeingSubTab('upload')}
                  className={`w-full flex items-center space-x-2 px-2 py-1.5 rounded-md text-[11px] transition cursor-pointer ${
                    ageingSubTab === 'upload'
                      ? 'text-white font-bold bg-[#2c3338]'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#2c3338]/50'
                  }`}
                >
                  <UploadCloud className="w-3.5 h-3.5 text-slate-400" />
                  <span>Upload AR Dump</span>
                </button>
                <button
                  onClick={() => setAgeingSubTab('dashboard')}
                  className={`w-full flex items-center space-x-2 px-2 py-1.5 rounded-md text-[11px] transition cursor-pointer ${
                    ageingSubTab === 'dashboard'
                      ? 'text-white font-bold bg-[#2c3338]'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#2c3338]/50'
                  }`}
                >
                  <TrendingUp className="w-3.5 h-3.5 text-slate-400" />
                  <span>Ageing Summary</span>
                </button>
                <button
                  onClick={() => setAgeingSubTab('customers')}
                  className={`w-full flex items-center space-x-2 px-2 py-1.5 rounded-md text-[11px] transition cursor-pointer ${
                    ageingSubTab === 'customers'
                      ? 'text-white font-bold bg-[#2c3338]'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#2c3338]/50'
                  }`}
                >
                  <Users className="w-3.5 h-3.5 text-slate-400" />
                  <span>Customer Follow-Up</span>
                </button>
              </div>
            )}
          </div>

          {/* ITEM 3: Dunning & Risk (Disabled / Roadmap) */}
          <div>
            <button
              disabled
              className="w-full flex items-center justify-between px-2.5 py-2.5 rounded-md text-slate-500 cursor-not-allowed opacity-60"
              title="Automated Customer Dunning & Exposure Alerts"
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <BellRing className="w-4 h-4 shrink-0 text-slate-500" />
                {!isCollapsed && (
                  <span className="truncate">Dunning & Risk</span>
                )}
              </div>
              {!isCollapsed && (
                <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-500 border border-slate-700">
                  Soon
                </span>
              )}
            </button>
          </div>

          {/* Section: External / Docs */}
          {!isCollapsed && (
            <div className="pt-4 px-2 pb-1 text-[10px] font-bold uppercase tracking-wider text-slate-400">
              System & Reference
            </div>
          )}

          <a
            href="/api/health"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full flex items-center justify-between px-2.5 py-2 rounded-md text-slate-400 hover:text-white hover:bg-[#2c3338] transition cursor-pointer text-xs"
            title="FastAPI System Health & Metadata"
          >
            <div className="flex items-center space-x-2.5 min-w-0">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              {!isCollapsed && <span>API Health</span>}
            </div>
            {!isCollapsed && <ExternalLink className="w-3 h-3 text-slate-500" />}
          </a>
        </nav>

        {/* Sidebar Footer with Collapse Toggle */}
        <div className="p-3 border-t border-[#2c3338] bg-[#15191c] flex items-center justify-between">
          {!isCollapsed && (
            <div className="text-[11px] text-slate-400">
              <p className="font-semibold text-slate-300">Jet Freight v1.2</p>
              <p className="text-[10px] text-slate-400">Credit Control Dept</p>
            </div>
          )}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="hidden md:flex p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-[#2c3338] transition cursor-pointer mx-auto"
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? (
              <PanelLeft className="w-4 h-4" />
            ) : (
              <PanelLeftClose className="w-4 h-4" />
            )}
          </button>
        </div>
      </aside>
    </>
  );
};
