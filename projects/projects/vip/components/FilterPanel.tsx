import React from 'react';
// FIX: Imported missing types Filters and GeminiModel.
import { Filters, GeminiModel } from '../types';
// FIX: Imported HistoryIcon which was missing from Icons.tsx.
import { HistoryIcon } from './Icons';

interface FilterPanelProps {
  filters: Filters;
  onFilterChange: (filters: Filters) => void;
  model: GeminiModel;
  onModelChange: (model: GeminiModel) => void;
  history: string[];
  onSearch: (query: string) => void;
  isLoading: boolean;
}

const FilterControl: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <div>
    <label className="block text-xs font-medium text-youtube-light-gray mb-1">{label}</label>
    {children}
  </div>
);

export const FilterPanel: React.FC<FilterPanelProps> = ({ filters, onFilterChange, model, onModelChange, history, onSearch, isLoading }) => {

  const handleSelectChange = <K extends keyof Filters,>(key: K) => (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({ ...filters, [key]: e.target.value as Filters[K] });
  };

  const handleModelSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onModelChange(e.target.value as GeminiModel);
  };

  const commonSelectClasses = "w-full bg-youtube-dark border border-gray-600 rounded-md p-2 text-sm focus:outline-none focus:ring-2 focus:ring-youtube-red";

  const modelOptions: { value: GeminiModel; label: string }[] = [
    { value: 'gemini-flash-lite-latest', label: 'Flash-Lite Latest' },
    { value: 'gemini-flash-latest', label: 'Flash Latest' },
    { value: 'gemini-2.5-pro', label: '2.5 Pro' },
    { value: 'gemini-2.0-flash', label: '2.0 Flash' },
    { value: 'gemini-2.0-flash-lite', label: '2.0 Flash-Lite' },
    { value: 'learnlm-2.0-flash-experimental', label: 'LearnLM 2.0 Exp' },
  ];

  const uploadDateOptions = [
    { value: 'any', label: 'Any time' }, { value: 'today', label: 'Today' }, { value: 'week', label: 'This week' }, { value: 'month', label: 'This month' }, { value: 'year', label: 'This year' },
  ];

  const durationOptions = [
    { value: 'any', label: 'Any duration' }, { value: 'short', label: 'Short (< 4 min)' }, { value: 'medium', label: 'Medium (4-20 min)' }, { value: 'long', label: 'Long (> 20 min)' },
  ];

  const typeOptions = [
    { value: 'video', label: 'Video' }, { value: 'channel', label: 'Channel' }, { value: 'playlist', label: 'Playlist' },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-2">
          <FilterControl label="AI Model">
            <select value={model} onChange={handleModelSelectChange} className={commonSelectClasses}>
              {modelOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
            </select>
          </FilterControl>
        </div>
        <FilterControl label="Upload Date">
          <select value={filters.uploadDate} onChange={handleSelectChange('uploadDate')} className={commonSelectClasses}>
            {uploadDateOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
          </select>
        </FilterControl>
        <FilterControl label="Duration">
          <select value={filters.duration} onChange={handleSelectChange('duration')} className={commonSelectClasses}>
            {durationOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
          </select>
        </FilterControl>
        <FilterControl label="Type">
          <select value={filters.type} onChange={handleSelectChange('type')} className={commonSelectClasses}>
            {typeOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
          </select>
        </FilterControl>
      </div>

      {history.length > 0 && (
         <div className="border-t border-gray-700 pt-4">
            <h3 className="text-sm font-semibold text-youtube-light-gray mb-3 flex items-center">
              <HistoryIcon className="w-4 h-4 mr-2" />
              Recent Searches
            </h3>
            <div className="flex flex-wrap gap-2">
              {history.map((item, index) => (
                <button
                  key={index}
                  onClick={() => onSearch(item)}
                  disabled={isLoading}
                  className="text-xs text-gray-300 bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded-full transition-colors disabled:cursor-not-allowed disabled:text-gray-500 disabled:hover:bg-gray-700"
                >
                  {item}
                </button>
              ))}
            </div>
         </div>
      )}
    </div>
  );
};
