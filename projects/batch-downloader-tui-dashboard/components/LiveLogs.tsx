
import React, { useEffect, useRef } from 'react';
import { LogEntry, LogLevel } from '../types';

interface Props {
  logs: LogEntry[];
}

const LiveLogs: React.FC<Props> = ({ logs }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  const getLevelColor = (level: LogLevel) => {
    switch (level) {
      case LogLevel.INFO: return 'text-blue-400';
      case LogLevel.SUCCESS: return 'text-green-400';
      case LogLevel.ERROR: return 'text-red-400';
      case LogLevel.WARN: return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="bg-[#131720] border border-[#1E2530] rounded-md flex flex-col h-[500px] lg:h-auto overflow-hidden">
      <div className="p-4 border-b border-[#1E2530] flex justify-between items-center">
        <h2 className="text-lg font-bold uppercase text-[#F7FAFC]">Live Logs</h2>
        <div className="flex gap-1">
          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
          <div className="w-2 h-2 rounded-full bg-gray-600"></div>
          <div className="w-2 h-2 rounded-full bg-gray-600"></div>
        </div>
      </div>
      <div 
        ref={containerRef}
        className="p-4 overflow-y-auto font-mono text-[13px] leading-relaxed flex-1 bg-[#0b0e14]"
      >
        {logs.map((log, i) => (
          <div key={i} className="mb-1 flex gap-2">
            <span className="text-gray-600 shrink-0">[{log.timestamp}]</span>
            <span className={`font-bold shrink-0 ${getLevelColor(log.level)}`}>[{log.level}]</span>
            <span className="text-gray-300">{log.message}</span>
          </div>
        ))}
        {logs.length === 0 && (
          <div className="text-gray-600 italic">No logs available. System initialized.</div>
        )}
      </div>
    </div>
  );
};

export default LiveLogs;
