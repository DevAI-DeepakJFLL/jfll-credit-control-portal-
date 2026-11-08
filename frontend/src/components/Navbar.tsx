import React from 'react';
import { FileText, History, PlusCircle } from 'lucide-react';

interface NavbarProps {
  currentTab: 'create' | 'history';
  setCurrentTab: (tab: 'create' | 'history') => void;
  onReset: () => void;
  hasData: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, setCurrentTab, onReset, hasData }) => {
  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Left: Brand Identity */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setCurrentTab('create')}>
          <img
            src="/jfll-logo.jpeg"
            alt="Jet Freight Logistics Limited"
            className="w-10 h-10 rounded-lg object-contain bg-white p-0.5 shadow-sm border border-slate-700/50"
          />
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-base tracking-tight text-white">JET FREIGHT LOGISTICS</span>
              <span className="bg-emerald-500/20 text-emerald-400 text-xs px-2 py-0.5 rounded-full font-medium border border-emerald-500/30">
                Credit Control
              </span>
            </div>
            <p className="text-xs text-slate-400">Credit Risk Underwriting & Sanction Portal</p>
          </div>
        </div>

        {/* Right: Actions and Tabs */}
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setCurrentTab('create')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold cursor-pointer focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-400 transition-all ${
              currentTab === 'create'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Credit Assessment</span>
          </button>

          <button
            onClick={() => setCurrentTab('history')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold cursor-pointer focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-400 transition-all ${
              currentTab === 'history'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <History className="w-4 h-4" />
            <span>Credit Memo Records</span>
          </button>

          {hasData && (
            <button
              onClick={onReset}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-700 transition cursor-pointer focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-400"
              title="Upload another customer report"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>New Customer Check</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
