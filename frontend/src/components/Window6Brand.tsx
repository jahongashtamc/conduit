'use client';

import React from 'react';
import { Cpu, ShieldCheck } from 'lucide-react';

interface Window6BrandProps {
  wsStatus: 'connected' | 'connecting' | 'disconnected';
}

export const Window6Brand: React.FC<Window6BrandProps> = ({ wsStatus }) => {
  return (
    <div className="h-16 px-4 flex items-center justify-between border-b border-white/10 bg-slate-900/60 select-none">
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 via-indigo-600 to-cyan-500 p-0.5 shadow-md shadow-blue-500/20 flex items-center justify-center">
          <div className="w-full h-full bg-slate-950 rounded-[7px] flex items-center justify-center">
            <Cpu className="w-5 h-5 text-blue-400 animate-pulse" />
          </div>
        </div>
        <div>
          <div className="flex items-center space-x-1.5">
            <span className="font-bold tracking-wider text-sm text-white font-mono">CONDUIT</span>
            <span className="px-1.5 py-0.2 text-[9px] font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded">
              7-OYNA
            </span>
          </div>
          <p className="text-[10px] text-slate-400 font-mono tracking-tight">Sovereign Agent Studio</p>
        </div>
      </div>

      <div className="flex items-center space-x-1.5" title={`WebSocket: ${wsStatus}`}>
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
