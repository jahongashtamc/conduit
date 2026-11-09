'use client';

import React, { useState } from 'react';
import { 
  Activity, 
  CheckCircle2, 
  AlertCircle, 
  XCircle, 
  Layers, 
  ArrowRight, 
  Maximize2, 
  X, 
  ExternalLink,
  Bot,
  RotateCcw,
  Image as ImageIcon
} from 'lucide-react';
import { Language } from '@/lib/translations';

interface SimpleAgentStatusProps {
  task: any | null;
  brainState: any | null;
  lang: Language;
  onRetry?: () => void;
  isRetrying?: boolean;
}

export const SimpleAgentStatus: React.FC<SimpleAgentStatusProps> = ({
  task,
  brainState,
  lang,
  onRetry,
  isRetrying = false,
}) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [imgError, setImgError] = useState(false);

  // If no task has ever been dispatched
  if (!task && !brainState) {
    return (
      <div className="bg-slate-900/60 border border-white/[0.08] rounded-2xl p-6 text-center backdrop-blur-md">
        <div className="w-10 h-10 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center mx-auto mb-3">
          <Bot className="w-5 h-5" />
        </div>
        <h3 className="text-sm font-semibold text-slate-200">
          {lang === 'uz' ? 'Bosh Agent Tayyor' : 'Core Agent Ready'}
        </h3>
        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
          {lang === 'uz' 
            ? 'Vazifangizni yozing. Bosh agent tegishli subagentlarni tanlab, qadamlarni o\'zi muvofiqlashtiradi.' 
            : 'Enter a task. The core agent will automatically orchestrate subagents and deliver verified evidence.'}
        </p>
      </div>
    );
  }

  const status = (task?.status || brainState?.status || 'working').toUpperCase();
  const isPass = status === 'PASS';
  const isBlocked = status === 'BLOCKED';
  const isFail = status === 'FAIL';
  const isWorking = !isPass && !isBlocked && !isFail;

  const activeSubagent = (brainState?.active_subagent || task?.target_agent || 'Manager').toUpperCase();
  const stepCount = brainState?.step_count ?? (task?.current_step === 'completed' ? 2 : 1);
  const loopCount = brainState?.attempt ?? 1;
  const thought = brainState?.thought || task?.prompt;
  const plan = brainState?.plan || [];
  const screenshotUrl = task?.screenshot_url;
  const evidence = task?.evidence || brainState?.last_report?.evidence;

  return (
    <div className="space-y-4">
      {/* 1. Bosh Agent Qisqa Holati Card */}
      <div className={`rounded-2xl p-5 border backdrop-blur-xl transition-all duration-300 shadow-xl ${
        isPass
          ? 'bg-slate-900/90 border-emerald-500/30'
          : isBlocked
          ? 'bg-slate-900/90 border-amber-500/30'
          : isFail
          ? 'bg-slate-900/90 border-rose-500/30'
          : 'bg-slate-900/90 border-blue-500/30'
      }`}>
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          {/* Status Badge */}
          <div className="flex items-center space-x-2.5">
            {isWorking ? (
              <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-blue-500/10 text-blue-300 border border-blue-500/30 text-xs font-semibold">
                <Activity className="w-3.5 h-3.5 animate-spin" />
                <span>{activeSubagent} {lang === 'uz' ? 'ishlayapti' : 'working'}: {stepCount}/8 {lang === 'uz' ? 'qadam' : 'step'}</span>
              </span>
            ) : isPass ? (
              <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 text-xs font-bold">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>PASS — {lang === 'uz' ? 'Muvaffaqiyatli yakunlandi' : 'Completed Successfully'}</span>
              </span>
            ) : isBlocked ? (
              <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30 text-xs font-bold">
                <AlertCircle className="w-4 h-4 text-amber-400" />
                <span>BLOCKED — {lang === 'uz' ? 'Vazifa to\'xtatildi' : 'Task Blocked'}</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-rose-500/15 text-rose-300 border border-rose-500/30 text-xs font-bold">
                <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                <span className="truncate max-w-sm">
                  FAIL {evidence?.includes("sabab:") ? evidence : (evidence ? `(sabab: ${evidence})` : '— Muvaffaqiyatsiz')}
                </span>
              </span>
            )}

            {/* Loop indicator */}
            <span className="text-[11px] font-mono text-slate-400 px-2 py-0.5 rounded bg-white/[0.04] border border-white/[0.06]">
              {lang === 'uz' ? 'Aylanish' : 'Loop'}: {loopCount}/3
            </span>

            {/* Qayta urinish tugmasi on FAIL / BLOCKED */}
            {onRetry && (isFail || isBlocked) && (
              <button
                type="button"
                onClick={onRetry}
                disabled={isRetrying}
                className="flex items-center space-x-1 px-3 py-1 rounded-full bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md transition active:scale-95 disabled:opacity-50"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${isRetrying ? 'animate-spin' : ''}`} />
                <span>{lang === 'uz' ? 'Qayta urinish' : 'Retry'}</span>
              </button>
            )}
          </div>

          <span className="text-[11px] font-mono text-slate-500">
            {task?.task_id}
          </span>
        </div>

        {/* Thought / Purpose */}
        {thought && (
          <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/50 p-3 rounded-xl border border-white/[0.05]">
            <span className="text-blue-400 font-semibold mr-1.5">
              {lang === 'uz' ? 'Bosh agent fikri:' : 'Brain thought:'}
            </span>
            {thought}
          </p>
        )}

        {/* Qadamlar Izi (Step Trail) */}
        {plan && plan.length > 0 && (
          <div className="mt-3.5 pt-3 border-t border-white/[0.06]">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center space-x-1">
              <Layers className="w-3 h-3 text-slate-500" />
              <span>{lang === 'uz' ? 'Qadamlar izi' : 'Execution steps'}</span>
            </div>
            <div className="flex flex-wrap items-center gap-1.5 text-xs">
              {plan.map((step: any, idx: number) => {
                const stepPass = step.status === 'PASS';
                const stepActive = step.status === 'active';
                return (
                  <React.Fragment key={idx}>
                    <div className={`px-2.5 py-1 rounded-lg border text-[11px] flex items-center space-x-1.5 ${
                      stepPass
                        ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                        : stepActive
                        ? 'bg-blue-500/20 text-blue-200 border-blue-500/40 ring-1 ring-blue-500/30'
                        : 'bg-white/[0.02] text-slate-400 border-white/[0.05]'
                    }`}>
                      <span className="font-bold">{step.step}.</span>
                      <span className="font-medium uppercase">{step.agent}</span>
                      <span className="text-slate-500">·</span>
                      <span className="text-slate-300">{step.title}</span>
                      {stepPass && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
                    </div>
                    {idx < plan.length - 1 && (
                      <ArrowRight className="w-3 h-3 text-slate-600 shrink-0" />
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* 2. Yakuniy Natija va Dalil Card */}
      {(evidence || (screenshotUrl && !imgError)) && (
        <div className="bg-slate-900/80 border border-white/[0.08] rounded-2xl p-5 shadow-xl backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-2.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-1.5">
              <span>{lang === 'uz' ? '📋 Yakuniy Natija va Dalil' : '📋 Final Result & Evidence'}</span>
            </h4>
            <span className="text-[11px] text-slate-400 font-mono">
              {isPass ? 'VERIFIED' : status}
            </span>
          </div>

          {/* Evidence Text */}
          {evidence && (
            <div className={`p-3.5 rounded-xl border text-xs leading-relaxed font-mono ${
              isPass
                ? 'bg-emerald-950/20 border-emerald-500/20 text-emerald-200'
                : isBlocked
                ? 'bg-amber-950/20 border-amber-500/20 text-amber-200'
                : 'bg-rose-950/20 border-rose-500/20 text-rose-200'
            }`}>
              {evidence}
            </div>
          )}

          {/* Valid Screenshot Preview (ONLY rendered if valid URL exists and no error) */}
          {screenshotUrl && !imgError && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>{lang === 'uz' ? 'Tasdiqlangan vizual skrinshot:' : 'Verified visual screenshot:'}</span>
                <button
                  onClick={() => setModalOpen(true)}
                  className="text-blue-400 hover:text-blue-300 flex items-center space-x-1 transition text-[11px]"
                >
                  <Maximize2 className="w-3 h-3" />
                  <span>{lang === 'uz' ? 'Kattalashtirish' : 'Zoom'}</span>
                </button>
              </div>

              <div 
                onClick={() => setModalOpen(true)}
                className="relative rounded-xl overflow-hidden border border-white/10 group cursor-pointer max-h-80 bg-slate-950"
              >
                <img
                  src={screenshotUrl}
                  alt="Verified evidence"
                  className="w-full h-auto object-cover group-hover:scale-[1.02] transition duration-300"
                  onError={() => setImgError(true)}
                />
                <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                  <span className="px-3 py-1.5 rounded-lg bg-slate-900/90 text-white text-xs font-semibold flex items-center space-x-1.5 border border-white/20">
                    <Maximize2 className="w-3.5 h-3.5" />
                    <span>{lang === 'uz' ? 'To\'liq o\'lchamda ko\'rish' : 'View full size'}</span>
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Modal for full size screenshot */}
      {modalOpen && screenshotUrl && !imgError && (
        <div 
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setModalOpen(false)}
        >
          <div 
            className="relative max-w-5xl max-h-[90vh] bg-slate-900 rounded-2xl border border-slate-700 overflow-hidden shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-3 border-b border-slate-800 flex items-center justify-between bg-slate-950/80">
              <span className="text-xs font-mono text-slate-300">
                {screenshotUrl}
              </span>
              <button
                onClick={() => setModalOpen(false)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-2 overflow-auto max-h-[80vh]">
              <img src={screenshotUrl} alt="Full evidence preview" className="w-full h-auto rounded-lg" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
