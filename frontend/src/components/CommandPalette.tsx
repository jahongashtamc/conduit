'use client';

import React, { useState, useEffect } from 'react';
import { Search, Compass, ShieldCheck, Power, Globe, Terminal, X } from 'lucide-react';
import { Language, translations } from '@/lib/translations';

interface Subagent {
  id: string;
  name: string;
  display_name_uz: string;
  display_name_en: string;
  status: 'active' | 'later';
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  subagents: Subagent[];
  onSelectAgent: (id: string) => void;
  onKillAll: () => void;
  onToggleLang: () => void;
  onTriggerPreset: (prompt: string, agent: string) => void;
  lang: Language;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  subagents,
  onSelectAgent,
  onKillAll,
  onToggleLang,
  onTriggerPreset,
  lang,
}) => {
  const t = translations[lang];
  const [query, setQuery] = useState('');

  // Close on Escape, toggle on Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
      } else if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const filteredSubagents = subagents.filter(
    (s) =>
      s.name.toLowerCase().includes(query.toLowerCase()) ||
      s.display_name_uz.toLowerCase().includes(query.toLowerCase()) ||
      s.display_name_en.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-start justify-center pt-20 p-4">
      <div className="max-w-xl w-full bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Input box */}
        <div className="p-3.5 border-b border-slate-800 flex items-center space-x-3 bg-slate-950">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t.cmdSearch}
            className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />
          <button
            onClick={onClose}
            className="p-1 text-slate-500 hover:text-slate-300 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1 text-xs">
          {/* Action: Kill All */}
          <button
            onClick={() => {
              onKillAll();
              onClose();
            }}
            className="w-full p-2.5 rounded-lg flex items-center justify-between hover:bg-rose-500/10 text-rose-400 border border-transparent hover:border-rose-500/30 transition text-left"
          >
            <div className="flex items-center space-x-2.5">
              <Power className="w-4 h-4 text-rose-400" />
              <span className="font-semibold">{t.cmdKillAll}</span>
            </div>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300">
              Emergency
            </span>
          </button>

          {/* Action: Language Switch */}
          <button
            onClick={() => {
              onToggleLang();
              onClose();
            }}
            className="w-full p-2.5 rounded-lg flex items-center justify-between hover:bg-slate-800 text-slate-300 transition text-left"
          >
            <div className="flex items-center space-x-2.5">
              <Globe className="w-4 h-4 text-blue-400" />
              <span>{t.cmdChangeLang} ({lang === 'uz' ? 'English ga o\'tish' : 'O\'zbekchaga o\'tish'})</span>
            </div>
          </button>

          {/* Subagents Section */}
          <div className="px-2 pt-2 pb-1 text-[10px] font-bold uppercase text-slate-500 tracking-wider">
            {t.subagentsTitle}
          </div>

          {filteredSubagents.map((agent) => (
            <button
              key={agent.id}
              onClick={() => {
                onSelectAgent(agent.id);
                onClose();
              }}
              className="w-full p-2.5 rounded-lg flex items-center justify-between hover:bg-slate-800 text-slate-200 transition text-left"
            >
              <div className="flex items-center space-x-2.5">
                {agent.id === 'scout' ? (
                  <Compass className="w-4 h-4 text-cyan-400" />
                ) : agent.id === 'inspector' ? (
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Terminal className="w-4 h-4 text-slate-400" />
                )}
                <span className="font-medium">
                  {lang === 'uz' ? agent.display_name_uz : agent.display_name_en}
                </span>
              </div>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded ${
                  agent.status === 'active'
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : 'bg-slate-800 text-slate-500'
                }`}
              >
                {agent.status === 'active' ? t.statusActive : t.statusLater}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
