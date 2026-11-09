'use client';

import React, { useState } from 'react';
import {
  Activity,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Terminal,
  Folder,
  Image as ImageIcon,
  ChevronRight,
  FileText,
  Info,
} from 'lucide-react';

interface Subagent {
  id: string;
  name: string;
  display_name_uz: string;
  display_name_en: string;
  role_desc_uz?: string;
  role_desc_en?: string;
  status: 'active' | 'later';
}

interface Task {
  task_id: string;
  title: string;
  prompt: string;
  target_agent: string;
  status: string;
  current_step: string;
  planner_output?: string;
  doer_output?: string;
  checker_output?: string;
  evidence?: string;
  screenshot_url?: string;
  step_durations?: {
    planner?: number;
    doer?: number;
    checker?: number;
  };
  total_duration?: number;
  created_at: string;
}

interface LogEntry {
  task_id: string;
  agent_name: string;
  level: string;
  message: string;
  timestamp: string;
}

interface Window4SubagentDetailProps {
  selectedAgent: Subagent | null;
  task: Task | null;
  logs: LogEntry[];
  lang: 'uz' | 'en';
}

export const Window4SubagentDetail: React.FC<Window4SubagentDetailProps> = ({
  selectedAgent,
  task,
  logs,
  lang,
}) => {
  const [activeTab, setActiveTab] = useState<'steps' | 'logs' | 'evidence'>('steps');

  if (!selectedAgent) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 bg-slate-950/50 text-center select-none">
        <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-white/10 flex items-center justify-center text-slate-500 mb-3 shadow-inner">
          <Activity className="w-6 h-6 stroke-[1.5]" />
        </div>
        <h3 className="text-sm font-semibold text-slate-300 mb-1">
          {lang === 'uz' ? 'Subagent tanlanmagan' : 'No Subagent Selected'}
        </h3>
        <p className="text-xs text-slate-400 max-w-sm">
          {lang === 'uz'
            ? 'Uning joriy ishi, qadamlar tarixi, oxirgi skrinshot va real-vaqt loglarini ko‘rish uchun Oyna 3 dagi biror subagentni bosing.'
            : 'Click any subagent in Window 3 to inspect active tasks, step history, screenshots, and live logs.'}
        </p>
      </div>
    );
  }

  // Filter logs for this specific agent or task
  const agentLogs = logs.filter(
    (l) =>
      l.agent_name.toLowerCase() === selectedAgent.id.toLowerCase() ||
      l.agent_name.toLowerCase() === selectedAgent.name.toLowerCase() ||
      (task && l.task_id === task.task_id)
  );

  const stepDurations = task?.step_durations || {};

  return (
    <div className="flex-1 flex flex-col bg-slate-950/90 overflow-hidden font-sans">
      {/* Subagent Top Bar */}
      <div className="h-12 px-4 border-b border-white/10 flex items-center justify-between bg-slate-900/60">
        <div className="flex items-center space-x-3">
          <div className="w-2.5 h-2.5 rounded-full bg-blue-400" />
          <div className="flex items-center space-x-2">
            <span className="font-bold text-sm text-white">{selectedAgent.name}</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
              workspaces/{selectedAgent.id}/
            </span>
          </div>
        </div>

        {/* Tab switchers */}
        <div className="flex items-center space-x-1 bg-slate-950 p-0.5 rounded-lg border border-white/5 text-xs">
          <button
            onClick={() => setActiveTab('steps')}
            className={`px-2.5 py-1 rounded-md transition font-medium ${
              activeTab === 'steps' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            {lang === 'uz' ? 'Qadamlar Tarixi' : 'Step History'}
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`px-2.5 py-1 rounded-md transition font-medium flex items-center space-x-1.5 ${
              activeTab === 'logs' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <span>{lang === 'uz' ? 'Loglar' : 'Logs'}</span>
            <span className="px-1 py-0.2 text-[9px] rounded-full bg-black/40 font-mono">
              {agentLogs.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('evidence')}
            className={`px-2.5 py-1 rounded-md transition font-medium ${
              activeTab === 'evidence' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            {lang === 'uz' ? 'Dalil & Skrinshot' : 'Evidence'}
          </button>
        </div>
      </div>

      {/* Detail Content */}
      <div className="flex-1 overflow-y-auto p-4 text-xs">
        {activeTab === 'steps' ? (
          <div className="space-y-4">
            {/* Active / Last Task Prompt */}
            {task ? (
              <div className="p-3 rounded-xl bg-slate-900/60 border border-white/10 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono text-slate-400">
                    ID: {task.task_id.slice(0, 8)}...
                  </span>
                  <span
                    className={`font-mono text-[10px] font-bold px-2 py-0.5 rounded border ${
                      task.status === 'PASS'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : task.status === 'FAIL'
                        ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                        : 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                    }`}
                  >
                    {task.status}
                  </span>
                </div>
                <p className="text-slate-200 font-medium">{task.prompt}</p>
              </div>
            ) : (
              <p className="text-slate-500 italic">
                {lang === 'uz' ? 'Hozircha biriktirilgan vazifa yo‘q.' : 'No active task assigned.'}
              </p>
            )}

            {/* 3 Steps Pipeline: Planner -> Doer -> Checker */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {/* Step 1: Planner */}
              <div className="p-3 rounded-xl bg-slate-900/40 border border-white/5 space-y-2">
                <div className="flex items-center justify-between text-slate-400">
                  <span className="font-semibold text-white">1. PLANNER</span>
                  <span className="font-mono text-[11px] text-blue-400">
                    {stepDurations.planner !== undefined ? `${stepDurations.planner}s` : '—'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed font-mono">
                  {task?.planner_output ||
                    (lang === 'uz' ? 'Rejalashtirish kutilmoqda...' : 'Awaiting planning...')}
                </p>
              </div>

              {/* Step 2: Doer */}
              <div className="p-3 rounded-xl bg-slate-900/40 border border-white/5 space-y-2">
                <div className="flex items-center justify-between text-slate-400">
                  <span className="font-semibold text-white">2. DOER (IJRO)</span>
                  <span className="font-mono text-[11px] text-blue-400">
                    {stepDurations.doer !== undefined ? `${stepDurations.doer}s` : '—'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed font-mono">
                  {task?.doer_output ||
                    (lang === 'uz' ? 'Amallar bajarilishi...' : 'Executing steps...')}
                </p>
              </div>

              {/* Step 3: Checker */}
              <div className="p-3 rounded-xl bg-slate-900/40 border border-white/5 space-y-2">
                <div className="flex items-center justify-between text-slate-400">
                  <span className="font-semibold text-white">3. CHECKER</span>
                  <span className="font-mono text-[11px] text-blue-400">
                    {stepDurations.checker !== undefined ? `${stepDurations.checker}s` : '—'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed font-mono">
                  {task?.checker_output ||
                    (lang === 'uz' ? 'Tekshiruv dalili...' : 'Verifying evidence...')}
                </p>
              </div>
            </div>
          </div>
        ) : activeTab === 'logs' ? (
          <div className="h-full flex flex-col font-mono text-[11px]">
            {agentLogs.length === 0 ? (
              <div className="p-4 text-slate-500 italic text-center">
                {lang === 'uz' ? 'Ushbu subagent uchun yangi loglar yo‘q' : 'No logs for this subagent'}
              </div>
            ) : (
              <div className="space-y-1">
                {agentLogs.map((log, idx) => (
                  <div
                    key={idx}
                    className="flex items-start space-x-2 py-1 px-2 rounded hover:bg-white/5"
                  >
                    <span className="text-slate-400 shrink-0">
                      {log.timestamp ? log.timestamp.split('T')[1]?.slice(0, 8) : ''}
                    </span>
                    <span
                      className={`px-1 rounded text-[10px] shrink-0 ${
                        log.level === 'ERROR'
                          ? 'bg-rose-500/20 text-rose-400'
                          : log.level === 'WARNING'
                          ? 'bg-amber-500/20 text-amber-400'
                          : log.level === 'SUCCESS'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : 'bg-blue-500/20 text-blue-400'
                      }`}
                    >
                      {log.level}
                    </span>
                    <span className="text-slate-300 break-all">{log.message}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-white/10 space-y-2">
              <span className="text-slate-400 font-semibold">
                {lang === 'uz' ? 'Yakuniy Dalil:' : 'Verified Evidence:'}
              </span>
              <p className="text-slate-200 font-mono text-xs">
                {task?.evidence || (lang === 'uz' ? 'Hali dalil qaytarilmadi.' : 'No evidence returned yet.')}
              </p>
            </div>

            {task?.screenshot_url ? (
              <div className="rounded-xl overflow-hidden border border-white/10 bg-slate-950 p-2">
                <img
                  src={task.screenshot_url}
                  alt="Subagent Screenshot"
                  className="w-full max-h-48 object-contain rounded-lg"
                />
              </div>
            ) : (
              <div className="p-6 rounded-xl border border-dashed border-white/10 text-center text-slate-500">
                {lang === 'uz' ? 'Ushbu vazifada skrinshot olinmadi' : 'No screenshot captured for this task'}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
