'use client';

import React, { useState } from 'react';
import { 
  Terminal, 
  Activity,
  ShieldCheck,
  Layers,
  Volume2,
  VolumeX
} from 'lucide-react';
import { Language } from '@/lib/translations';
import { soundEngine } from '@/lib/audio';

interface DesktopStatusBarProps {
  lang: Language;
  wsStatus: 'connected' | 'connecting' | 'disconnected';
  activeEngine: string;
  kernelMode?: string;
  activeSubagent?: string | null;
  taskCount: number;
  budget?: {
    usedTokens: number;
    maxTokens: number;
    usedCostUsd: number;
    maxBudgetUsd: number;
    isBlocked: boolean;
  };
}

export const DesktopStatusBar: React.FC<DesktopStatusBarProps> = ({

  wsStatus,
  activeEngine,
  kernelMode,
  activeSubagent,
  taskCount,
  budget
}) => {
  const compact = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(n >= 100000 ? 0 : 1)}k` : String(n));
  const [soundOn, setSoundOn] = useState(() => soundEngine.getEnabled());

  const handleToggleSound = () => {
    const newState = soundEngine.toggle();
    setSoundOn(newState);
  };
  return (
    <footer className="h-9 bg-[#0b0f15] border-t border-white/10 px-4 flex items-center justify-between text-[11px] text-zinc-400 select-none z-50">
      {/* Left items: Connection & Host */}
      <div className="flex items-center space-x-3">
        {/* WS Status */}
        <div className="flex items-center space-x-1.5">
          <span
            className={`w-2 h-2 rounded-full ${
              wsStatus === 'connected'
                ? 'bg-emerald-400'
                : wsStatus === 'connecting'
                ? 'bg-amber-400 animate-pulse'
                : 'bg-rose-500'
            }`}
          />
          <span className="font-mono text-slate-300">
            {wsStatus === 'connected' ? 'ONLINE // 127.0.0.1:8000' : 'CONNECTING...'}
          </span>
        </div>

        <span className="text-slate-600">|</span>

        {/* Engine */}
        <div className="flex items-center space-x-1 text-slate-300">
          <Terminal className="w-3 h-3 text-blue-400" />
          <span className="font-mono uppercase">{activeEngine}</span>
        </div>

        <span className="text-slate-600">|</span>

        {/* Kernel mode */}
        {kernelMode && (
          <div className="flex items-center space-x-1 text-slate-300">
            <Layers className="w-3 h-3 text-blue-400" />
            <span className="font-mono uppercase">{kernelMode.replace('_', ' ')}</span>
          </div>
        )}

        <span className="text-slate-600">|</span>

        {/* Security sandbox */}
        <div className="flex items-center space-x-1 text-emerald-400">
          <ShieldCheck className="w-3 h-3" />
          <span>SANDBOX ISOLATED</span>
        </div>
      </div>

      {/* Center item: Active Subagent / Heart state */}
      <div className="hidden sm:flex items-center space-x-2">
        {activeSubagent ? (
          <span className="flex items-center space-x-1 px-2 py-1 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 font-mono text-[11px]">
            <Activity className="w-2.5 h-2.5 animate-spin" />
            <span>SUBAGENT: {activeSubagent.toUpperCase()}</span>
          </span>
        ) : (
          <span className="text-slate-500 font-mono text-[11px]">
            SYSTEM READY // HEURISTIC ENGINE IDLE
          </span>
        )}
      </div>

      {/* Right items: Shortcuts, Sound & Tasks */}
      <div className="flex items-center space-x-3 font-mono text-slate-400">
        <button
          onClick={handleToggleSound}
          title={soundOn ? 'Ovozni o‘chirish' : 'Ovozni yoqish'}
          className="flex h-6 items-center space-x-1 px-1 rounded text-slate-400 hover:text-blue-400 hover:bg-white/5 transition cursor-pointer"
        >
          {soundOn ? <Volume2 className="w-3 h-3 text-blue-400" /> : <VolumeX className="w-3 h-3 text-slate-500" />}
          <span className="text-[11px]">{soundOn ? 'SFX ON' : 'SFX MUTE'}</span>
        </button>
        {budget && (
          <>
            <span
              title="Subagent token/narx byudjeti (conduit budget)"
              className={budget.isBlocked ? 'text-rose-400' : 'text-emerald-400'}
            >
              TOK {compact(budget.usedTokens)}/{compact(budget.maxTokens)} · ${budget.usedCostUsd.toFixed(2)}
            </span>
            <span className="text-slate-600">|</span>
          </>
        )}
        <span>TASKS: {taskCount}</span>
        <span className="text-slate-600">|</span>
        <span className="hover:text-slate-200 transition">Ctrl+Enter (Run)</span>
        <span className="text-slate-600">|</span>
        <span className="hover:text-slate-200 transition">Ctrl+D (Details)</span>
      </div>
    </footer>
  );
};
