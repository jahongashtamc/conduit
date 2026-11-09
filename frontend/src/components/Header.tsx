'use client';

import React from 'react';
import { Power, Globe, Moon, Sun, Terminal, CheckCircle2, AlertTriangle } from 'lucide-react';
import { Language, translations } from '@/lib/translations';

interface HeaderProps {
  lang: Language;
  onToggleLang: () => void;
  isDark: boolean;
  onToggleTheme: () => void;
  wsStatus: 'connected' | 'connecting' | 'disconnected';
  onKillAll: () => void;
  onOpenCmd: () => void;
  pendingApprovalsCount?: number;
}

export const Header: React.FC<HeaderProps> = ({
  lang,
  onToggleLang,
  isDark,
  onToggleTheme,
  wsStatus,
  onKillAll,
  onOpenCmd,
  pendingApprovalsCount = 0,
}) => {
  const t = translations[lang];

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/95 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand & Project Info */}
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 flex items-center justify-center font-black text-white text-lg tracking-wider shadow-md shadow-blue-500/20">
          C
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-bold text-lg text-white tracking-tight">{t.appTitle}</h1>
            <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              FAZA 2: SECURED
            </span>
            {pendingApprovalsCount > 0 && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500 text-slate-950 animate-bounce">
                {pendingApprovalsCount} {t.pendingApprovalsBadge}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">{t.appSubtitle}</p>
        </div>
      </div>

      {/* Middle: Connection Status & Quick Cmd Prompt */}
      <div className="flex items-center space-x-3">
        <button
          onClick={onOpenCmd}
          className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs text-slate-300 hover:bg-slate-800 hover:border-slate-600 transition"
          title="Open Command Palette (Ctrl+K)"
        >
          <Terminal className="w-3.5 h-3.5 text-blue-400" />
          <span>{lang === 'uz' ? 'Buyruqlar paneli' : 'Command palette'}</span>
          <kbd className="px-1.5 py-0.5 rounded bg-slate-700/80 text-[10px] font-mono text-slate-400">Ctrl+K</kbd>
        </button>

        {/* Live WebSocket Status */}
        <div className="flex items-center space-x-2 px-2.5 py-1 rounded-full bg-slate-800/60 border border-slate-700/60 text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              wsStatus === 'connected'
                ? 'bg-emerald-400 animate-pulse'
                : wsStatus === 'connecting'
                ? 'bg-amber-400 animate-pulse'
                : 'bg-rose-500'
            }`}
          />
          <span className="text-slate-300 font-medium">
            {wsStatus === 'connected' ? t.statusConnected : wsStatus === 'connecting' ? t.statusConnecting : t.statusDisconnected}
          </span>
        </div>
      </div>

      {/* Right Controls: Kill All, Language, Theme */}
      <div className="flex items-center space-x-2 sm:space-x-3">
        {/* Kill All Button */}
        <button
          onClick={onKillAll}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 font-medium text-xs transition active:scale-95 shadow-sm"
          title={t.killAllConfirm}
        >
          <Power className="w-3.5 h-3.5" />
          <span className="hidden sm:inline font-semibold">{t.killAll}</span>
        </button>

        {/* Language Switcher */}
        <button
          onClick={onToggleLang}
          className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition"
          title="Switch Language (UZ / EN)"
        >
          <Globe className="w-3.5 h-3.5 text-slate-400" />
          <span className="uppercase">{lang}</span>
        </button>

        {/* Theme Toggle */}
        <button
          onClick={onToggleTheme}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
          title="Toggle Theme"
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-blue-400" />}
        </button>
      </div>
    </header>
  );
};
