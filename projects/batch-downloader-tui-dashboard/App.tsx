
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { DownloadItem, DownloadStatus, LogEntry, LogLevel } from './types';
import Header from './components/Header';
import OverallStatus from './components/OverallStatus';
import DownloadTable from './components/DownloadTable';
import LiveLogs from './components/LiveLogs';

const INITIAL_DOWNLOADS: DownloadItem[] = [
  { id: '1', channel: 'Tech Insights', status: DownloadStatus.DOWNLOADING, progress: 85, eta: '0:03' },
  { id: '2', channel: 'Gaming Central', status: DownloadStatus.QUEUED, progress: 0, eta: '--:--' },
  { id: '3', channel: 'Music Mixes', status: DownloadStatus.DOWNLOADING, progress: 45, eta: '0:12' },
  { id: '4', channel: 'Travel Vlogs', status: DownloadStatus.COMPLETED, progress: 100, eta: '0:00' },
  { id: '5', channel: 'News Updates', status: DownloadStatus.ERROR, progress: 0, eta: '--:--' },
  { id: '6', channel: 'Science Daily', status: DownloadStatus.DOWNLOADING, progress: 15, eta: '0:25' },
];

const App: React.FC = () => {
  const [downloads, setDownloads] = useState<DownloadItem[]>(INITIAL_DOWNLOADS);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Helper to add a log
  const addLog = useCallback((level: LogLevel, message: string) => {
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
    setLogs(prev => [...prev, { timestamp, level, message }]);
  }, []);

  // Initialize with some logs
  useEffect(() => {
    const initialLogs: LogEntry[] = [
      { timestamp: '2024-01-20 14:30:00', level: LogLevel.INFO, message: "Starting download for 'Tech Insights'." },
      { timestamp: '2024-01-20 14:30:15', level: LogLevel.INFO, message: "Download progress for 'Tech Insights': 25%." },
      { timestamp: '2024-01-20 14:31:00', level: LogLevel.SUCCESS, message: "Download complete for 'Tech Insights'." },
      { timestamp: '2024-01-20 14:31:10', level: LogLevel.INFO, message: "Starting download for 'Music Mixes'." },
      { timestamp: '2024-01-20 14:31:55', level: LogLevel.ERROR, message: "Failed to download 'News Updates'. Reason: Network connection lost." },
      { timestamp: '2024-01-20 14:32:10', level: LogLevel.INFO, message: "Initiating download for 'Science Daily'." },
    ];
    setLogs(initialLogs);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Simulate dynamic updates
  useEffect(() => {
    const interval = setInterval(() => {
      setDownloads(current => current.map(item => {
        if (item.status === DownloadStatus.DOWNLOADING) {
          const newProgress = Math.min(100, item.progress + Math.floor(Math.random() * 5));
          const isFinished = newProgress === 100;
          
          if (isFinished) {
            addLog(LogLevel.SUCCESS, `Download complete for '${item.channel}'.`);
          } else if (newProgress % 20 === 0) {
            addLog(LogLevel.INFO, `Download progress for '${item.channel}': ${newProgress}%.`);
          }

          return {
            ...item,
            progress: newProgress,
            status: isFinished ? DownloadStatus.COMPLETED : item.status,
            eta: isFinished ? '0:00' : `0:${Math.max(0, parseInt(item.eta.split(':')[1]) - 1).toString().padStart(2, '0')}`
          };
        }
        return item;
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, [addLog]);

  const activeCount = downloads.filter(d => d.status === DownloadStatus.DOWNLOADING).length;
  const completedCount = downloads.filter(d => d.status === DownloadStatus.COMPLETED).length;
  const totalCount = downloads.length;
  const overallProgress = Math.round((downloads.reduce((acc, d) => acc + d.progress, 0) / (totalCount * 100)) * 100);

  return (
    <div className="min-h-screen p-6 md:p-10 flex flex-col gap-6 max-w-7xl mx-auto">
      <Header />
      
      <OverallStatus 
        progress={overallProgress} 
        summary={`${overallProgress}% Complete (${activeCount}/${totalCount} downloads active)`} 
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1">
        <DownloadTable downloads={downloads} />
        <LiveLogs logs={logs} />
      </div>
    </div>
  );
};

export default App;
