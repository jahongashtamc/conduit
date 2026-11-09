'use client';

import React from 'react';
import { Brain, Heart, ArrowRight, CheckCircle2, XCircle, Clock, Zap, ShieldAlert, Sparkles, Activity, RotateCcw, Layers } from 'lucide-react';
import { Language } from '@/lib/translations';

export interface BrainPlanStep {
  step: number;
  agent: string;
  title: string;
  status: 'pending' | 'active' | 'PASS' | 'FAIL';
  description?: string;
}

export interface BrainState {
  task_id: string;
  goal: string;
  thought?: string;
  plan?: BrainPlanStep[];
  active_subagent?: string | null;
  active_command?: {
    to: string;
    task: string;
    expected_evidence: string;
  } | null;
  last_report?: {
    from_agent: string;
    status: 'PASS' | 'FAIL' | 'BLOCKED';
    evidence: string;
    notes: string;
    screenshot_url?: string;
  } | null;
  short_memory?: Array<{
    timestamp: string;
    decision: string;
    error?: string | null;
    result?: string | null;
  }>;
  status?: string;
  attempt?: number;
}

interface BrainPanelProps {
  state: BrainState | null;
  lang: Language;
}

export const BrainPanel: React.FC<BrainPanelProps> = ({ state, lang }) => {
  if (!state || (!state.thought && (!state.plan || state.plan.length === 0))) {
    return (
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 mb-6 backdrop-blur-md">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-200">
                {lang === 'uz' ? 'Bosh Agent (Miya + Yurak)' : 'Core Agent (Brain & Heartbeat)'}
              </h3>
              <p className="text-xs text-slate-500">
                {lang === 'uz' ? 'Kutish rejimida. Vazifa kelganda faollashadi.' : 'Idle mode. Activates on goal dispatch.'}
              </p>
            </div>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
            IDLE
          </span>
        </div>
      </div>
    );
  }

  const isSuccess = state.status === 'PASS';
  const isFailed = state.status === 'FAIL';
  const isBlocked = state.status === 'BLOCKED';
  const isWorking = !isSuccess && !isFailed && !isBlocked;

  const [rollbackMsg, setRollbackMsg] = React.useState<string | null>(null);

  const handleRollback = async () => {
    if (!state.task_id) return;
    try {
      const res = await fetch(`/api/heart/rollback/${state.task_id}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setRollbackMsg(`Qaytarildi: ${data.rollback?.step_name || 'Checkpoint'}`);
        setTimeout(() => setRollbackMsg(null), 3000);
      } else {
        setRollbackMsg('Checkpoint topilmadi');
        setTimeout(() => setRollbackMsg(null), 3000);
      }
    } catch {
      setRollbackMsg('Qaytishda xatolik');
      setTimeout(() => setRollbackMsg(null), 3000);
    }
  };

  return (
    <div className="bg-gradient-to-b from-slate-900/90 to-slate-950/90 border border-purple-500/30 rounded-2xl p-5 mb-6 shadow-2xl backdrop-blur-xl relative overflow-hidden transition-all duration-300">
      {/* Glow background accent */}
      <div className="absolute -top-16 -right-16 w-48 h-48 bg-purple-600/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-16 -left-16 w-48 h-48 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 mb-4 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600/20 to-cyan-500/20 border border-purple-500/40 flex items-center justify-center text-purple-400 relative">
            <Brain className="w-5 h-5 animate-pulse" />
            <span className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-rose-500/20 border border-rose-500/50 flex items-center justify-center text-rose-400">
              <Heart className="w-2.5 h-2.5 animate-ping" />
            </span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                {lang === 'uz' ? 'Bosh Agent (Miya + Yurak)' : 'Core Agent (Brain & Heartbeat)'}
                <Sparkles className="w-4 h-4 text-amber-400" />
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
                AYLANISH {state.attempt || 1}/3
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                MAX 8 QADAM
              </span>
            </div>
            <p className="text-xs text-slate-400 truncate max-w-lg mt-0.5">
              <span className="text-slate-500 font-medium">Maqsad:</span> {state.goal}
            </p>
          </div>
        </div>

        {/* Status Pill & Rollback Button */}
        <div className="flex items-center gap-2">
          {rollbackMsg && (
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30 animate-pulse">
              {rollbackMsg}
            </span>
          )}
          <button
            onClick={handleRollback}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title="Oxirgi yaxshi qadamga qaytish"
          >
            <RotateCcw className="w-3 h-3 text-cyan-400" />
            <span className="text-[11px]">{lang === 'uz' ? 'Oxirgi qadamga qayt' : 'Rollback Checkpoint'}</span>
          </button>

          {isWorking && (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              <Activity className="w-3.5 h-3.5 animate-spin" />
              {state.status || 'RUNNING'}
            </span>
          )}
          {isSuccess && (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              <CheckCircle2 className="w-3.5 h-3.5" />
              PASS — Maqsad Bajarildi
            </span>
          )}
          {isBlocked && (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
              <ShieldAlert className="w-3.5 h-3.5" />
              BLOCKED — Cheklov To'xtatdi
            </span>
          )}
          {isFailed && (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
              <XCircle className="w-3.5 h-3.5" />
              FAIL — To'xtatildi
            </span>
          )}
        </div>
      </div>

      {/* Grid: 1. Thought | 2. Plan */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 mb-4">
        {/* Thought (Miya hozir nimani o'ylayapti) */}
        <div className="lg:col-span-6 bg-slate-950/60 border border-purple-500/20 rounded-xl p-3.5 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2 text-xs font-semibold uppercase tracking-wider text-purple-400">
              <Zap className="w-3.5 h-3.5" />
              {lang === 'uz' ? 'Hozir nima o\'ylayapti' : 'Current Brain Thought'}
            </div>
            <div className="text-xs text-slate-200 leading-relaxed font-sans bg-purple-950/20 rounded-lg p-2.5 border border-purple-500/10">
              {state.thought || (lang === 'uz' ? 'Reja tahlil qilinmoqda...' : 'Analyzing plan...')}
            </div>
          </div>
          {state.active_subagent && (
            <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
              <span className="text-slate-400">Faol ijrochi subagent:</span>
              <span className="font-semibold text-cyan-400 uppercase bg-cyan-950/50 px-2 py-0.5 rounded border border-cyan-500/30 flex items-center gap-1.5 animate-pulse">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                {state.active_subagent}
              </span>
            </div>
          )}
        </div>

        {/* Operativ Reja (Plan) */}
        <div className="lg:col-span-6 bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5">
          <div className="flex items-center gap-2 mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            {lang === 'uz' ? 'Tuzilgan Reja' : 'Formulated Plan'}
          </div>
          <div className="space-y-2">
            {state.plan && state.plan.length > 0 ? (
              state.plan.map((step, idx) => {
                const isStepPass = step.status === 'PASS';
                const isStepActive = step.status === 'active' || (state.active_subagent?.toLowerCase() === step.agent.toLowerCase() && isWorking);
                return (
                  <div
                    key={idx}
                    className={`flex items-start gap-2.5 p-2 rounded-lg text-xs transition-all border ${
                      isStepPass
                        ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-200'
                        : isStepActive
                        ? 'bg-cyan-950/30 border-cyan-500/40 text-cyan-200'
                        : 'bg-slate-900/40 border-slate-800/60 text-slate-400'
                    }`}
                  >
                    <span
                      className={`w-5 h-5 rounded-full flex items-center justify-center font-mono text-[10px] font-bold shrink-0 mt-0.5 ${
                        isStepPass
                          ? 'bg-emerald-500 text-slate-950'
                          : isStepActive
                          ? 'bg-cyan-500 text-slate-950 animate-pulse'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {isStepPass ? '✓' : step.step}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-200">{step.title}</span>
                        <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-400">
                          {step.agent}
                        </span>
                      </div>
                      {step.description && (
                        <p className="text-[11px] text-slate-400 mt-0.5 truncate">{step.description}</p>
                      )}
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-xs text-slate-500 py-3 text-center">
                {lang === 'uz' ? 'Reja tuzilmoqda...' : 'Formulating plan...'}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Buyruq va hisobot protokoli (Command & Report Card) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1 border-t border-slate-800/60">
        {/* Active Command (Miya -> Subagent) */}
        <div className="bg-slate-950/40 border border-cyan-500/20 rounded-xl p-3">
          <div className="flex items-center justify-between mb-1.5 text-[11px]">
            <span className="font-semibold text-cyan-400 flex items-center gap-1.5">
              <ArrowRight className="w-3 h-3 text-cyan-400" />
              {lang === 'uz' ? 'Oxirgi Buyruq (Miya → Subagent)' : 'Dispatched Command'}
            </span>
            {state.active_command && (
              <span className="font-mono text-[10px] text-cyan-300 bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-500/30">
                To: {state.active_command.to}
              </span>
            )}
          </div>
          {state.active_command ? (
            <div className="space-y-1 text-xs">
              <p className="text-slate-200 line-clamp-2">{state.active_command.task}</p>
              <p className="text-[10px] text-slate-400">
                <span className="text-slate-500">Kutilayotgan dalil:</span>{' '}
                <span className="font-mono text-cyan-300">{state.active_command.expected_evidence}</span>
              </p>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">
              {lang === 'uz' ? 'Hozirda yangi buyruq yuborilmagan' : 'No active command'}
            </p>
          )}
        </div>

        {/* Subagent Report (Subagent -> Miya) */}
        <div className="bg-slate-950/40 border border-slate-800 rounded-xl p-3">
          <div className="flex items-center justify-between mb-1.5 text-[11px]">
            <span className="font-semibold text-slate-300 flex items-center gap-1.5">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              {lang === 'uz' ? 'Subagent Hisoboti (Subagent → Miya)' : 'Subagent Report'}
            </span>
            {state.last_report && (
              <span
                className={`font-mono text-[10px] px-1.5 py-0.5 rounded font-bold border ${
                  state.last_report.status === 'PASS'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                }`}
              >
                {state.last_report.from_agent.toUpperCase()}: {state.last_report.status}
              </span>
            )}
          </div>
          {state.last_report ? (
            <div className="space-y-1 text-xs">
              <p className="text-slate-300 text-[11px] line-clamp-2">{state.last_report.evidence}</p>
              {state.last_report.notes && (
                <p className="text-[10px] text-slate-400">
                  <span className="text-slate-500">Izoh:</span> {state.last_report.notes}
                </p>
              )}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">
              {lang === 'uz' ? 'Hisobot kutilmoqda...' : 'Waiting for report...'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
