
import React from 'react';
import { DownloadItem, DownloadStatus } from '../types';

interface Props {
  downloads: DownloadItem[];
}

const StatusBadge: React.FC<{ status: DownloadStatus }> = ({ status }) => {
  const styles = {
    [DownloadStatus.DOWNLOADING]: 'bg-[#1A365D] text-blue-100 border-blue-400/30',
    [DownloadStatus.QUEUED]: 'bg-[#2D3748] text-gray-300 border-gray-400/30',
    [DownloadStatus.COMPLETED]: 'bg-[#1C4532] text-green-100 border-green-400/30',
    [DownloadStatus.ERROR]: 'bg-[#742A2A] text-red-100 border-red-400/30',
  };

  return (
    <span className={`px-4 py-1.5 rounded-sm text-xs font-bold uppercase tracking-wider border ${styles[status]} min-w-[120px] text-center inline-block`}>
      {status}
    </span>
  );
};

const DownloadTable: React.FC<Props> = ({ downloads }) => {
  return (
    <div className="bg-[#131720] border border-[#1E2530] rounded-md overflow-hidden flex flex-col">
      <div className="p-4 border-b border-[#1E2530]">
        <h2 className="text-lg font-bold uppercase text-[#F7FAFC]">Current Downloads</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-gray-500 uppercase font-bold border-b border-[#1E2530]">
            <tr>
              <th className="px-6 py-4">Channel</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Progress</th>
              <th className="px-6 py-4">ETA</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1E2530]">
            {downloads.map((item) => (
              <tr key={item.id} className="hover:bg-[#1A202C] transition-colors group">
                <td className="px-6 py-5 font-medium group-hover:text-blue-400">{item.channel}</td>
                <td className="px-6 py-5">
                  <StatusBadge status={item.status} />
                </td>
                <td className="px-6 py-5 min-w-[200px]">
                  <div className="flex items-center gap-3">
                    <div className="flex-1 bg-[#1A202C] rounded-full h-1 overflow-hidden border border-[#2D3748]">
                      <div 
                        className={`h-full transition-all duration-300 ${item.status === DownloadStatus.ERROR ? 'bg-red-500' : 'bg-[#2B6CB0]'}`}
                        style={{ width: `${item.progress}%` }}
                      ></div>
                    </div>
                    <span className="text-xs font-mono w-8">{item.progress}%</span>
                  </div>
                </td>
                <td className="px-6 py-5 text-gray-400 font-mono tracking-tighter">
                  {item.eta}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DownloadTable;
