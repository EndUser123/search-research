
import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="flex items-center justify-between py-2 border-b border-[#1E2530]">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-[#2B6CB0] flex items-center justify-center rotate-45">
          <div className="w-4 h-4 bg-white rotate-[-45deg] rounded-sm"></div>
        </div>
        <h1 className="text-xl font-bold tracking-tight uppercase">Batch Downloader</h1>
      </div>
      
      <nav className="hidden md:flex items-center gap-8">
        <a href="#" className="text-sm font-medium text-white hover:text-blue-400 transition-colors uppercase">Dashboard</a>
        <a href="#" className="text-sm font-medium text-gray-400 hover:text-white transition-colors uppercase">Settings</a>
        <a href="#" className="text-sm font-medium text-gray-400 hover:text-white transition-colors uppercase">Help</a>
        <div className="w-10 h-10 rounded-full bg-[#1A365D] border border-blue-500/30 overflow-hidden flex items-center justify-center">
          <img src="https://picsum.photos/seed/user/40" alt="Avatar" className="w-full h-full object-cover opacity-80" />
        </div>
      </nav>
    </header>
  );
};

export default Header;
