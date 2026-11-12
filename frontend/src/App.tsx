import React, { useState } from 'react';
import { CRMHeader } from './components/layout/CRMHeader';
import { CreditAppraisalView } from './automations/credit-appraisal/CreditAppraisalView';
import { AgeingReportView } from './automations/ageing-report/AgeingReportView';
import { CRMAutomationId } from './types/shared';

export const App: React.FC = () => {
  const getInitialTab = (): CRMAutomationId => {
    try {
      const params = new URLSearchParams(window.location.search);
      const tab = params.get('tab');
      if (tab === 'ageing-report' || tab === 'credit-appraisal' || tab === 'dunning-exposure') {
        return tab;
      }
    } catch {
      // fallback
    }
    return 'credit-appraisal';
  };

  const [activeAutomation, setActiveAutomationState] = useState<CRMAutomationId>(getInitialTab);

  const setActiveAutomation = (id: CRMAutomationId) => {
    setActiveAutomationState(id);
    try {
      const url = new URL(window.location.href);
      url.searchParams.set('tab', id);
      window.history.pushState({}, '', url);
    } catch {
      // no-op
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Master CRM Navigation Header */}
      <CRMHeader
        activeAutomation={activeAutomation}
        setActiveAutomation={setActiveAutomation}
      />

      {/* Main Automation Workspace */}
      <main className="flex-1">
        {activeAutomation === 'credit-appraisal' && <CreditAppraisalView />}
        {activeAutomation === 'ageing-report' && <AgeingReportView />}
      </main>
    </div>
  );
};
