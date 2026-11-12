import React from 'react';
import { Menu, ChevronRight } from 'lucide-react';
import { CRMAutomationId } from '../../types/shared';

interface CRMMastheadProps {
  activeAutomation: CRMAutomationId;
  creditSubTab: 'create' | 'history';
  ageingSubTab: 'upload' | 'dashboard' | 'customers';
  onOpenMobileSidebar: () => void;
}

export const CRMMasthead: React.FC<CRMMastheadProps> = ({
  activeAutomation,
  creditSubTab,
  ageingSubTab,
  onOpenMobileSidebar
}) => {
  const getBreadcrumbTitle = () => {
    if (activeAutomation === 'credit-appraisal') {
      return {
        module: 'Credit Appraisal',
        section: creditSubTab === 'create' ? 'Assessment Form' : 'Appraisal History'
      };
    }
    if (activeAutomation === 'ageing-report') {
      const sectionName = 
        ageingSubTab === 'upload' ? 'Upload Master AR Dump' :
        ageingSubTab === 'dashboard' ? 'Ageing Summary' : 'Customer Follow-Up';
      return {
        module: 'Ageing Report',
        section: sectionName
      };
    }
    return {
      module: 'Credit Control CRM',
      section: 'Workspace'
    };
  };

  const breadcrumbs = getBreadcrumbTitle();

  return (
    <header className="h-14 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30 shadow-2xs">
      {/* Left: Mobile Toggle & Breadcrumbs */}
      <div className="flex items-center space-x-3">
        <button
          onClick={onOpenMobileSidebar}
          className="md:hidden p-1.5 rounded-md text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition cursor-pointer"
          aria-label="Open navigation sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-2 text-xs">
          <span className="font-semibold text-slate-500">Credit CRM</span>
          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          <span className="font-semibold text-slate-700">{breadcrumbs.module}</span>
          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          <span className="font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-100">
            {breadcrumbs.section}
          </span>
        </div>
      </div>

      {/* Right: Operational Status Indicator */}
      <div className="flex items-center space-x-3 text-xs">
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-700">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-medium text-[11px] text-slate-700">System Online</span>
        </div>
      </div>
    </header>
  );
};
