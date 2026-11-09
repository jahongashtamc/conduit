'use client';

import React, { useState, useEffect } from 'react';
import {
  Compass,
  ShieldCheck,
  Box,
  Sparkles,
  Film,
  Brush,
  Palette,
  Bot,
  Circle,
  Clock,
  CheckCircle2,
  AlertCircle,
  ShieldAlert,
  Terminal,
  Camera,
  Timer
} from 'lucide-react';
import { Language, translations } from '@/lib/translations';

interface Subagent {
  id: string;
  name: string;
  display_name_uz: string;
  display_name_en: string;
  role_desc_uz: string;
  role_desc_en: string;
  target_app: string;
  status: 'active' | 'later';
  icon: string;
}

interface PendingApproval {
  approval_id: string;
  agent_id: string;
  action_type: string;
  risk_description: string;
  status: string;
}

interface SubagentsListProps {
  subagents: Subagent[];
  activeAgentId: string | null;
  onSelectAgent: (agentId: string) => void;
  lang: Language;
  currentAgentWorking?: string | null;
  activeCommandTo?: string | null;
  agentReports?: Record<string, { status: 'PASS' | 'FAIL' | 'BLOCKED'; evidence?: string }>;
  pendingApprovals?: PendingApproval[];
  activeTask?: {
    task_id: string;
    target_agent: string;
    status: string;
    current_step: string;
    total_duration?: number;
    screenshot_url?: string;
  } | null;
}

const getAgentIcon = (id: string) => {
  switch (id) {
    case 'scout':
      return Compass;
    case 'inspector':
      return ShieldCheck;
    case 'sculptor':
      return Box;
    case 'animator':
      return Sparkles;
    case 'editor':
      return Film;
    case 'painter':
      return Brush;
    case 'designer':
      return Palette;
    default:
      return Bot;
  }
};

export const SubagentsList: React.FC<SubagentsListProps> = ({
  subagents,
  activeAgentId,
  onSelectAgent,
  lang,
  currentAgentWorking,
  activeCommandTo,
  agentReports,
  pendingApprovals = [],
  activeTask,
}) => {
  const t = translations[lang];

  // Live stopwatch for active working agent
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const isAnyAgentWorking = Boolean(currentAgentWorking || activeCommandTo);

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isAnyAgentWorking) {
      interval = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      setElapsedSeconds(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isAnyAgentWorking]);

  const formatTimer = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}s`;
  };

  return (
    <aside className="w-full lg:w-72 bg-slate-900/60 border-r border-slate-800 p-4 flex flex-col h-full overflow-y-auto">
      {/* Header telemetry summary */}
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            {t.subagentsTitle}
          </h2>
          <p className="text-[11px] text-slate-500">{t.subagentsDesc}</p>
        </div>
        {isAnyAgentWorking && (
          <div className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-[10px] font-mono">
            <Timer className="w-3 h-3 animate-spin" />
            <span>{formatTimer(elapsedSeconds)}</span>
          </div>
        )}
      </div>

      <div className="space-y-2">
        {subagents.map((agent) => {
          const Icon = getAgentIcon(agent.id);
          const isSelected = activeAgentId === agent.id;
          const isActive = agent.status === 'active';
          const isWorkingNow = currentAgentWorking === agent.id || activeCommandTo === agent.id;
          const hasCommand = activeCommandTo === agent.id;
          const report = agentReports?.[agent.id];
          
          // Check if there is an approval waiting for this agent
          const needsApproval = pendingApprovals.some(
            (appr) =>
              appr.status === 'pending' &&
              (appr.agent_id.toLowerCase() === agent.id.toLowerCase() ||
               (agent.id === 'scout' && appr.agent_id.toLowerCase() === 'manager'))
          );

          // Determine explicit state: 'needs approval', 'working', 'PASS', 'FAIL', 'BLOCKED', 'idle'
          let explicitStatus: 'needs approval' | 'working' | 'PASS' | 'FAIL' | 'BLOCKED' | 'idle' = 'idle';
          if (needsApproval) {
            explicitStatus = 'needs approval';
          } else if (isWorkingNow) {
            explicitStatus = 'working';
          } else if (report?.status === 'PASS' || (activeTask?.target_agent === agent.id && activeTask.status === 'PASS')) {
            explicitStatus = 'PASS';
          } else if (report?.status === 'FAIL' || (activeTask?.target_agent === agent.id && activeTask.status === 'FAIL')) {
            explicitStatus = 'FAIL';
          } else if (report?.status === 'BLOCKED' || (activeTask?.target_agent === agent.id && activeTask.status === 'BLOCKED')) {
            explicitStatus = 'BLOCKED';
          } else if (isActive) {
            explicitStatus = 'idle';
          }

          // Step title
          const isCurrentTarget = activeTask?.target_agent === agent.id;
          const currentStep = isCurrentTarget ? activeTask?.current_step : null;

          return (
            <button
              key={agent.id}
              onClick={() => onSelectAgent(agent.id)}
              className={`w-full text-left p-3 rounded-xl border transition-all duration-300 flex items-start space-x-3 group relative overflow-hidden ${
                needsApproval
                  ? 'bg-amber-950/30 border-amber-500/70 shadow-[0_0_15px_rgba(245,158,11,0.2)] ring-1 ring-amber-500/40'
                  : hasCommand
                  ? 'bg-gradient-to-r from-purple-950/40 via-cyan-950/30 to-slate-900 border-cyan-400/80 shadow-[0_0_18px_rgba(6,182,212,0.35)] ring-2 ring-cyan-500/50'
                  : isWorkingNow
                  ? 'bg-blue-950/40 border-blue-500/70 shadow-[0_0_14px_rgba(59,130,246,0.25)]'
                  : isSelected
                  ? 'bg-blue-600/15 border-blue-500/50 shadow-sm'
                  : 'bg-slate-800/40 border-slate-800/80 hover:bg-slate-800/80 hover:border-slate-700'
              }`}
            >
              {/* Agent Icon */}
              <div
                className={`p-2 rounded-lg mt-0.5 shrink-0 transition ${
                  needsApproval
                    ? 'bg-amber-500/20 text-amber-300 animate-bounce'
                    : hasCommand || isWorkingNow
                    ? 'bg-cyan-500/30 text-cyan-300 animate-pulse'
                    : isActive
                    ? 'bg-blue-500/20 text-blue-400 group-hover:bg-blue-500/30'
                    : 'bg-slate-800 text-slate-500'
                }`}
              >
                <Icon className="w-4 h-4" />
              </div>

              {/* Agent Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-1">
                  <span className="font-semibold text-xs text-slate-100 truncate">
                    {lang === 'uz' ? agent.display_name_uz : agent.display_name_en}
                  </span>

                  {/* Aniq holat Badge: idle, working, needs approval, PASS, FAIL */}
                  {explicitStatus === 'needs approval' ? (
                    <span className="flex items-center space-x-1 text-[9px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/50 shrink-0 animate-pulse">
                      <AlertCircle className="w-2.5 h-2.5" />
                      <span>{t.needsApproval}</span>
                    </span>
                  ) : explicitStatus === 'working' ? (
                    <span className="flex items-center space-x-1 text-[9px] font-bold px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/40 shrink-0">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping" />
                      <span>{t.working}</span>
                    </span>
                  ) : explicitStatus === 'PASS' ? (
                    <span className="flex items-center space-x-1 text-[9px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shrink-0">
                      <CheckCircle2 className="w-2.5 h-2.5" />
                      <span>PASS</span>
                    </span>
                  ) : explicitStatus === 'FAIL' ? (
                    <span className="flex items-center space-x-1 text-[9px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/50 shrink-0">
                      <ShieldAlert className="w-2.5 h-2.5" />
                      <span>FAIL</span>
                    </span>
                  ) : explicitStatus === 'BLOCKED' ? (
                    <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-orange-500/20 text-orange-300 border border-orange-500/50 shrink-0">
                      BLOCKED
                    </span>
                  ) : isActive ? (
                    <span className="text-[10px] font-medium px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-400 border border-slate-700/60 shrink-0">
                      {t.idle}
                    </span>
                  ) : (
                    <span className="text-[10px] font-medium px-1.5 py-0.2 rounded-full bg-slate-800/60 text-slate-500 border border-slate-700/40 shrink-0">
                      {t.statusLater}
                    </span>
                  )}
                </div>

                <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">
                  {lang === 'uz' ? agent.role_desc_uz : agent.role_desc_en}
                </p>

                {/* Sub-status & Live Monitoring Metrics */}
                <div className="flex items-center flex-wrap gap-1.5 mt-2 text-[10px]">
                  {/* Joriy qadam indicator */}
                  {isWorkingNow && currentStep ? (
                    <span className="px-1.5 py-0.2 rounded bg-cyan-950/60 text-cyan-300 border border-cyan-800/80 font-mono text-[9px]">
                      Qadam: {currentStep}
                    </span>
                  ) : null}

                  {/* Ijro vaqti (Execution time stopwatch) */}
                  {isWorkingNow ? (
                    <span className="flex items-center space-x-1 text-cyan-300 font-mono text-[9px]">
                      <Timer className="w-2.5 h-2.5 animate-spin text-cyan-400" />
                      <span>{formatTimer(elapsedSeconds)}</span>
                    </span>
                  ) : isCurrentTarget && activeTask?.total_duration ? (
                    <span className="flex items-center space-x-1 text-slate-400 font-mono text-[9px]">
                      <Clock className="w-2.5 h-2.5 text-slate-500" />
                      <span>{activeTask.total_duration}s</span>
                    </span>
                  ) : null}

                  {/* Workspace tag */}
                  <span className="text-emerald-400/90 font-mono text-[9px] bg-slate-900 px-1.5 py-0.2 rounded border border-slate-800">
                    workspaces/{agent.id}/
                  </span>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </aside>
  );
};
