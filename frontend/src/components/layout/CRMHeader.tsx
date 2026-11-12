import React from 'react';
import { CRMAutomationId } from '../../types/shared';
import { ShieldCheck, CalendarClock, BellRing } from 'lucide-react';

interface CRMHeaderProps {
  activeAutomation: CRMAutomationId;
  setActiveAutomation: (id: CRMAutomationId) => void;
}

export const CRMHeader: React.FC<CRMHeaderProps> = ({ activeAutomation, setActiveAutomation }) => {
  const automations = [
    {
      id: 'credit-appraisal' as CRMAutomationId,
      label: 'Credit Appraisal',
      badge: 'CRIF & Rubix',
      icon: ShieldCheck,
      description: 'Underwriting assessment & 1-page memo'
    },
    {
      id: 'ageing-report' as CRMAutomationId,
      label: 'Ageing Report',
      badge: 'New',
      icon: CalendarClock,
      description: 'AR ledger bucketing & follow-up compiler'
    },
    {
      id: 'dunning-exposure' as CRMAutomationId,
      label: 'Dunning & Risk',
      badge: 'Coming Soon',
      icon: BellRing,
      description: 'Payment alerts & overdue dunning',
      disabled: true
    }
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="h-16 flex items-center justify-between">
          
          {/* Left: Brand Identity */}
          <div className="flex items-center space-x-3.5">
            <img
              src="/jfll-logo.jpeg"
              alt="Jet Freight Logistics Limited"
              className="w-10 h-10 rounded-lg object-contain bg-white p-0.5 shadow-xs border border-slate-700/60"
            />
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-base tracking-tight text-white">JET FREIGHT LOGISTICS</span>
                <span className="bg-blue-500/20 text-blue-400 text-[11px] px-2 py-0.5 rounded-full font-semibold border border-blue-500/30">
                  Credit Control CRM
                </span>
              </div>
              <p className="text-xs text-slate-400">Departmental Automation & Underwriting Hub</p>
            </div>
          </div>

          {/* Right: Operational Status Indicator */}
          <div className="hidden md:flex items-center space-x-3 text-xs text-slate-400">
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-medium text-[11px]">System Online</span>
            </div>
          </div>
        </div>

        {/* Global CRM Automation Switcher Tabs */}
        <div className="flex space-x-1 overflow-x-auto no-scrollbar border-t border-slate-800/80">
          {automations.map((item) => {
            const Icon = item.icon;
            const isActive = activeAutomation === item.id;
            return (
              <button
                key={item.id}
                disabled={item.disabled}
                onClick={() => !item.disabled && setActiveAutomation(item.id)}
                className={`relative flex items-center space-x-2 px-4 py-2.5 text-xs font-semibold transition cursor-pointer ${
                  isActive
                    ? 'text-white font-bold bg-slate-800/80'
                    : item.disabled
                    ? 'text-slate-500 cursor-not-allowed opacity-60'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/40'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
                {item.badge && (
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold ${
                      item.badge === 'New'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : item.badge === 'Coming Soon'
                        ? 'bg-slate-800 text-slate-400 border border-slate-700'
                        : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
                )}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
