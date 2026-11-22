'use client';

import React, { useMemo, useState } from 'react';
import {
  Search, Bot, Plus, ArrowLeft, Camera, Box, Palette, Film, ShieldCheck, Globe,
  Code2, PenTool, Network, FileText, MessageSquare,
  Sparkles, Play, CheckCircle2, XCircle, Clock3,
} from 'lucide-react';
import { Language } from '@/lib/translations';
import type { SubagentInfo } from './TaskComposer';

interface TaskInfo {
  task_id?: string;
  target_agent?: string;
  status?: string;
}

interface AgentsCatalogProps {
  subagents: SubagentInfo[];
  tasks: TaskInfo[];
  lang: Language;
  onNewTask: (agent?: string) => void;
  onBack: () => void;
}

const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  scout: Camera,
  sculptor: Box,
  designer: Palette,
  animator: Film,
  editor: Film,
  painter: PenTool,
  inspector: ShieldCheck,
  sentinel: ShieldCheck,
  superagent: Network,
  notion: FileText,
  slack: MessageSquare,
  inst_blender: Box,
  inst_video: Film,
  inst_image: Sparkles,
  inst_web: Globe,
  inst_figma: Palette,
};

type Filter = 'all' | 'role' | 'instrument' | 'active';

export const AgentsCatalog: React.FC<AgentsCatalogProps> = ({ subagents, tasks, lang, onNewTask, onBack }) => {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<Filter>('all');

  const isInstrument = (id: string) => id.startsWith('inst_');

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return subagents.filter((a) => {
      if (filter === 'instrument' && !isInstrument(a.id)) return false;
      if (filter === 'role' && isInstrument(a.id)) return false;
      if (filter === 'active' && a.status !== 'active') return false;
      if (!q) return true;
      const haystack = [a.id, a.name, a.display_name_uz, a.display_name_en, a.role_desc_uz, a.role_desc_en, a.target_app]
        .filter(Boolean).join(' ').toLowerCase();
      return haystack.includes(q);
    });
  }, [subagents, query, filter]);

  const lastTask = (id: string): TaskInfo | undefined =>
    tasks.find((t) => (t.target_agent || '').toLowerCase() === id.toLowerCase());

  const filters: Array<{ key: Filter; uz: string; en: string }> = [
    { key: 'all', uz: 'Barchasi', en: 'All' },
    { key: 'role', uz: 'Rol agentlari', en: 'Role agents' },
    { key: 'instrument', uz: 'Instrumentlar', en: 'Instruments' },
    { key: 'active', uz: 'Faol', en: 'Active' },
  ];

  return (
    <div className="h-full flex flex-col min-h-0">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-5">
        <button
          onClick={onBack}
          className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg border border-white/10 bg-white/5 text-slate-300 hover:text-white hover:border-blue-500/40 transition shrink-0"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span className="text-xs">{lang === 'uz' ? 'Studiyaga qaytish' : 'Back to studio'}</span>
        </button>
        <div className="flex-1">
          <h1 className="text-xl font-semibold text-white flex items-center space-x-2">
            <Bot className="w-5 h-5 text-blue-400" />
            <span>{lang === 'uz' ? 'Agentlar katalogi' : 'Agent catalog'}</span>
            <span className="px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-xs text-slate-400">
              {subagents.length}
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            {lang === 'uz'
              ? 'Barcha subagentlar, ularning holati va oxirgi natijalari'
              : 'All subagents, their status and latest results'}
          </p>
        </div>
        <button
          onClick={() => onNewTask()}
          className="btn-accent flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-semibold text-white shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>{lang === 'uz' ? 'Yangi vazifa' : 'New task'}</span>
        </button>
      </div>

      {/* Qidiruv + filtrlar */}
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <div className="relative flex-1 min-w-[240px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={lang === 'uz' ? 'Agent yoki vazifa bo‘yicha qidirish...' : 'Search agents or tasks...'}
            aria-label={lang === 'uz' ? 'Agent qidirish' : 'Search agents'}
            className="w-full rounded-xl bg-[#0d1117] border border-white/10 pl-10 pr-3 py-2.5 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {filters.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              aria-pressed={filter === f.key}
              className="px-3 py-1.5 rounded-lg border border-white/10 bg-white/5 text-xs text-slate-300 hover:text-white transition"
            >
              {lang === 'uz' ? f.uz : f.en}
            </button>
          ))}
        </div>
      </div>

      {/* Agentlar tarmog'i */}
      <div className="flex-1 min-h-0 overflow-y-auto pr-1">
        {filtered.length === 0 ? (
          <div className="h-48 flex flex-col items-center justify-center text-slate-500 space-y-2">
            <Search className="w-8 h-8 opacity-40" />
            <p className="text-sm">{lang === 'uz' ? 'Hech narsa topilmadi' : 'Nothing found'}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3 pb-3">
            {filtered.map((a) => {
              const Icon = ICONS[a.id] || (isInstrument(a.id) ? Code2 : Bot);
              const last = lastTask(a.id);
              const status = (last?.status || '').toUpperCase();
              const StatusIcon = status === 'PASS' ? CheckCircle2 : status === 'FAIL' || status === 'BLOCKED' ? XCircle : Clock3;
              const statusColor = status === 'PASS'
                ? 'text-emerald-400'
                : status === 'FAIL' || status === 'BLOCKED'
                  ? 'text-rose-400'
                  : 'text-slate-500';
              return (
                <div
                  key={a.id}
                  className="card-elevated p-3 flex flex-col min-h-[165px]"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center space-x-3 min-w-0">
                      <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center shrink-0">
                        <Icon className="w-5 h-5 text-blue-400" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-white truncate">
                          {(lang === 'uz' ? a.display_name_uz : a.display_name_en) || a.name || a.id}
                        </p>
                        <p className="text-[11px] font-mono text-slate-500 truncate">{a.id}</p>
                      </div>
                    </div>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold shrink-0 ${
                      a.status === 'active'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-white/5 text-slate-500 border border-white/10'
                    }`}>
                      {a.status === 'active' ? (lang === 'uz' ? 'FAOL' : 'ACTIVE') : (lang === 'uz' ? 'NOSFAOL' : 'INACTIVE')}
                    </span>
                  </div>

                  <p className="text-xs text-slate-400 mt-3 line-clamp-2 flex-1">
                    {(lang === 'uz' ? a.role_desc_uz : a.role_desc_en) || a.role_desc_en || '—'}
                  </p>

                  <div className="flex items-center justify-between gap-2 mt-3 pt-3 border-t border-white/5">
                    <div className="flex items-center space-x-2 min-w-0">
                      <span className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-[10px] text-slate-400 truncate">
                        {isInstrument(a.id) ? (lang === 'uz' ? 'INSTRUMENT' : 'TOOL') : (lang === 'uz' ? 'ROL' : 'ROLE')}
                      </span>
                      {last && (
                        <span className={`flex items-center space-x-1 text-[11px] font-mono ${statusColor}`}>
                          <StatusIcon className="w-3 h-3" />
                          <span>{status || '—'}</span>
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => onNewTask(a.id)}
                      className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/25 text-blue-300 text-xs hover:bg-blue-500/20 transition shrink-0"
                    >
                      <Play className="w-3 h-3" />
                      <span>{lang === 'uz' ? 'Ishga tushir' : 'Run'}</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
