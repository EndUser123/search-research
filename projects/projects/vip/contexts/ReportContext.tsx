import React, { createContext, useState, useContext, ReactNode } from 'react';
import type { AnalysisReport } from '../types';

interface ReportContextType {
  analysisReport: AnalysisReport | null;
  setAnalysisReport: (report: AnalysisReport | null) => void;
}

const ReportContext = createContext<ReportContextType | undefined>(undefined);

export const ReportProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [analysisReport, setAnalysisReport] = useState<AnalysisReport | null>(null);

  return (
    <ReportContext.Provider value={{ analysisReport, setAnalysisReport }}>
      {children}
    </ReportContext.Provider>
  );
};

export const useReport = (): ReportContextType => {
  const context = useContext(ReportContext);
  if (context === undefined) {
    throw new Error('useReport must be used within a ReportProvider');
  }
  return context;
};
