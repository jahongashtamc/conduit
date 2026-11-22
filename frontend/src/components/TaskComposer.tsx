'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { X, Send, Sparkles, Box, ScanSearch, Palette, Film, Cpu } from 'lucide-react';
import { Language } from '@/lib/translations';

export interface SubagentInfo {
  id: string;
  name?: string;
  display_name_uz?: string;
  display_name_en?: string;
  role_desc_uz?: string;
  role_desc_en?: string;
  target_app?: string;
  status?: string;
}

interface TaskComposerProps {
  isOpen: boolean;
  onClose: () => void;
  subagents: SubagentInfo[];
  initialAgent?: string | null;
  kernelMode: string;
  onDispatch: (prompt: string, agent: string, mode: string) => void | Promise<void>;
  lang: Language;
}

const MODES = ['standard', 'eepx', 'super_agent', 'deepx'] as const;

const TEMPLATES: Array<{ key: string; prompt: string; agent: string; icon: React.ComponentType<{ className?: string }> }> = [
  { key: 'web', prompt: 'Saytni ochib tahlil qil va skrinshot ol', agent: 'scout', icon: ScanSearch },
  { key: '3d', prompt: 'Oddiy 3D model yarat va render ol', agent: 'sculptor', icon: Box },
  { key: 'audit', prompt: 'Tizim salomatligini tekshir', agent: 'inspector', icon: Cpu },
  { key: 'ui', prompt: 'UI dizayn tizimi va tokenlarni sinxronizatsiya qil', agent: 'designer', icon: Palette },
  { key: 'video', prompt: 'Qisqa animatsiya/video klip yarat', agent: 'animator', icon: Film },
];

export const TaskComposer: React.FC<TaskComposerProps> = ({
  isOpen,
  onClose,
  subagents,
  initialAgent,
  kernelMode,
  onDispatch,
  lang,
}) => {
  const preferred = initialAgent && subagents.some((a) => a.id === initialAgent)
    ? initialAgent
    : (subagents[0]?.id || '');
  const [prompt, setPrompt] = useState('');
  const [agent, setAgent] = useState(preferred);
  const [mode, setMode] = useState<string>(kernelMode || 'standard');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  const canSubmit = useMemo(() => prompt.trim().length > 2 && !!agent && !busy, [prompt, agent, busy]);

  if (!isOpen) return null;

  const submit = async () => {
    if (!canSubmit) return;
    setBusy(true);
    try {
      await onDispatch(prompt.trim(), agent, mode);
      setPrompt('');
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center p-6 bg-black/70 backdrop-blur-sm"
      onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={lang === 'uz' ? 'Yangi vazifa' : 'New task'}
        className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-white/10 bg-[#111720] shadow-2xl"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div>
            <h2 className="text-lg font-semibold text-white flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-blue-400" />
              <span>{lang === 'uz' ? 'Yangi vazifa yaratish' : 'Create new task'}</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              {lang === 'uz' ? 'Agent, rejim va vazifani tanlang' : 'Choose an agent, mode and task'}
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Yopish"
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* Shablonlar */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
              {lang === 'uz' ? 'Tezkor shablonlar' : 'Quick templates'}
            </p>
            <div className="flex flex-wrap gap-2">
              {TEMPLATES.map((t) => {
                const Icon = t.icon;
                return (
                  <button
                    key={t.key}
                    onClick={() => { setPrompt(t.prompt); setAgent(t.agent); }}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-slate-300 hover:text-white hover:border-blue-500/40 hover:bg-white/10 transition"
                  >
                    <Icon className="w-3.5 h-3.5 text-blue-400" />
                    <span>{t.key.toUpperCase()}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Vazifa matni */}
          <div>
            <label htmlFor="composer-prompt" className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
              {lang === 'uz' ? 'Vazifa' : 'Task'}
            </label>
            <textarea
              id="composer-prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); void submit(); }
              }}
              rows={5}
              autoFocus
              placeholder={lang === 'uz' ? 'Agentga aniq vazifani yozing... (Ctrl+Enter — yuborish)' : 'Describe the task precisely... (Ctrl+Enter to send)'}
              className="w-full resize-none rounded-xl bg-[#0d1117] border border-white/10 px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Agent */}
            <div>
              <label htmlFor="composer-agent" className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                {lang === 'uz' ? 'Ijrochi agent' : 'Executing agent'}
              </label>
              <select
                id="composer-agent"
                value={agent}
                onChange={(e) => setAgent(e.target.value)}
                className="w-full rounded-xl bg-[#0d1117] border border-white/10 px-3 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50"
              >
                {subagents.map((a) => (
                  <option key={a.id} value={a.id}>
                    {(lang === 'uz' ? a.display_name_uz : a.display_name_en) || a.name || a.id}
                    {a.status === 'active' ? '  ✓' : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* Rejim */}
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                {lang === 'uz' ? 'Yadro rejimi' : 'Kernel mode'}
              </p>
              <div className="grid grid-cols-2 gap-2">
                {MODES.map((m) => (
                  <button
                    key={m}
                    onClick={() => setMode(m)}
                    aria-pressed={mode === m}
                    className={`px-2 py-2 rounded-lg border text-xs font-mono transition ${
                      mode === m
                        ? 'border-blue-500/50 bg-blue-500/10 text-white'
                        : 'border-white/10 bg-white/5 text-slate-400 hover:text-white'
                    }`}
                  >
                    {m.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end space-x-3 px-6 py-4 border-t border-white/10">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-white/5 transition"
          >
            {lang === 'uz' ? 'Bekor qilish' : 'Cancel'}
          </button>
          <button
            onClick={() => void submit()}
            disabled={!canSubmit}
            className="btn-accent flex items-center space-x-2 px-5 py-2 rounded-lg text-sm font-semibold text-white disabled:opacity-40 transition"
          >
            <Send className="w-4 h-4" />
            <span>{busy ? (lang === 'uz' ? 'Yuborilmoqda...' : 'Dispatching...') : (lang === 'uz' ? 'Ishga tushirish' : 'Dispatch')}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
