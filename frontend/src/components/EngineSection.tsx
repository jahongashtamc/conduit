'use client';

import React, { useState } from 'react';
import { Terminal, CheckCircle2, XCircle, Play, ChevronDown, ChevronUp, Copy, Check, ShieldCheck } from 'lucide-react';
import { Language, translations } from '@/lib/translations';

export interface EngineItem {
  name: string;
  binary: string;
  description: string;
  command_template: string;
  timeout_seconds: number;
  available: boolean;
}

export interface EngineStatus {
  active_engine: string;
  engines: Record<string, EngineItem>;
}

interface EngineSectionProps {
  engineStatus: EngineStatus;
  onSelectEngine: (engineKey: string) => Promise<void>;
  onTestEngine: () => Promise<void>;
  isTesting: boolean;
  lang: Language;
}

export const EngineSection: React.FC<EngineSectionProps> = ({
  engineStatus,
  onSelectEngine,
  onTestEngine,
  isTesting,
  lang,
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [copied, setCopied] = useState(false);

  const activeKey = engineStatus.active_engine || 'claude_code';
  const activeEngine = engineStatus.engines[activeKey] || {
    name: 'Claude Code CLI',
    binary: 'claude',
    command_template: 'claude -p "{prompt}" --output-format text --allowedTools "Bash(python tools.py *),FileRead,FileEdit,Write"',
    available: true
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(activeEngine.command_template);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mb-5 rounded-2xl bg-slate-900/90 border border-slate-800 p-4 shadow-lg">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        {/* Left: CLI Engine Info */}
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600/30 via-blue-600/20 to-indigo-600/30 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0 shadow-sm">
            <Terminal className="w-5 h-5" />
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-slate-100 uppercase tracking-wide">
                {lang === 'uz' ? 'AI Dvigateli (CLI):' : 'AI Engine (CLI Subprocess):'}
              </span>

              {/* Engine Switcher */}
              <select
                value={activeKey}
                onChange={(e) => onSelectEngine(e.target.value)}
                className="text-xs bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-0.5 text-slate-200 font-semibold focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {Object.entries(engineStatus.engines).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v.name} {v.available ? '' : '(Topilmadi)'}
                  </option>
                ))}
              </select>

              {/* Status Badge */}
              <span
                className={`text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center space-x-1 ${
                  activeEngine.available
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                    : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    activeEngine.available ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
                  }`}
                />
                <span>
                  {activeEngine.available
                    ? lang === 'uz'
                      ? 'Faol & Tayyor'
                      : 'Active & Ready'
                    : lang === 'uz'
                    ? "Dastur o'rnatilmagan"
                    : 'Not Installed'}
                </span>
              </span>
            </div>

            <p className="text-[11px] text-slate-400 mt-1 font-mono">
              <span className="text-slate-500">Ilova:</span> <span className="text-blue-300 font-semibold">{activeEngine.binary}</span>
              <span className="text-slate-600 mx-1.5">•</span>
              <span className="text-slate-500">Qobiq:</span> <span className="text-emerald-400 font-semibold">tools.py (agent-studio-plugin)</span>
              <span className="text-slate-600 mx-1.5">•</span>
              <span className="text-slate-500">Izolatsiya:</span> <span className="text-cyan-400">workspaces/</span>
            </p>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center space-x-2 self-end sm:self-auto">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-medium transition"
          >
            <span>{lang === 'uz' ? 'Shablon' : 'Template'}</span>
            {showDetails ? <ChevronUp className="w-3 h-3 ml-0.5" /> : <ChevronDown className="w-3 h-3 ml-0.5" />}
          </button>

          <button
            onClick={onTestEngine}
            disabled={isTesting || !activeEngine.available}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition active:scale-95 ${
              isTesting
                ? 'bg-blue-600/20 text-blue-300 border-blue-500/30 cursor-wait'
                : activeEngine.available
                ? 'bg-blue-600 hover:bg-blue-500 text-white border-blue-500 shadow-sm shadow-blue-500/20'
                : 'bg-slate-800 text-slate-500 border-slate-700 cursor-not-allowed'
            }`}
          >
            <Play className="w-3 h-3 fill-current" />
            <span>{isTesting ? (lang === 'uz' ? 'Sinovda...' : 'Testing...') : lang === 'uz' ? 'Sinab ko\'rish' : 'Test Run'}</span>
          </button>
        </div>
      </div>

      {/* Expandable CLI Template Viewer */}
      {showDetails && (
        <div className="mt-3.5 pt-3 border-t border-slate-800/80 animate-in fade-in duration-150">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] font-semibold text-slate-300">
              {lang === 'uz' ? 'Subprocess buyruq shabloni (config/engine.json):' : 'Subprocess command template (config/engine.json):'}
            </span>
            <button
              onClick={handleCopy}
              className="flex items-center space-x-1 text-[10px] text-blue-400 hover:text-blue-300 transition"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? (lang === 'uz' ? 'Nusxalandi!' : 'Copied!') : lang === 'uz' ? 'Nusxa olish' : 'Copy'}</span>
            </button>
          </div>

          <pre className="p-2.5 rounded-xl bg-slate-950 font-mono text-[11px] text-emerald-300 border border-slate-800 overflow-x-auto leading-relaxed">
            {activeEngine.command_template}
          </pre>
          <div className="flex items-center space-x-2 text-[10px] text-slate-500 mt-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>
              {lang === 'uz'
                ? "Xavfsizlik: 'Hamma ruxsatni o'tkazib yuborish' bayrog'i o'chirilgan. Faqat tools.py va workspace fayllari ruxsat etilgan."
                : 'Security: No dangerously-skip-permissions flag. Only tools.py and workspace file I/O permitted.'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
