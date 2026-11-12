import React, { useState } from 'react';
import { CRMSidebar } from './components/layout/CRMSidebar';
import { CRMMasthead } from './components/layout/CRMMasthead';
import { CreditAppraisalView } from './automations/credit-appraisal/CreditAppraisalView';
import { AgeingReportView } from './automations/ageing-report/AgeingReportView';
import { CRMAutomationId } from './types/shared';

export const App: React.FC = () => {
  const getInitialTab = (): CRMAutomationId => {
    try {
      const params = new URLSearchParams(window.location.search);
      const tab = params.get('tab');
      if (tab === 'ageing-report' || tab === 'credit-appraisal') {
        return tab;
      }
    } catch {
      // fallback
    }
    return 'credit-appraisal';
  };

  const getInitialSubTab = () => {
    try {
      const params = new URLSearchParams(window.location.search);
      return params.get('sub');
    } catch {
      return null;
    }
  };

  const [activeAutomation, setActiveAutomationState] = useState<CRMAutomationId>(getInitialTab);
  const [creditSubTab, setCreditSubTabState] = useState<'create' | 'history'>(() => {
    const sub = getInitialSubTab();
    return sub === 'history' ? 'history' : 'create';
  });
  const [ageingSubTab, setAgeingSubTabState] = useState<'upload' | 'dashboard' | 'customers'>(() => {
    const sub = getInitialSubTab();
    return sub === 'dashboard' ? 'dashboard' : sub === 'customers' ? 'customers' : 'upload';
  });
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);
  const [isMobileOpen, setIsMobileOpen] = useState<boolean>(false);

  // Sync state to URL search parameters for clean bookmarking & browser back/forward
  const syncUrl = (tab: CRMAutomationId, sub?: string) => {
    try {
      const url = new URL(window.location.href);
      url.searchParams.set('tab', tab);
      if (sub) {
        url.searchParams.set('sub', sub);
      } else {
        url.searchParams.delete('sub');
      }
      window.history.pushState({}, '', url);
    } catch {
      // no-op
    }
  };

  const setActiveAutomation = (id: CRMAutomationId) => {
    setActiveAutomationState(id);
    setIsMobileOpen(false);
    const sub = id === 'credit-appraisal' ? creditSubTab : id === 'ageing-report' ? ageingSubTab : undefined;
    syncUrl(id, sub);
  };

  const setCreditSubTab = (tab: 'create' | 'history') => {
    setCreditSubTabState(tab);
    setIsMobileOpen(false);
    syncUrl('credit-appraisal', tab);
  };

  const setAgeingSubTab = (tab: 'upload' | 'dashboard' | 'customers') => {
    setAgeingSubTabState(tab);
    setIsMobileOpen(false);
    syncUrl('ageing-report', tab);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex font-sans antialiased text-slate-800">
      {/* WordPress-Style Left Sidebar */}
      <CRMSidebar
        activeAutomation={activeAutomation}
        setActiveAutomation={setActiveAutomation}
        creditSubTab={creditSubTab}
        setCreditSubTab={setCreditSubTab}
        ageingSubTab={ageingSubTab}
        setAgeingSubTab={setAgeingSubTab}
        isCollapsed={isCollapsed}
        setIsCollapsed={setIsCollapsed}
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
      />

      {/* Main Content Area (Offset by Sidebar Width) */}
      <div 
        className={`flex-1 min-w-0 flex flex-col min-h-screen transition-all duration-200 ease-in-out ${
          isCollapsed ? 'md:pl-16' : 'md:pl-64'
        }`}
      >
        {/* Top Masthead with Breadcrumbs & Status */}
        <CRMMasthead
          activeAutomation={activeAutomation}
          creditSubTab={creditSubTab}
          ageingSubTab={ageingSubTab}
          onOpenMobileSidebar={() => setIsMobileOpen(true)}
        />

        {/* Dynamic Automation View */}
        <main className="flex-1 bg-slate-50">
          {activeAutomation === 'credit-appraisal' && (
            <CreditAppraisalView
              subTab={creditSubTab}
              setSubTab={setCreditSubTab}
            />
          )}

          {activeAutomation === 'ageing-report' && (
            <AgeingReportView
              activeTab={ageingSubTab}
              setActiveTab={setAgeingSubTab}
            />
          )}
        </main>
      </div>
    </div>
  );
};
