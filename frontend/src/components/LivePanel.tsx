'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Image as ImageIcon,
  Terminal,
  Maximize2,
  X,
  FileCheck2,
  Clock,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Timer,
  Search,
  Copy,
  Check,
  ShieldCheck,
  ShieldAlert,
  Download
} from 'lucide-react';
import { Language, translations } from '@/lib/translations';

interface LogEntry {
  task_id: string;
  agent_name: string;
  level: string;
  message: string;
  timestamp: string;
}

interface LivePanelProps {
  screenshotUrl?: string;
  logs: LogEntry[];
  currentAgent: string;
  status: string;
  currentStep?: string;
  stepDurations?: {
    planner?: number;
    doer?: number;
    checker?: number;
  };
  totalDuration?: number;
  evidence?: string;
  lang: Language;
}

export const LivePanel: React.FC<LivePanelProps> = ({
  screenshotUrl,
  logs,
  currentAgent,
  status,
  currentStep,
  stepDurations,
  totalDuration,
  evidence,
  lang,
}) => {
  const t = translations[lang];
  const [modalOpen, setModalOpen] = useState(false);
  const [imgError, setImgError] = useState(false);
  const [activeUrl, setActiveUrl] = useState<string | null>(screenshotUrl || '/api/screenshot/latest');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLevel, setSelectedLevel] = useState<string>('ALL');
  const [copiedLogs, setCopiedLogs] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  const logContainerRef = useRef<HTMLDivElement>(null);

  // Live stopwatch while working
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (status === 'working') {
      interval = setInterval(() => setElapsed((p) => p + 1), 1000);
    } else {
      setElapsed(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [status]);

  const formatTimer = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}s`;
  };

  // Auto scroll logs
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, searchQuery, selectedLevel]);

  // Update activeUrl when screenshotUrl prop changes
  useEffect(() => {
    setImgError(false);
    if (screenshotUrl) {
      setActiveUrl(screenshotUrl);
    } else {
      setActiveUrl('/api/screenshot/latest');
    }
  }, [screenshotUrl]);

  const handleCopyLogs = () => {
    const text = logs
      .map((l) => `[${l.timestamp}] [${l.agent_name}] [${l.level}] ${l.message}`)
      .join('\n');
    navigator.clipboard.writeText(text);
    setCopiedLogs(true);
    setTimeout(() => setCopiedLogs(false), 2000);
  };

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      !searchQuery ||
      log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.agent_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesLevel =
      selectedLevel === 'ALL' ||
      log.level.toUpperCase() === selectedLevel.toUpperCase();
    return matchesSearch && matchesLevel;
  });

  const getLevelBadge = (level: string) => {
    switch (level.toUpperCase()) {
      case 'SUCCESS':
        return <span className="text-[10px] text-emerald-400 font-bold">[SUCCESS]</span>;
      case 'ERROR':
        return <span className="text-[10px] text-rose-400 font-bold">[ERROR]</span>;
      case 'WARNING':
        return <span className="text-[10px] text-amber-400 font-bold">[WARN]</span>;
      default:
        return <span className="text-[10px] text-blue-400 font-bold">[INFO]</span>;
    }
  };

  const isVerified = Boolean(evidence && status === 'PASS');

  return (
    <aside className="w-full lg:w-96 bg-slate-900/60 border-l border-slate-800 p-4 flex flex-col h-full overflow-hidden">
      {/* Header bar with Subagent & Real-time Telemetry */}
      <div className="flex items-center justify-between mb-3 shrink-0">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              {t.livePanelTitle}
            </h2>
            {status === 'working' ? (
              <span className="flex items-center space-x-1 px-1.5 py-0.2 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30 text-[10px] font-mono">
                <Timer className="w-2.5 h-2.5 animate-spin" />
                <span>{formatTimer(elapsed)}</span>
              </span>
            ) : totalDuration ? (
              <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-1.5 py-0.2 rounded border border-slate-700">
                {totalDuration}s
              </span>
            ) : null}
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">
            {currentAgent ? (
              <>
                <span className="capitalize font-semibold text-slate-300">{currentAgent}</span>
                {' · '}
                <span className={status === 'PASS' ? 'text-emerald-400' : status === 'working' ? 'text-blue-400' : 'text-slate-400'}>
                  {status}
                </span>
              </>
            ) : (
              t.idle
            )}
          </p>
        </div>

        {/* Evidence Verification Mini Indicator */}
        <div className="shrink-0">
          {isVerified ? (
            <span className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[9px] font-semibold">
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              <span>Dalil Tasdiqlandi</span>
            </span>
          ) : status === 'FAIL' ? (
            <span className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30 text-[9px] font-semibold">
              <ShieldAlert className="w-3 h-3 text-rose-400" />
              <span>FAIL</span>
            </span>
          ) : (
            <span className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700/60 text-[9px]">
              <Clock className="w-2.5 h-2.5 text-slate-500" />
              <span>Kutishda</span>
            </span>
          )}
        </div>
      </div>

      {/* Mini Step Tracker Pill */}
      {currentStep && (
        <div className="mb-3 px-3 py-1.5 rounded-lg bg-slate-950/70 border border-slate-800 flex items-center justify-between text-[10px] shrink-0">
          <span className="text-slate-500">Joriy bosqich:</span>
          <span className="font-mono font-bold text-cyan-400 uppercase tracking-wide">
            {currentStep}
          </span>
        </div>
      )}

      {/* Screenshot Preview Card — Skrinshot yoki 'Hali skrinshot yo'q' holati */}
      <div className="mb-4 bg-slate-950/80 border border-slate-800 rounded-xl overflow-hidden shrink-0">
        <div className="px-3 py-2 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center space-x-1.5 text-xs text-slate-300 font-semibold">
            <ImageIcon className="w-3.5 h-3.5 text-cyan-400" />
            <span>{t.screenshotTitle}</span>
          </div>
          {activeUrl && !imgError && (
            <div className="flex items-center space-x-1">
              <button
                onClick={() => setModalOpen(true)}
                className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-slate-200 transition"
                title={t.zoomScreenshot}
              >
                <Maximize2 className="w-3.5 h-3.5" />
              </button>
              <a
                href={activeUrl}
                target="_blank"
                rel="noreferrer"
                className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-slate-200 transition"
                title="Alohida oynada ochish"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          )}
        </div>

        <div className="p-2 flex items-center justify-center min-h-[140px] max-h-[220px] bg-slate-950/50">
          {activeUrl && !imgError ? (
            <div
              className="relative w-full h-[170px] rounded-lg overflow-hidden border border-slate-800 cursor-pointer group"
              onClick={() => setModalOpen(true)}
            >
              <img
                src={activeUrl}
                alt="Target Screenshot"
                className="w-full h-full object-cover transition duration-300 group-hover:scale-105"
                onError={() => {
                  if (activeUrl !== '/api/screenshot/latest') {
                    setActiveUrl('/api/screenshot/latest');
                  } else {
                    setImgError(true);
                  }
                }}
              />
              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                <span className="text-xs font-medium text-white flex items-center space-x-1">
                  <Maximize2 className="w-3.5 h-3.5" />
                  <span>{t.zoomScreenshot}</span>
                </span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-6 px-4 text-center text-slate-500 w-full">
              <ImageIcon className="w-7 h-7 text-slate-600 mb-1.5 stroke-[1.5]" />
              <span className="text-xs font-medium text-slate-400">Hali skrinshot yo'q</span>
              <span className="text-[10px] text-slate-600 mt-0.5">Vazifa bajarilgach tasvir bu yerda ko'rinadi</span>
            </div>
          )}
        </div>
      </div>

      {/* Real-time Logs Card with Search & Filters */}
      <div className="flex-1 flex flex-col bg-slate-950/80 border border-slate-800 rounded-xl overflow-hidden min-h-0">
        <div className="px-3 py-2 border-b border-slate-800 flex items-center justify-between bg-slate-900/60 shrink-0">
          <div className="flex items-center space-x-1.5 text-xs text-slate-300 font-semibold">
            <Terminal className="w-3.5 h-3.5 text-emerald-400" />
            <span>{t.logsTitle}</span>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopyLogs}
              className="flex items-center space-x-1 text-[10px] text-slate-400 hover:text-slate-200 transition"
              title="Barcha loglarni nusxalash"
            >
              {copiedLogs ? (
                <Check className="w-3 h-3 text-emerald-400" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
            </button>
            <span className="text-[10px] font-mono text-slate-500">{filteredLogs.length} qator</span>
          </div>
        </div>

        {/* Filter controls */}
        <div className="p-2 border-b border-slate-800/80 bg-slate-950/40 flex items-center gap-1.5 shrink-0">
          <div className="relative flex-1">
            <Search className="w-3 h-3 text-slate-500 absolute left-2 top-2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Qidirish..."
              className="w-full bg-slate-900 border border-slate-800 rounded-md pl-6 pr-2 py-1 text-[11px] text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50"
            />
          </div>
          <div className="flex items-center space-x-1">
            {['ALL', 'INFO', 'WARN', 'ERROR'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setSelectedLevel(lvl)}
                className={`text-[9px] px-1.5 py-0.5 rounded font-mono transition ${
                  selectedLevel === lvl
                    ? 'bg-blue-600/30 text-blue-300 border border-blue-500/50'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>

        <div
          ref={logContainerRef}
          className="flex-1 p-3 overflow-y-auto font-mono text-[11px] space-y-2 bg-slate-950/90"
        >
          {filteredLogs.length === 0 ? (
            <div className="text-center py-10 text-slate-600 italic">
              {searchQuery ? 'Mos log topilmadi' : t.noLogs}
            </div>
          ) : (
            filteredLogs.map((log, idx) => (
              <div key={idx} className="leading-relaxed border-b border-slate-900 pb-1.5">
                <div className="flex items-center space-x-2 text-[10px] text-slate-500">
                  <span>{log.timestamp.split('T')[1]?.substring(0, 8) || log.timestamp}</span>
                  <span className="text-slate-400 font-semibold">[{log.agent_name}]</span>
                  {getLevelBadge(log.level)}
                </div>
                <div className="text-slate-300 mt-0.5 whitespace-pre-wrap break-words">
                  {log.message}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Modal for Zoomed Screenshot */}
      {modalOpen && activeUrl && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="relative max-w-5xl w-full bg-slate-900 border border-slate-700 rounded-2xl overflow-hidden shadow-2xl">
            <div className="p-3 border-b border-slate-800 flex items-center justify-between bg-slate-950">
              <span className="text-xs font-semibold text-slate-200">
                {t.screenshotTitle} (Full HD Snapshot)
              </span>
              <button
                onClick={() => setModalOpen(false)}
                className="p-1 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-2 max-h-[80vh] overflow-auto flex items-center justify-center bg-black">
              <img src={activeUrl} alt="Zoomed Screenshot" className="max-w-full h-auto rounded-lg" />
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};
