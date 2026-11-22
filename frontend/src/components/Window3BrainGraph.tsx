'use client';

import React, { useMemo } from 'react';
import {
  Brain,





  Zap,
  Search,
  Box,

  ShieldAlert,
  Palette,
  Film,
  Scissors,
  Brush,
  FileText,
  MessageSquare,
  Crown,
  FlaskConical,
  Globe,
  Image as ImageIcon,
  PenTool,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

/** Per-role identity: icon + accent colour so cards are recognisable at a glance. */
const AGENT_STYLE: Record<string, { icon: LucideIcon; tint: string; ring: string }> = {
  scout: { icon: Search, tint: 'text-sky-300', ring: 'bg-sky-500/10 border-sky-500/25' },
  sculptor: { icon: Box, tint: 'text-orange-300', ring: 'bg-orange-500/10 border-orange-500/25' },
  inspector: { icon: FlaskConical, tint: 'text-emerald-300', ring: 'bg-emerald-500/10 border-emerald-500/25' },
  sentinel: { icon: ShieldAlert, tint: 'text-rose-300', ring: 'bg-rose-500/10 border-rose-500/25' },
  designer: { icon: Palette, tint: 'text-fuchsia-300', ring: 'bg-fuchsia-500/10 border-fuchsia-500/25' },
  animator: { icon: Film, tint: 'text-slate-300', ring: 'bg-slate-500/10 border-slate-500/25' },
  editor: { icon: Scissors, tint: 'text-amber-300', ring: 'bg-amber-500/10 border-amber-500/25' },
  painter: { icon: Brush, tint: 'text-pink-300', ring: 'bg-pink-500/10 border-pink-500/25' },
  notion: { icon: FileText, tint: 'text-slate-200', ring: 'bg-slate-500/10 border-slate-400/25' },
  slack: { icon: MessageSquare, tint: 'text-slate-300', ring: 'bg-slate-500/10 border-slate-500/25' },
  superagent: { icon: Crown, tint: 'text-yellow-300', ring: 'bg-yellow-500/10 border-yellow-500/25' },
  // Instrument yordamchi agentlari (ilova dvigatellari)
  inst_blender: { icon: Box, tint: 'text-orange-200', ring: 'bg-orange-500/15 border-orange-400/30' },
  inst_video: { icon: Film, tint: 'text-slate-200', ring: 'bg-slate-500/15 border-slate-400/30' },
  inst_image: { icon: ImageIcon, tint: 'text-pink-200', ring: 'bg-pink-500/15 border-pink-400/30' },
  inst_web: { icon: Globe, tint: 'text-sky-200', ring: 'bg-sky-500/15 border-sky-400/30' },
  inst_figma: { icon: PenTool, tint: 'text-fuchsia-200', ring: 'bg-fuchsia-500/15 border-fuchsia-400/30' },
};

const FALLBACK_STYLE = { icon: Brain, tint: 'text-slate-300', ring: 'bg-slate-500/10 border-slate-500/25' };

interface Subagent {
  id: string;
  name: string;
  display_name_uz: string;
  display_name_en: string;
  role_desc_uz?: string;
  role_desc_en?: string;
  status: 'active' | 'later';
  icon?: string;
}

interface Window3BrainGraphProps {
  subagents: Subagent[];
  activeAgentId: string | null;
  onSelectAgent: (agentId: string) => void;
  activeAgents?: string[];
  activeCommandTo?: string | null;
  agentReports: Record<string, { status: 'PASS' | 'FAIL' | 'BLOCKED'; evidence?: string }>;
  currentTaskStatus?: string;
  lang: 'uz' | 'en';
}

export const Window3BrainGraph: React.FC<Window3BrainGraphProps> = ({
  subagents,
  activeAgentId,
  onSelectAgent,
  activeAgents = [],
  activeCommandTo,
  agentReports,
  currentTaskStatus,
  lang,
}) => {
  const activeSubagents = useMemo(() => {
    return subagents.filter((a) => a.status === 'active' || a.id !== 'superagent');
  }, [subagents]);

  // Merge single active subagent and parallel active agents list
  const activeAgentsSet = useMemo(() => {
    const s = new Set<string>(activeAgents.map((a) => a.toLowerCase()));
    if (activeCommandTo) s.add(activeCommandTo.toLowerCase());
    return s;
  }, [activeAgents, activeCommandTo]);

  const isAnyWorking = activeAgentsSet.size > 0 || currentTaskStatus === 'working';

  return (
    <div className="flex-[4] min-h-0 flex flex-col p-3 bg-slate-900/30 border-b border-white/10 relative overflow-hidden select-none">
      <style jsx>{`
        @keyframes flowForward {
          0% { stroke-dashoffset: 32; }
          100% { stroke-dashoffset: 0; }
        }
        @keyframes flowBackward {
          0% { stroke-dashoffset: 0; }
          100% { stroke-dashoffset: 32; }
        }
        .anim-flow-forward {
          stroke-dasharray: 8 6;
          animation: flowForward 0.9s linear infinite;
        }
        .anim-flow-backward {
          stroke-dasharray: 8 6;
          animation: flowBackward 0.9s linear infinite;
        }
      `}</style>

      {/* Background Tech Grid effect */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-800/20 via-transparent to-transparent pointer-events-none" />

      {/* Header Bar */}
      <div className="flex items-center justify-between pb-2 border-b border-white/5 relative z-10">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-slate-500 animate-pulse" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono">
            {lang === 'uz' ? 'Agentlar tarmog‘i' : 'Agent Network'}
          </h2>
        </div>

        <div className="flex items-center space-x-3 text-[11px] font-mono text-slate-400">
          <span className="flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>PASS</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
            <span>FAIL</span>
          </span>
          <span className="flex items-center space-x-1 text-slate-400 font-bold">
            <Zap className="w-3 h-3" />
            <span>{activeAgentsSet.size > 0 ? `${activeAgentsSet.size} PARALLEL` : 'IDLE'}</span>
          </span>
        </div>
      </div>

      {/* Visual Graph Area with Curved Bezier Connections */}
      <div className="flex-1 min-h-0 flex flex-col justify-start gap-2 pt-1 pb-1 relative z-10 overflow-y-auto">
        {/* Core Brain Orchestrator Node */}
        <div className="relative group">
          <div
            className={`px-5 py-2.5 rounded-2xl border transition-all duration-300 flex items-center space-x-3 shadow-xl ${
              isAnyWorking
                ? 'bg-slate-950/70 border-slate-400/70 shadow-slate-500/25 ring-2 ring-slate-500/30'
                : 'bg-slate-900/90 border-white/15 hover:border-slate-400/50'
            }`}
          >
            <div
              className={`p-2 rounded-xl ${
                isAnyWorking
                  ? 'bg-gradient-to-tr from-slate-500 to-slate-600 text-white animate-spin-slow shadow-md'
                  : 'bg-slate-500/10 text-slate-400'
              }`}
            >
              <Brain className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-bold text-xs text-white tracking-wide">
                  {lang === 'uz' ? 'BOSH AGENT' : 'CORE BRAIN'}
                </span>
                <span className="px-1.5 py-0.2 rounded text-[11px] font-mono font-bold bg-slate-500/20 text-slate-300 border border-slate-500/30">
                  YURAK (N=3 PARALLEL)
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                {activeAgentsSet.size > 0
                  ? lang === 'uz'
                    ? `Parallel oqim: ${Array.from(activeAgentsSet).map((s) => s.toUpperCase()).join(', ')}`
                    : `Active streams: ${Array.from(activeAgentsSet).map((s) => s.toUpperCase()).join(', ')}`
                  : lang === 'uz'
                  ? 'Kutish rejimida (Idle)'
                  : 'Ready for CLI commands'}
              </p>
            </div>
          </div>

          {isAnyWorking && (
            <span className="absolute -inset-1 rounded-2xl bg-slate-500/20 blur-md -z-10 animate-pulse" />
          )}
        </div>

        {/* Oddiy bog'lovchi: Bosh agent -> subagentlar (animatsiya/gradient yo'q) */}
        <div className="relative h-5 w-full shrink-0" aria-hidden>
          <div className={`absolute left-1/2 top-0 h-2.5 w-px ${isAnyWorking ? 'bg-blue-500/50' : 'bg-white/15'}`} />
          <div className={`absolute left-[25%] right-[25%] top-2.5 h-px ${isAnyWorking ? 'bg-blue-500/50' : 'bg-white/15'}`} />
          <div className={`absolute left-[25%] top-2.5 h-2.5 w-px ${isAnyWorking ? 'bg-blue-500/50' : 'bg-white/15'}`} />
          <div className={`absolute left-[75%] top-2.5 h-2.5 w-px ${isAnyWorking ? 'bg-blue-500/50' : 'bg-white/15'}`} />
        </div>

        {/* Subagent kartalari: rol ikonkasi, aniq nom va holat */}
        <div className="w-full grid grid-cols-2 gap-2 auto-rows-fr">
          {activeSubagents.map((agent) => {
            const agentKey = agent.id.toLowerCase();
            const isCurrentlyActive = activeAgentsSet.has(agentKey);
            const isSelected = activeAgentId === agent.id;
            const report = agentReports[agentKey];
            const style = AGENT_STYLE[agentKey] ?? FALLBACK_STYLE;
            const RoleIcon = style.icon;

            const status = isCurrentlyActive
              ? 'RUN'
              : report?.status === 'PASS'
              ? 'PASS'
              : report?.status === 'FAIL'
              ? 'FAIL'
              : report?.status === 'BLOCKED'
              ? 'BLOCKED'
              : 'IDLE';

            const statusTone =
              status === 'PASS'
                ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                : status === 'FAIL'
                ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                : status === 'BLOCKED'
                ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                : status === 'RUN'
                ? 'bg-slate-500/10 text-slate-300 border-slate-500/30'
                : 'bg-slate-700/30 text-slate-400 border-white/10';

            return (
              <button
                key={agent.id}
                onClick={() => onSelectAgent(agent.id)}
                aria-pressed={isSelected}
                aria-label={`${agent.name} — ${status}`}
                className={`group relative min-w-0 p-2.5 rounded-xl border text-left transition-all duration-200 flex flex-col gap-2 h-full ${
                  isSelected
                    ? 'bg-slate-950/60 border-slate-400 ring-2 ring-slate-500/30 shadow-lg shadow-slate-950/40'
                    : isCurrentlyActive
                    ? 'bg-slate-950/40 border-slate-400/70 ring-1 ring-slate-500/30 shadow-md'
                    : 'bg-slate-900/70 border-white/8 hover:border-slate-400/40 hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-start justify-between gap-1.5">
                  <span className={`p-1.5.5 rounded-lg border shrink-0 ${style.ring}`}>
                    <RoleIcon className={`w-3.5 h-3.5 ${style.tint}`} aria-hidden="true" />
                  </span>
                  <span
                    className={`text-[11px] font-mono font-semibold px-1.5 py-1 rounded border shrink-0 ${statusTone}`}
                  >
                    {status}
                  </span>
                </div>

                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-sm text-white leading-tight truncate group-hover:text-slate-300 transition">
                    {agent.name}
                  </h3>
                  <p className={`text-[11px] leading-snug line-clamp-2 min-h-[2.1em] ${isCurrentlyActive ? 'text-slate-300' : 'text-slate-400'}`}>
                    {isCurrentlyActive
                      ? (lang === 'uz' ? 'Ishlamoqda…' : 'Working…')
                      : (agent.role_desc_uz || agent.role_desc_en || (lang === 'uz' ? 'Kutish rejimida' : 'Idle'))}
                  </p>
                </div>

                {/* Active stream indicator */}
                {isCurrentlyActive && (
                  <div className="pt-1.5 border-t border-slate-500/20 text-[11px] font-mono text-slate-300 flex items-center gap-1">
                    <Zap className="w-3 h-3 shrink-0" aria-hidden="true" />
                    <span className="truncate">{lang === 'uz' ? 'Faol oqim' : 'Active stream'}</span>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
