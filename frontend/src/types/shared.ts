export type CRMAutomationId = 'credit-appraisal' | 'ageing-report';

export interface CRMAutomationTab {
  id: CRMAutomationId;
  label: string;
  shortLabel: string;
  description: string;
  badge?: string;
  iconName: 'ShieldCheck' | 'CalendarClock' | 'FileSpreadsheet';
  isAvailable: boolean;
}
