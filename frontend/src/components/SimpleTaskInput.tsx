'use client';

import React, { useState } from 'react';
import { Send, CornerDownLeft, Loader2, Sparkles } from 'lucide-react';
import { Language } from '@/lib/translations';

interface SimpleTaskInputProps {
  onSubmit: (prompt: string) => Promise<void>;
  lang: Language;
  isLoading: boolean;
  isAgentConnected?: boolean;
}

export const SimpleTaskInput: React.FC<SimpleTaskInputProps> = ({
  onSubmit,
  lang,
  isLoading,
  isAgentConnected = true,
}) => {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prompt.trim() || isLoading || !isAgentConnected) return;
    const currentPrompt = prompt;
    setPrompt('');
    await onSubmit(currentPrompt);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey || !e.shiftKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const presets = [
    { label: "Google'dan qidir", text: "Google'dan Conduit haqida qidir, skrinshot ol va tekshir" },
    { label: "Figma dizayn tizimi", text: "Figma dizayn tizimini tuzat va PC app spec yarat" },
    { label: "Yangi ilova (Notion)", text: "Notion'dagi loyiha sahifasini tekshir" },
  ];

  return (
    <div className="bg-slate-900/80 border border-white/[0.08] rounded-2xl p-4 shadow-xl backdrop-blur-xl">
      <form onSubmit={handleSubmit} className="relative">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={lang === 'uz' ? "Vazifani yozing (Bosh agent o'zi rejalashtirib, kerakli subagentga topshiradi)..." : "Enter task (Core agent will route and execute)..."}
          rows={3}
          className="w-full bg-slate-950/80 border border-white/[0.06] rounded-xl p-3.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500/80 focus:ring-2 focus:ring-blue-500/20 transition resize-none"
        />

        <div className="flex flex-wrap items-center justify-between gap-2 mt-3">
          {/* Quick Preset Chips */}
          <div className="flex items-center space-x-1.5 overflow-x-auto py-1">
            <span className="text-[11px] text-slate-500 flex items-center space-x-1 mr-1">
              <Sparkles className="w-3 h-3 text-blue-400" />
            </span>
            {presets.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setPrompt(p.text)}
                className="text-[11px] px-2.5 py-1 rounded-full bg-white/[0.04] hover:bg-blue-600/20 hover:text-blue-300 text-slate-400 border border-white/[0.06] transition whitespace-nowrap"
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!prompt.trim() || isLoading || !isAgentConnected}
            className={`flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition active:scale-95 shadow-md ${
              !isAgentConnected
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                : isLoading
                ? 'bg-blue-600/50 text-white cursor-wait'
                : prompt.trim()
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-500 hover:to-indigo-500 shadow-blue-500/20'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>{lang === 'uz' ? 'Bajarilmoqda...' : 'Running...'}</span>
              </>
            ) : (
              <>
                <span>{lang === 'uz' ? 'Yuborish' : 'Send'}</span>
                <Send className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
