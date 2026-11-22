'use client';

import React, { useState } from 'react';
import { Bot, Check, ArrowRight, Sparkles } from 'lucide-react';
import { Language } from '@/lib/translations';

export interface EngineInfo {
  name?: string;
  binary?: string;
  available?: boolean;
  note?: string;
  install_url?: string;
}

interface AgentChoiceModalProps {
  isOpen: boolean;
  engines: string[];
  engineInfo: Record<string, EngineInfo>;
  current: string;
  lang: Language;
  onSelect: (key: string) => void;
  onSkip: () => void;
}

export const AgentChoiceModal: React.FC<AgentChoiceModalProps> = ({
  isOpen, engines, engineInfo, current, lang, onSelect, onSkip,
}) => {
  const [chosen, setChosen] = useState(current || engines[0] || 'agy');
  if (!isOpen) return null;

  const selectedReady = engineInfo[chosen]?.available === true;

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center p-6 bg-[#070a10]/95 backdrop-blur-md">
      <div
        role="dialog"
        aria-modal="true"
        aria-label={lang === 'uz' ? 'AI agentni tanlash' : 'Choose AI agent'}
        className="w-full max-w-3xl max-h-[92vh] overflow-y-auto rounded-2xl border border-white/10 bg-[#111720] shadow-2xl"
      >
        <div className="px-6 pt-6 pb-4 border-b border-white/10">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/25 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-white">
                {lang === 'uz' ? 'Qaysi AI agentdan foydalanasiz?' : 'Which AI agent will you use?'}
              </h1>
              <p className="text-sm text-slate-400 mt-1">
                {lang === 'uz'
                  ? 'Studiya butunlay shu agent bilan ishlaydi: terminal, vazifalar va natijalar.'
                  : 'The whole studio works with this agent: terminal, tasks and results.'}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6">
          {engines.length === 0 ? (
            <p className="text-sm text-slate-400">{lang === 'uz' ? 'Agentlar yuklanmoqda...' : 'Loading agents...'}</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {engines.map((key) => {
                const info = engineInfo[key] || {};
                const active = chosen === key;
                return (
                  <button
                    key={key}
                    onClick={() => setChosen(key)}
                    aria-pressed={active}
                    className={`text-left p-3 rounded-xl border transition ${
                      active
                        ? 'border-blue-500/50 bg-blue-500/10'
                        : 'border-white/10 bg-white/[0.03] hover:bg-white/[0.06]'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center space-x-3 min-w-0">
                        <div className="w-9 h-9 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center shrink-0">
                          <Bot className="w-4 h-4 text-blue-400" />
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-white truncate">
                            {info.name || key}
                          </p>
                          <p className="text-[11px] font-mono text-slate-500 truncate">{key}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 shrink-0">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${
                          info.available
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-white/5 text-slate-500 border-white/10'
                        }`}>
                          {info.available ? (lang === 'uz' ? 'TAYYOR' : 'READY') : (lang === 'uz' ? 'YO‘Q' : 'MISSING')}
                        </span>
                        {active && <Check className="w-4 h-4 text-blue-400" />}
                      </div>
                    </div>
                    {info.note && (
                      <p className="text-[11px] text-slate-500 mt-3 line-clamp-2">{info.note}</p>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          <div className="flex items-center justify-between gap-4 mt-6 pt-4 border-t border-white/10">
            <button
              onClick={onSkip}
              className="px-4 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-white/5 transition"
            >
              {lang === 'uz' ? 'Keyinroq sozlash' : 'Configure later'}
            </button>
            {!selectedReady && (
              <p className="text-xs text-amber-400">
                {lang === 'uz' ? 'Bu agent CLI topilmadi — ' : 'This agent CLI is missing — '}
                {engineInfo[chosen]?.install_url ? (
                  <a
                    href={engineInfo[chosen].install_url}
                    target="_blank"
                    rel="noreferrer"
                    className="underline hover:text-amber-300"
                  >
                    {lang === 'uz' ? 'o‘rnatish yo‘riqnomasi' : 'installation guide'}
                  </a>
                ) : (lang === 'uz' ? 'avval uni o‘rnating.' : 'install it first.')}
              </p>
            )}
            <button
              onClick={() => onSelect(chosen)}
              disabled={!chosen || !selectedReady}
              className="btn-accent flex items-center space-x-2 px-6 py-2.5 rounded-lg text-sm font-semibold text-white disabled:opacity-40"
            >
              <span>{lang === 'uz' ? 'Bu agent bilan ishlash' : 'Work with this agent'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
