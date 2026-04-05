
import React from 'react';

interface Props {
  progress: number;
  summary: string;
}

const OverallStatus: React.FC<Props> = ({ progress, summary }) => {
  return (
    <section className="bg-[#131720] border border-[#1E2530] p-6 rounded-md shadow-xl">
      <h2 className="text-lg font-bold mb-4 uppercase text-[#F7FAFC]">Overall Download Status</h2>
      <div className="space-y-4">
        <div className="flex flex-col gap-2">
          <span className="text-sm text-gray-400 uppercase tracking-widest font-semibold">Overall Progress</span>
          <div className="w-full bg-[#1A202C] rounded-full h-2 overflow-hidden border border-[#2D3748]">
            <div 
              className="bg-[#2B6CB0] h-full transition-all duration-700 ease-out" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
        <p className="text-sm text-gray-400 font-mono">{summary}</p>
      </div>
    </section>
  );
};

export default OverallStatus;
