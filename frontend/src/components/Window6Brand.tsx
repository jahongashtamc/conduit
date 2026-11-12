'use client';

import React from 'react';
import { Cpu } from 'lucide-react';

interface Window6BrandProps {
  wsStatus: 'connected' | 'connecting' | 'disconnected';
}

export const Window6Brand: React.FC<Window6BrandProps> = ({ wsStatus }) => {
  return (
    <div className="h-14 px-4 flex items-center justify-between border-b border-white/10 bg-slate-900/50 select-none shrink-0">
      <div className="flex items-center space-x-2.5">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 via-indigo-600 to-cyan-500 p-px shadow-md shadow-blue-500/20 flex items-center justify-center">
          <div className="w-full h-full bg-slate-950 rounded-[7px] flex items-center justify-center">
            <Cpu className="w-4 h-4 text-blue-400" />
          </div>
        </div>
        <div className="min-w-0">
          <span className="block font-bold tracking-wider text-sm text-white font-mono leading-tight">CONDUIT</span>
          <p className="text-[10px] text-slate-400 font-mono tracking-tight truncate">Sovereign Agent Studio</p>
        </div>
      </div>

      <div className="flex items-center space-x-1.5 shrink-0" title={`WebSocket: ${wsStatus}`}>
        <span
          className={`w-2 h-2 rounded-full ${
            wsStatus === 'connected'
              ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50'
              : wsStatus === 'connecting'
              ? 'bg-amber-400 animate-ping'
              : 'bg-rose-500'
          }`}
        />
      </div>
    </div>
  );
};
