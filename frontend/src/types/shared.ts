export type CRMAutomationId = 'credit-appraisal' | 'ageing-report' | 'dunning-exposure';

export interface CRMAutomationTab {
  id: CRMAutomationId;
  label: string;
  shortLabel: string;
  description: string;
  badge?: string;
  iconName: 'ShieldCheck' | 'CalendarClock' | 'BellRing' | 'FileSpreadsheet';
  isAvailable: boolean;
}
