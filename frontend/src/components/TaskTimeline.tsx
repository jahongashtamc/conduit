'use client';

import React, { useState } from 'react';
import {
  GitCommit,
  CheckCircle2,
  Clock,
  AlertCircle,
  ShieldAlert,
  ChevronDown,
  ChevronRight,
  FileText,
  Activity,
  Bot,
  Timer,
  Copy,
  Check,
  ExternalLink,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { Language, translations } from '@/lib/translations';

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
  created_at: string;
  step_durations?: {
    planner?: number;
    doer?: number;
    checker?: number;
  };
  total_duration?: number;
}

interface TaskTimelineProps {
  task: Task | null;
  lang: Language;
}

export const TaskTimeline: React.FC<TaskTimelineProps> = ({ task, lang }) => {
  const t = translations[lang];
  const [expandedStep, setExpandedStep] = useState<string | null>('checker');
  const [copiedStep, setCopiedStep] = useState<string | null>(null);

  const handleCopy = (key: string, text?: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedStep(key);
    setTimeout(() => setCopiedStep(null), 2000);
  };

  if (!task) {
    return (
      <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-8 text-center flex flex-col items-center justify-center">
        <div className="w-12 h-12 rounded-full bg-slate-800/80 flex items-center justify-center text-slate-500 mb-3">
          <GitCommit className="w-6 h-6" />
        </div>
        <h3 className="font-semibold text-slate-300 text-sm">{t.timelineTitle}</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">{t.noActiveTask}</p>
      </div>
    );
  }

  const steps = [
    {
      key: 'planner',
      number: 1,
      title: t.stepPlanner,
      output: task.planner_output,
      desc: lang === 'uz' ? 'Topshiriq tahlili va amallar ketma-ketligi' : 'Task analysis and execution schedule',
      summary: task.planner_output
        ? lang === 'uz'
          ? 'Reja va tool ko\'rsatmalari shakllantirildi'
          : 'Plan and tool invocations generated'
        : null,
      duration: task.step_durations?.planner,
    },
    {
      key: 'doer',
      number: 2,
      title: t.stepDoer,
      output: task.doer_output,
      desc: lang === 'uz' ? 'Tool va brauzer orqali amallarni bajarish' : 'Tool invocation and browser interactions',
      summary: task.doer_output
        ? lang === 'uz'
          ? 'Tool buyruqlari ijro etildi va skrinshot olindi'
          : 'Tool executed and snapshot captured'
        : null,
      duration: task.step_durations?.doer,
    },
    {
      key: 'checker',
      number: 3,
      title: t.stepChecker,
      output: task.checker_output,
      desc: lang === 'uz' ? 'Dalil va skrinshotni tasdiqlash' : 'Evidence and visual snapshot validation',
      summary: task.checker_output
        ? lang === 'uz'
          ? 'check_goal va nishon dalili sinovdan o\'tkazildi'
          : 'check_goal and artifact verified'
        : null,
      duration: task.step_durations?.checker,
    },
  ];

  const getStepStatus = (stepKey: string) => {
    if (task.status === 'FAIL') return 'FAIL';
    if (task.current_step === stepKey) return task.status; // working or PASS or idle
    
    // Check if passed already
    if (stepKey === 'planner' && (task.planner_output || task.current_step === 'doer' || task.current_step === 'checker' || task.current_step === 'completed')) {
      return 'PASS';
    }
    if (stepKey === 'doer' && (task.doer_output || task.current_step === 'checker' || task.current_step === 'completed')) {
      return 'PASS';
    }
    if (stepKey === 'checker' && (task.checker_output || task.current_step === 'completed')) {
      return task.status === 'PASS' ? 'PASS' : task.status;
    }
    return 'idle';
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PASS':
        return (
          <span className="flex items-center space-x-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>{t.pass}</span>
          </span>
        );
      case 'working':
        return (
          <span className="flex items-center space-x-1 text-[11px] font-semibold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-full border border-blue-500/20">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
            <span>{t.working}</span>
          </span>
        );
      case 'FAIL':
        return (
          <span className="flex items-center space-x-1 text-[11px] font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20">
            <ShieldAlert className="w-3 h-3 text-rose-400" />
            <span>{t.fail}</span>
          </span>
        );
      case 'BLOCKED':
        return (
          <span className="flex items-center space-x-1 text-[11px] font-semibold text-orange-400 bg-orange-500/10 px-2 py-0.5 rounded-full border border-orange-500/20">
            <AlertCircle className="w-3 h-3 text-orange-400" />
            <span>BLOCKED</span>
          </span>
        );
      case 'needs approval':
        return (
          <span className="flex items-center space-x-1 text-[11px] font-semibold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
            <AlertCircle className="w-3 h-3 text-amber-400" />
            <span>{t.needsApproval}</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center space-x-1 text-[11px] font-medium text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full border border-slate-700/60">
            <Clock className="w-3 h-3 text-slate-500" />
            <span>{t.idle}</span>
          </span>
        );
    }
  };

  const isVerifiedPass = Boolean(task.evidence && task.status === 'PASS');

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg">
      {/* Top Header with Total Duration & Telemetry */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="font-bold text-sm text-slate-200">{t.timelineTitle}</h3>
            <span className="text-xs font-mono text-slate-500">[{task.task_id}]</span>
            {task.total_duration ? (
              <span className="flex items-center space-x-1 text-[10px] font-mono text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded-full border border-cyan-800/80">
                <Timer className="w-3 h-3 text-cyan-400" />
                <span>Jami: {task.total_duration}s</span>
              </span>
            ) : null}
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            <span className="font-medium text-blue-400 capitalize">{task.target_agent}</span>: {task.title}
          </p>
        </div>
        <div>{getStatusBadge(task.status)}</div>
      </div>

      {/* Visual Step Progress Bar */}
      <div className="mt-4 pt-1 pb-3 px-2 flex items-center justify-between border-b border-slate-800/60">
        {steps.map((st, idx) => {
          const status = getStepStatus(st.key);
          const isPassed = status === 'PASS';
          const isWorking = status === 'working';

          return (
            <React.Fragment key={st.key}>
              <div className="flex items-center space-x-2">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold transition-all ${
                    isPassed
                      ? 'bg-emerald-500 text-slate-950 ring-2 ring-emerald-400/40'
                      : isWorking
                      ? 'bg-blue-500 text-white animate-pulse ring-2 ring-blue-400/50'
                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}
                >
                  {isPassed ? <Check className="w-3.5 h-3.5 stroke-[2.5]" /> : st.number}
                </div>
                <div className="hidden sm:block">
                  <div className="text-[11px] font-semibold text-slate-300">{st.title}</div>
                  {st.duration ? (
                    <div className="text-[9px] font-mono text-cyan-400">{st.duration}s</div>
                  ) : null}
                </div>
              </div>
              {idx < steps.length - 1 && (
                <div
                  className={`flex-1 mx-3 h-0.5 rounded transition-all ${
                    isPassed ? 'bg-emerald-500/80' : 'bg-slate-800'
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Steps List with Intermediate Summaries */}
      <div className="mt-4 space-y-3 relative before:absolute before:inset-0 before:left-3.5 before:w-0.5 before:bg-slate-800 before:z-0">
        {steps.map((st) => {
          const status = getStepStatus(st.key);
          const isExpanded = expandedStep === st.key;

          return (
            <div
              key={st.key}
              className={`relative z-10 border rounded-xl overflow-hidden transition-all ${
                status === 'working'
                  ? 'bg-slate-950/90 border-blue-500/50 shadow-md ring-1 ring-blue-500/20'
                  : 'bg-slate-950/70 border-slate-800/80'
              }`}
            >
              <button
                onClick={() => setExpandedStep(isExpanded ? null : st.key)}
                className="w-full p-3 flex items-center justify-between hover:bg-slate-800/30 transition text-left"
              >
                <div className="flex items-center space-x-3">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs ${
                      status === 'PASS'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : status === 'working'
                        ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30 animate-pulse'
                        : status === 'FAIL'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : 'bg-slate-800 text-slate-500 border border-slate-700'
                    }`}
                  >
                    {st.key[0].toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="text-xs font-semibold text-slate-200">{st.title}</h4>
                      {st.duration ? (
                        <span className="text-[10px] font-mono text-cyan-400 bg-slate-900 px-1.5 py-0.2 rounded border border-slate-800">
                          {st.duration}s
                        </span>
                      ) : null}
                    </div>
                    {/* Oraliq xulosa (Intermediate Summary) */}
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      {st.summary || st.desc}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  {getStatusBadge(status)}
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-slate-500" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  )}
                </div>
              </button>

              {isExpanded && (
                <div className="p-3 border-t border-slate-800/60 bg-slate-900/50 text-xs">
                  {st.output ? (
                    <div className="relative group">
                      <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-slate-800/50">
                        <span className="text-[10px] font-mono text-slate-500">
                          {lang === 'uz' ? 'Oraliq xulosa va ijro chiqishi:' : 'Intermediate step output:'}
                        </span>
                        <button
                          onClick={() => handleCopy(st.key, st.output)}
                          className="flex items-center space-x-1 text-[10px] text-slate-400 hover:text-slate-200 transition bg-slate-800 px-2 py-0.5 rounded"
                        >
                          {copiedStep === st.key ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-400" />
                              <span className="text-emerald-400">Nusxalandi</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              <span>Nusxa olish</span>
                            </>
                          )}
                        </button>
                      </div>
                      <pre className="text-slate-300 font-mono text-[11px] whitespace-pre-wrap leading-relaxed max-h-56 overflow-y-auto">
                        {st.output}
                      </pre>
                    </div>
                  ) : (
                    <p className="text-slate-500 italic text-[11px]">
                      {status === 'working' ? `${t.working}...` : 'Hali natija yo\'q'}
                    </p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Dalilga asoslangan tasdiq (Evidence-based verification card) */}
      <div className={`mt-4 p-3.5 rounded-xl border flex items-start space-x-3 ${
        isVerifiedPass
          ? 'bg-emerald-950/20 border-emerald-500/40 shadow-sm'
          : task.status === 'FAIL'
          ? 'bg-rose-950/20 border-rose-500/40'
          : 'bg-slate-950/90 border-slate-800'
      }`}>
        {isVerifiedPass ? (
          <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
        ) : task.status === 'FAIL' ? (
          <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
        ) : (
          <FileText className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
        )}

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-200 uppercase tracking-wide">
              {t.evidence}:
            </span>
            <span
              className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                isVerifiedPass
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono'
                  : task.status === 'FAIL'
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 font-mono'
                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono'
              }`}
            >
              {isVerifiedPass
                ? 'EVIDENCE VERIFIED (PASS)'
                : task.status === 'FAIL'
                ? 'VERIFICATION FAILED'
                : 'DALILSIZ PASS RAD ETILADI'}
            </span>
          </div>

          <p className="text-xs text-slate-300 mt-1.5 font-mono leading-relaxed">
            {task.evidence || "Dalil faqat checker bosqichida skrinshot va parametrlar to'liq o'tgandan keyin belgilanadi. Dalilsiz PASS qat'iy rad etiladi."}
          </p>

          {task.screenshot_url && (
            <div className="mt-2 flex items-center space-x-2 text-[11px] text-cyan-400">
              <span className="font-semibold">Skrinshot artefakti:</span>
              <a
                href={task.screenshot_url}
                target="_blank"
                rel="noreferrer"
                className="underline flex items-center space-x-1 hover:text-cyan-300"
              >
                <span>{task.screenshot_url}</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
