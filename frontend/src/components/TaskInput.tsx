'use client';

import React, { useState } from 'react';
import { Send, Sparkles, Compass, ShieldCheck, CornerDownLeft, Loader2, AlertCircle } from 'lucide-react';
import { Language, translations } from '@/lib/translations';

interface Subagent {
  id: string;
  name: string;
  display_name_uz: string;
  display_name_en: string;
  status: 'active' | 'later';
}

interface TaskInputProps {
  onSubmit: (prompt: string, targetAgent: string) => Promise<void>;
  subagents: Subagent[];
  lang: Language;
  isLoading: boolean;
  isAgentConnected?: boolean;
}

export const TaskInput: React.FC<TaskInputProps> = ({
  onSubmit,
  subagents,
  lang,
  isLoading,
  isAgentConnected = true,
}) => {
  const t = translations[lang];
  const [prompt, setPrompt] = useState('');
  const [targetAgent, setTargetAgent] = useState('auto');

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prompt.trim() || isLoading || !isAgentConnected) return;
    const currentPrompt = prompt;
    setPrompt('');
    await onSubmit(currentPrompt, targetAgent);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey || !e.shiftKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSuggestion = (preset: string, agent: string) => {
    setPrompt(preset);
    setTargetAgent(agent);
  };

  return (
    <div className="mb-6 bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-xl">
      <div className="flex items-center justify-between mb-2">
        <label className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
          <Sparkles className="w-3.5 h-3.5 text-blue-400" />
          <span>{t.taskInputTitle}</span>
        </label>

        {/* Subagent Selector */}
        <div className="flex items-center space-x-2">
          <span className="text-[11px] text-slate-400 hidden sm:inline">{t.targetAgent}:</span>
          <select
            value={targetAgent}
            onChange={(e) => setTargetAgent(e.target.value)}
            className="text-xs bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
          >
            <option value="auto">{t.autoRoute}</option>
            {subagents.map((s) => (
              <option key={s.id} value={s.id}>
                {lang === 'uz' ? s.display_name_uz : s.display_name_en} {s.status === 'later' ? '(Faza 4)' : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="relative">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t.taskInputPlaceholder}
          rows={3}
          className="w-full bg-slate-950/70 border border-slate-800 rounded-xl p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500/80 focus:ring-2 focus:ring-blue-500/20 transition resize-none"
        />

        <div className="flex items-center justify-between mt-2.5">
          <span className="text-[11px] text-slate-500 hidden sm:flex items-center space-x-1">
            <CornerDownLeft className="w-3 h-3 text-slate-600" />
            <span>{t.enterHint}</span>
          </span>

          <button
            type="submit"
            disabled={!prompt.trim() || isLoading || !isAgentConnected}
            className={`flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition active:scale-95 shadow-md ${
              !isAgentConnected
                ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30 cursor-not-allowed'
                : prompt.trim() && !isLoading
                ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-500/20'
                : 'bg-slate-800 text-slate-500 cursor-not-allowed'
            }`}
          >
            {!isAgentConnected ? (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                <span>{lang === 'uz' ? 'Agent ulanmagan' : 'Agent Disconnected'}</span>
              </>
            ) : isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>{t.working}...</span>
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>{t.sendButton}</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Quick Suggestions Chips */}
      <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5">
        <span className="text-[11px] font-medium text-slate-400 mr-1">{t.quickSuggestions}</span>
        
        <button
          onClick={() => handleSuggestion(t.suggestScoutGoogle, 'scout')}
          className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 text-[11px] text-slate-300 transition"
        >
          <Compass className="w-3 h-3 text-cyan-400" />
          <span>{t.suggestScoutGoogle}</span>
        </button>

        <button
          onClick={() => handleSuggestion(t.suggestInspectorAudit, 'inspector')}
          className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 text-[11px] text-slate-300 transition"
        >
          <ShieldCheck className="w-3 h-3 text-emerald-400" />
          <span>{t.suggestInspectorAudit}</span>
        </button>

        <button
          onClick={() => handleSuggestion(t.suggestDangerDelete, 'scout')}
          className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-[11px] text-rose-300 transition"
        >
          <Sparkles className="w-3 h-3 text-amber-400" />
          <span>{t.suggestDangerDelete}</span>
        </button>
      </div>
    </div>
  );
};
