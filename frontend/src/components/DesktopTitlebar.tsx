'use client';

import React, { useState } from 'react';
import { 
  Minus, 
  Square, 
  X, 
  Terminal, 
  Power, 
  Globe, 
  Activity, 
  AlertTriangle,
  Search,
  Sparkles,
  SlidersHorizontal,
  Command as CommandIcon,
  ShieldAlert,
  Coins,
  Radio,
  Layers
} from 'lucide-react';
import { Language, translations } from '@/lib/translations';

interface StudioTopBarProps {
  lang: Language;
  onToggleLang: () => void;
  activeTab?: 'workstation' | 'brain' | 'memory' | 'apps';
  onTabChange?: (tab: 'workstation' | 'brain' | 'memory' | 'apps') => void;
  wsStatus: 'connected' | 'connecting' | 'disconnected';
  onKillAll: () => void;
  onOpenCmd: () => void;
  onOpenEvolution?: () => void;
  onOpenApprovals?: () => void;
  onOpenResources?: () => void;
  onOpenConnections?: () => void;
  skillsCount?: number;
  totalCost?: number;
  hasDangerousApprovals?: boolean;
  hasMissingConnections?: boolean;
  pendingApprovalsCount?: number;
  kernelMode?: string;
  onModeChange?: (mode: string) => void;
  showDetails?: boolean;
  onToggleDetails?: () => void;
  onMinimize?: () => void;
  onMaximize?: () => void;
  onClose?: () => void;
}

export const StudioTopBar: React.FC<StudioTopBarProps> = ({
  lang,
  onToggleLang,
  activeTab = 'workstation',
  onTabChange,
  wsStatus,
  onKillAll,
  onOpenCmd,
  onOpenEvolution,
  onOpenApprovals,
  onOpenResources,
  onOpenConnections,
  skillsCount = 3,
  totalCost = 0,
  hasDangerousApprovals = false,
  hasMissingConnections = false,
  pendingApprovalsCount = 0,
  kernelMode = 'standard',
  onModeChange,
  showDetails = false,
  onToggleDetails,
  onMinimize,
  onMaximize,
  onClose,
}) => {
  const t = translations[lang];

  const handleWindowAction = (action: 'min' | 'max' | 'close') => {
    if (action === 'min' && onMinimize) onMinimize();
    else if (action === 'max' && onMaximize) onMaximize();
    else if (action === 'close' && onClose) onClose();
    else {
      if (action === 'max') {
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(() => {});
        } else {
          document.exitFullscreen().catch(() => {});
        }
      } else if (action === 'close') {
        window.close();
      }
    }
  };

  return (
    <header className="h-11 bg-black/95 border-b border-zinc-800/80 backdrop-blur-xl flex items-center justify-between px-3 select-none text-xs text-zinc-300 z-50 sticky top-0">
      {/* Left: Brand + Workspace Navigation Tabs */}
      <div className="flex items-center space-x-3">
        {/* Brand Logo & Name */}
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 rounded-md bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 flex items-center justify-center font-black text-white text-[11px] shadow-lg shadow-blue-500/20 border border-white/20">
            C
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="font-bold tracking-tight text-white text-xs">CONDUIT</span>
            <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 rounded bg-blue-500/10 text-blue-400 border border-blue-500/30">
              STUDIO
            </span>
          </div>
        </div>

        {/* Separator */}
        <div className="h-4 w-px bg-white/10 hidden sm:block" />

        {/* 4 Bosqich 2 Boshqaruv Tugmalari (Evolyutsiya, Tasdiqlar, Resurs, Ulanish) */}
        <div className="flex items-center space-x-1.5">
          {/* 1. Evolyutsiya */}
          <button
            onClick={onOpenEvolution}
            className="px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all flex items-center space-x-1.5 bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-white border border-white/[0.08] hover:border-indigo-500/40"
            title="Skillar, Xotira va Saboqlar"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>{lang === 'uz' ? 'Evolyutsiya' : 'Evolution'}</span>
            {skillsCount !== undefined && (
              <span className="px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 text-[10px] font-mono">
                {skillsCount}
              </span>
            )}
          </button>

          {/* 2. Tasdiqlar */}
          <button
            onClick={onOpenApprovals}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all flex items-center space-x-1.5 border ${
              hasDangerousApprovals
                ? 'bg-red-950/60 text-red-200 border-red-500/60 animate-pulse'
                : pendingApprovalsCount > 0
                ? 'bg-amber-950/40 text-amber-300 border-amber-500/40'
                : 'bg-slate-900/90 text-slate-300 border-white/[0.08] hover:bg-slate-800 hover:border-amber-500/40'
            }`}
            title="Kutilayotgan ruxsatlar navbati"
          >
            <ShieldAlert className={`w-3.5 h-3.5 ${hasDangerousApprovals ? 'text-red-400' : 'text-amber-400'}`} />
            <span>{lang === 'uz' ? 'Tasdiqlar' : 'Approvals'}</span>
            {pendingApprovalsCount > 0 && (
              <span
                className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                  hasDangerousApprovals
                    ? 'bg-red-500 text-white'
                    : 'bg-amber-500/20 text-amber-300'
                }`}
              >
                {pendingApprovalsCount}
              </span>
            )}
          </button>

          {/* 3. Resurs */}
          <button
            onClick={onOpenResources}
            className="px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all flex items-center space-x-1.5 bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-white border border-white/[0.08] hover:border-emerald-500/40"
            title="Tokenlar, vaqt va sarflangan pul ($)"
          >
            <Coins className="w-3.5 h-3.5 text-emerald-400" />
            <span>{lang === 'uz' ? 'Resurs' : 'Resource'}</span>
            <span className="text-emerald-400 font-mono text-[10px] font-bold">
              ${totalCost.toFixed(2)}
            </span>
          </button>

          {/* 4. Ulanish holati */}
          <button
            onClick={onOpenConnections}
            className="px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all flex items-center space-x-1.5 bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-white border border-white/[0.08] hover:border-cyan-500/40"
            title="CLI vositalari ulanish holati"
          >
            <Radio className="w-3.5 h-3.5 text-cyan-400" />
            <span>{lang === 'uz' ? 'Ulanish holati' : 'Connections'}</span>
            <span
              className={`w-2 h-2 rounded-full ${
                hasMissingConnections ? 'bg-rose-500 animate-pulse' : 'bg-emerald-400'
              }`}
            />
          </button>
        </div>

        {/* Separator */}
        <div className="h-4 w-px bg-white/10 hidden md:block" />

        {/* KERNEL V2 MODE SWITCHER */}
        <div className="hidden sm:flex items-center p-0.5 rounded-lg bg-slate-900 border border-white/10 text-[10px] font-mono">
          <button
            onClick={() => onModeChange && onModeChange('standard')}
            className={`px-2 py-0.5 rounded transition ${
              kernelMode === 'standard'
                ? 'bg-blue-600 text-white font-bold shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
            title="Standart Rejim: Bitta subagent ijrosi"
          >
            STANDART
          </button>
          <button
            onClick={() => onModeChange && onModeChange('eepx')}
            className={`px-2 py-0.5 rounded transition flex items-center space-x-1 ${
              kernelMode === 'eepx'
                ? 'bg-emerald-600 text-white font-bold shadow-sm shadow-emerald-500/20'
                : 'text-slate-400 hover:text-emerald-300'
            }`}
            title="EEPX Rejim: Chuqur kognitiv tahlil va ikki tomonlama audit"
          >
            <Sparkles className="w-2.5 h-2.5 text-emerald-300" />
            <span>EEPX</span>
          </button>
          <button
            onClick={() => onModeChange && onModeChange('super_agent')}
            className={`px-2 py-0.5 rounded transition flex items-center space-x-1 ${
              kernelMode === 'super_agent'
                ? 'bg-purple-600 text-white font-bold shadow-sm shadow-purple-500/20'
                : 'text-slate-400 hover:text-purple-300'
            }`}
            title="Super Agent Rejim: Avtonom ko'p subagentli Swarm orkestratsiyasi"
          >
            <Layers className="w-2.5 h-2.5 text-purple-300" />
            <span>SUPER AGENT</span>
          </button>
          <button
            onClick={() => onModeChange && onModeChange('deepx')}
            className={`px-2 py-0.5 rounded transition flex items-center space-x-1 ${
              kernelMode === 'deepx'
                ? 'bg-amber-600 text-white font-bold shadow-sm shadow-amber-500/20'
                : 'text-slate-400 hover:text-amber-300'
            }`}
            title="DEEPX Rejim: DeepSearch + Uzoq Muddat Fikrlash + Sentinel RedTeam + To'liq MVP"
          >
            <ShieldAlert className="w-2.5 h-2.5 text-amber-300" />
            <span>DEEPX</span>
          </button>
        </div>
      </div>

      {/* Center: Command Palette Trigger */}
      <div className="hidden lg:flex items-center justify-center flex-1 max-w-sm mx-4">
        <button
          onClick={onOpenCmd}
          className="w-full flex items-center justify-between px-3 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-900 border border-white/[0.08] hover:border-blue-500/40 text-slate-400 hover:text-slate-300 transition text-[11px] group shadow-sm"
          title="Buyruqlar paneli (Ctrl+K)"
        >
          <div className="flex items-center space-x-2">
            <Search className="w-3.5 h-3.5 text-blue-400 group-hover:scale-110 transition-transform" />
            <span>{lang === 'uz' ? 'Subagentlar yoki buyruqlar qidirish...' : 'Search agents or commands...'}</span>
          </div>
          <kbd className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-slate-400 border border-white/5">
            Ctrl+K
          </kbd>
        </button>
      </div>

      {/* Right: Details Toggle + Approvals + Kill All + Language + WS Status + Native Window Controls */}
      <div className="flex items-center space-x-2 sm:space-x-2.5">
        {/* Tafsilotlar (Ctrl+D) Toggle Button */}
        {onToggleDetails && (
          <button
            onClick={onToggleDetails}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium transition border ${
              showDetails
                ? 'bg-blue-600/20 text-blue-300 border-blue-500/40 shadow-sm'
                : 'bg-slate-900 hover:bg-slate-800 text-slate-300 border-white/[0.08]'
            }`}
            title="Tafsilotlarni ko'rish (Ctrl+D)"
          >
            <SlidersHorizontal className="w-3 h-3 text-blue-400" />
            <span className="font-semibold">{lang === 'uz' ? 'Tafsilotlar' : 'Details'}</span>
            <kbd className="hidden sm:inline-block px-1 py-0.2 rounded bg-black/40 text-[9px] font-mono text-slate-400">
              Ctrl+D
            </kbd>
          </button>
        )}

        {/* Approvals Alert */}
        {pendingApprovalsCount > 0 && (
          <span className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-bold animate-pulse">
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            <span>{pendingApprovalsCount}</span>
          </span>
        )}

        {/* WebSocket Ping Dot */}
        <div className="flex items-center space-x-1.5 px-2 py-1 rounded-md bg-slate-900/80 border border-white/[0.06] text-[10px] font-mono">
          <span
            className={`w-2 h-2 rounded-full ${
              wsStatus === 'connected'
                ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50'
                : wsStatus === 'connecting'
                ? 'bg-amber-400 animate-pulse'
                : 'bg-rose-500'
            }`}
          />
          <span className="text-slate-400 hidden xl:inline">
            {wsStatus === 'connected' ? 'LIVE' : 'SYNCING'}
          </span>
        </div>

        {/* Kill All Emergency Stop */}
        <button
          onClick={onKillAll}
          className="flex items-center space-x-1 px-2 py-1 rounded-md bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 text-[11px] font-medium transition active:scale-95"
          title="Barcha jarayonlarni to'xtatish"
        >
          <Power className="w-3 h-3" />
          <span className="hidden md:inline">{lang === 'uz' ? 'To\'xtatish' : 'Kill All'}</span>
        </button>

        {/* Language Switch */}
        <button
          onClick={onToggleLang}
          className="px-2 py-1 rounded-md bg-slate-900 hover:bg-slate-800 text-slate-300 border border-white/[0.08] text-[10px] font-bold font-mono transition"
          title="Tilni o'zgartirish"
        >
          {lang.toUpperCase()}
        </button>

        {/* Separator */}
        <div className="h-4 w-px bg-white/10" />

        {/* Window Controls */}
        <div className="flex items-center space-x-0.5">
          <button
            onClick={() => handleWindowAction('min')}
            className="w-6 h-6 flex items-center justify-center rounded hover:bg-white/10 text-slate-400 hover:text-white transition"
            title="Kichraytirish"
          >
            <Minus className="w-3 h-3" />
          </button>
          <button
            onClick={() => handleWindowAction('max')}
            className="w-6 h-6 flex items-center justify-center rounded hover:bg-white/10 text-slate-400 hover:text-white transition"
            title="Katta ekran (F11)"
          >
            <Square className="w-2.5 h-2.5" />
          </button>
          <button
            onClick={() => handleWindowAction('close')}
            className="w-6 h-6 flex items-center justify-center rounded hover:bg-rose-600 text-slate-400 hover:text-white transition"
            title="Yopish"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      </div>
    </header>
  );
};
