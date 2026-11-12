'use client';

import React, { useMemo } from 'react';
import {
  Brain,
  Activity,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Zap,
  Search,
  Box,
  ShieldCheck,
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
  animator: { icon: Film, tint: 'text-violet-300', ring: 'bg-violet-500/10 border-violet-500/25' },
  editor: { icon: Scissors, tint: 'text-amber-300', ring: 'bg-amber-500/10 border-amber-500/25' },
  painter: { icon: Brush, tint: 'text-pink-300', ring: 'bg-pink-500/10 border-pink-500/25' },
  notion: { icon: FileText, tint: 'text-slate-200', ring: 'bg-slate-500/10 border-slate-400/25' },
  slack: { icon: MessageSquare, tint: 'text-purple-300', ring: 'bg-purple-500/10 border-purple-500/25' },
  superagent: { icon: Crown, tint: 'text-yellow-300', ring: 'bg-yellow-500/10 border-yellow-500/25' },
  // Instrument yordamchi agentlari (ilova dvigatellari)
  inst_blender: { icon: Box, tint: 'text-orange-200', ring: 'bg-orange-500/15 border-orange-400/30' },
  inst_video: { icon: Film, tint: 'text-violet-200', ring: 'bg-violet-500/15 border-violet-400/30' },
  inst_image: { icon: ImageIcon, tint: 'text-pink-200', ring: 'bg-pink-500/15 border-pink-400/30' },
  inst_web: { icon: Globe, tint: 'text-sky-200', ring: 'bg-sky-500/15 border-sky-400/30' },
  inst_figma: { icon: PenTool, tint: 'text-fuchsia-200', ring: 'bg-fuchsia-500/15 border-fuchsia-400/30' },
};

const FALLBACK_STYLE = { icon: Brain, tint: 'text-cyan-300', ring: 'bg-cyan-500/10 border-cyan-500/25' };

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
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-950/20 via-transparent to-transparent pointer-events-none" />

      {/* Header Bar */}
      <div className="flex items-center justify-between pb-2 border-b border-white/5 relative z-10">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
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
          <span className="flex items-center space-x-1 text-cyan-400 font-bold">
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
                ? 'bg-blue-950/70 border-cyan-400/70 shadow-cyan-500/20 ring-2 ring-cyan-500/30'
                : 'bg-slate-900/90 border-white/15 hover:border-blue-400/50'
            }`}
          >
            <div
              className={`p-2 rounded-xl ${
                isAnyWorking
                  ? 'bg-gradient-to-tr from-cyan-500 to-blue-600 text-white animate-spin-slow shadow-md'
                  : 'bg-blue-500/10 text-blue-400'
              }`}
            >
              <Brain className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-bold text-xs text-white tracking-wide">
                  {lang === 'uz' ? 'BOSH AGENT' : 'CORE BRAIN'}
                </span>
                <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  YURAK (N=3 PARALLEL)
                </span>
              </div>
              <p className="text-[10px] text-slate-400 font-mono mt-0.5">
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
            <span className="absolute -inset-1 rounded-2xl bg-cyan-500/20 blur-md -z-10 animate-pulse" />
          )}
        </div>

        {/* Dynamic Curved Bezier SVG Connection Canvas */}
        <div className="w-full h-10 relative flex items-center justify-center pointer-events-none">
          <svg className="w-full h-full overflow-visible" viewBox="0 0 700 80" preserveAspectRatio="none">
            <defs>
              {/* Gradient for forward command dispatch */}
              <linearGradient id="commandStreamGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#38bdf8" />
                <stop offset="50%" stopColor="#818cf8" />
                <stop offset="100%" stopColor="#06b6d4" />
              </linearGradient>

              {/* Gradient for backward report return */}
              <linearGradient id="reportStreamGrad" x1="0%" y1="100%" x2="0%" y2="0%">
                <stop offset="0%" stopColor="#10b981" />
                <stop offset="100%" stopColor="#38bdf8" />
              </linearGradient>

              {/* Glow filter */}
              <filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Render curved bezier lines from Brain (350, 0) to each subagent position */}
            {activeSubagents.map((agent, idx) => {
              const total = activeSubagents.length;
              // Target X coordinate distributed evenly across 700 units
              const targetX = 50 + (idx / (total - 1 || 1)) * 600;
              const startX = 350;
              const startY = 5;
              const endY = 75;

              const agentKey = agent.id.toLowerCase();
              const isWorking = activeAgentsSet.has(agentKey);
              const rep = agentReports[agentKey];
              const isReportDone = rep && (rep.status === 'PASS' || rep.status === 'FAIL');

              // Smooth cubic bezier curve
              const pathD = `M ${startX} ${startY} C ${startX} 40, ${targetX} 40, ${targetX} ${endY}`;

              return (
                <g key={agent.id}>
                  {/* Subtle background base curve */}
                  <path
                    d={pathD}
                    fill="none"
                    stroke={isWorking ? 'rgba(56, 189, 248, 0.25)' : 'rgba(255, 255, 255, 0.08)'}
                    strokeWidth={isWorking ? 2 : 1}
                  />

                  {/* Active Command Flow (Brain -> Subagent) */}
                  {isWorking && (
                    <path
                      d={pathD}
                      fill="none"
                      stroke="url(#commandStreamGrad)"
                      strokeWidth={3}
                      className="anim-flow-forward"
                      filter="url(#neonGlow)"
                    />
                  )}

                  {/* Active Report Flow (Subagent -> Brain in reverse) */}
                  {!isWorking && isReportDone && (
                    <path
                      d={pathD}
                      fill="none"
                      stroke="url(#reportStreamGrad)"
                      strokeWidth={2}
                      className="anim-flow-backward"
                      opacity={0.8}
                    />
                  )}
                </g>
              );
            })}
          </svg>
        </div>

        {/* Subagent kartalari: rol ikonkasi, aniq nom va holat */}
        <div className="w-full grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-2 auto-rows-fr">
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
                ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
                : 'bg-slate-700/30 text-slate-400 border-white/10';

            return (
              <button
                key={agent.id}
                onClick={() => onSelectAgent(agent.id)}
                aria-pressed={isSelected}
                aria-label={`${agent.name} — ${status}`}
                className={`group relative min-w-0 p-2.5 rounded-xl border text-left transition-all duration-200 flex flex-col gap-2 h-full ${
                  isSelected
                    ? 'bg-blue-950/60 border-blue-400 ring-2 ring-blue-500/25 shadow-lg'
                    : isCurrentlyActive
                    ? 'bg-cyan-950/40 border-cyan-400/70 ring-1 ring-cyan-500/30 shadow-md'
                    : 'bg-slate-900/70 border-white/8 hover:border-white/25 hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-start justify-between gap-1.5">
                  <span className={`p-1.5 rounded-lg border shrink-0 ${style.ring}`}>
                    <RoleIcon className={`w-3.5 h-3.5 ${style.tint}`} aria-hidden="true" />
                  </span>
                  <span
                    className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded border shrink-0 ${statusTone}`}
                  >
                    {status}
                  </span>
                </div>

                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-sm text-white leading-tight truncate group-hover:text-cyan-300 transition">
                    {agent.name}
                  </h3>
                  <p className={`text-[11px] leading-snug line-clamp-2 min-h-[2.1em] ${isCurrentlyActive ? 'text-cyan-300' : 'text-slate-400'}`}>
                    {isCurrentlyActive
                      ? (lang === 'uz' ? 'Ishlamoqda…' : 'Working…')
                      : (agent.role_desc_uz || agent.role_desc_en || (lang === 'uz' ? 'Kutish rejimida' : 'Idle'))}
                  </p>
                </div>

                {/* Active stream indicator */}
                {isCurrentlyActive && (
                  <div className="pt-1.5 border-t border-cyan-500/20 text-[10px] font-mono text-cyan-300 flex items-center gap-1">
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
