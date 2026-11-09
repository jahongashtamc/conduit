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
} from 'lucide-react';

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
    <div className="flex-1 flex flex-col p-4 bg-slate-950/70 border-b border-white/10 relative overflow-hidden select-none">
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
            {lang === 'uz' ? 'Oyna 3 — Bosh Agent & Parallel Subagentlar Tuguni' : 'Window 3 — Core Brain & Subagents Node'}
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
      <div className="flex-1 flex flex-col justify-between items-center pt-2 pb-1 relative z-10">
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
        <div className="w-full h-16 relative flex items-center justify-center pointer-events-none my-1">
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

        {/* Connected Subagents Grid (Names ONLY - NO target app names displayed) */}
        <div className="w-full grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
          {activeSubagents.map((agent) => {
            const agentKey = agent.id.toLowerCase();
            const isCurrentlyActive = activeAgentsSet.has(agentKey);
            const isSelected = activeAgentId === agent.id;
            const report = agentReports[agentKey];

            return (
              <button
                key={agent.id}
                onClick={() => onSelectAgent(agent.id)}
                className={`group relative p-2.5 rounded-xl border text-left transition-all duration-200 flex flex-col justify-between ${
                  isSelected
                    ? 'bg-blue-950/50 border-blue-400 ring-2 ring-blue-500/20 shadow-lg'
                    : isCurrentlyActive
                    ? 'bg-cyan-950/40 border-cyan-400/80 ring-1 ring-cyan-500/40 animate-pulse shadow-md'
                    : 'bg-slate-900/60 border-white/5 hover:border-white/20 hover:bg-slate-800/40'
                }`}
              >
                {/* Top: Status Pill */}
                <div className="flex items-center justify-between mb-1.5">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      isCurrentlyActive
                        ? 'bg-cyan-400 animate-ping'
                        : report?.status === 'PASS'
                        ? 'bg-emerald-400'
                        : report?.status === 'FAIL'
                        ? 'bg-rose-400'
                        : report?.status === 'BLOCKED'
                        ? 'bg-amber-400'
                        : 'bg-slate-600'
                    }`}
                  />
                  {report?.status ? (
                    <span
                      className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded border ${
                        report.status === 'PASS'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : report.status === 'FAIL'
                          ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                          : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                      }`}
                    >
                      {report.status}
                    </span>
                  ) : (
                    <span className="text-[9px] font-mono text-slate-400">
                      {isCurrentlyActive ? 'RUN' : 'IDLE'}
                    </span>
                  )}
                </div>

                {/* Subagent Name ONLY (Never show underlying target app) */}
                <div>
                  <h3 className="font-semibold text-xs text-white group-hover:text-cyan-400 transition truncate">
                    {agent.name}
                  </h3>
                  <p className="text-[10px] text-slate-400 font-mono mt-0.5 truncate">
                    {isCurrentlyActive ? (
                      <span className="text-cyan-400 flex items-center space-x-1">
                        <Activity className="w-2.5 h-2.5 animate-spin" />
                        <span>{lang === 'uz' ? 'Ishlamoqda' : 'Working'}</span>
                      </span>
                    ) : (
                      lang === 'uz' ? 'Subagent' : 'Subagent'
                    )}
                  </p>
                </div>

                {/* Active stream indicator */}
                {isCurrentlyActive && (
                  <div className="mt-1.5 pt-1 border-t border-cyan-500/20 text-[9px] font-mono text-cyan-300 truncate flex items-center space-x-1">
                    <Zap className="w-2.5 h-2.5" />
                    <span>{lang === 'uz' ? 'Parallel nur faol' : 'Stream active'}</span>
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
