'use client';

import React, { useState, useEffect } from 'react';
import {
  Globe,
  Camera,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,


  FileText,
  Sparkles,
  Download,
  Wrench,

  Cpu,
  Layers,
  Zap,
  ShieldAlert,
  Search,
  Activity
} from 'lucide-react';

interface Window2BrowserProps {
  taskId?: string;
  screenshotUrl?: string;
  taskEvidence?: string;
  taskStatus?: string;
  targetApp?: string;
  lang: 'uz' | 'en';
}

interface HealingEvent {
  id?: number | string;
  category?: string;
  timestamp?: string;
  diagnosis?: string;
  remedy?: string;
  [key: string]: unknown;
}

interface EepxTrace {
  id?: number | string;
  phase?: string;
  confidence_score?: number | string;
  details?: Record<string, unknown>;
  [key: string]: unknown;
}

interface SwarmStage {
  id?: number | string;
  stage_index?: number;
  stage_title?: string;
  status?: string;
  target_agent?: string;
  output_artifact?: string;
  [key: string]: unknown;
}

interface DeepxThought {
  id?: number | string;
  step_number?: number;
  thought_title?: string;
  perspective?: string;
  confidence?: string | number;
  thought_content?: string;
  [key: string]: unknown;
}

interface DeepsearchCitation {
  id?: number | string;
  source_title?: string;
  relevance_score?: number | string;
  summary?: string;
  [key: string]: unknown;
}

interface MvpBlueprint {
  project_name?: string;
  scaffold_status?: string;
  frontend_spec?: { framework?: string; [key: string]: unknown };
  backend_spec?: { framework?: string; [key: string]: unknown };
  security_spec?: { redteam_status?: string; security_score?: number; [key: string]: unknown };
  [key: string]: unknown;
}

interface KernelTelemetry {
  active_mode?: string;
  [key: string]: unknown;
}

interface LiveBrowserState {
  is_open?: boolean;
  url?: string;
  title?: string;
  frame_count?: number;
  last_error?: string;
  [key: string]: unknown;
}

export const Window2Browser: React.FC<Window2BrowserProps> = ({
  taskId,
  screenshotUrl,
  taskEvidence,
  taskStatus,
  targetApp,
  lang,
}) => {
  const [activeTab, setActiveTab] = useState<'jonli' | 'dalil' | 'natija' | 'hisobot' | 'healer' | 'yadro'>('jonli');
  const [imgError, setImgError] = useState(false);
  const [imgTimestamp, setImgTimestamp] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [healingEvents, setHealingEvents] = useState<HealingEvent[]>([]);
  const [isSelfHealing, setIsSelfHealing] = useState(false);
  const [urlDraft, setUrlDraft] = useState('');
  const [isNavigating, setIsNavigating] = useState(false);
  const [navError, setNavError] = useState<string | null>(null);

  const openUrl = async (raw: string) => {
    const url = raw.trim();
    if (!url || isNavigating) return;
    const target = /^https?:\/\//i.test(url) ? url : `https://${url}`;
    setIsNavigating(true);
    setNavError(null);
    try {
      const res = await fetch('/api/browser/navigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: target }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data?.success === false) {
        setNavError(data?.detail || (lang === 'uz' ? 'Sahifa ochilmadi' : 'Failed to open page'));
      } else {
        setUrlDraft('');
        setLiveFrame((n) => n + 1);
      }
    } catch {
      setNavError(lang === 'uz' ? 'Backend bilan aloqa yo\u2018q' : 'Backend unreachable');
    } finally {
      setIsNavigating(false);
    }
  };

  // Live subagent browser view
  const [liveState, setLiveState] = useState<LiveBrowserState>({ is_open: false, url: '', title: '' });
  const [liveFrame, setLiveFrame] = useState(0);
  const [liveOn, setLiveOn] = useState(true);

  useEffect(() => {
    if (!liveOn) return;
    let alive = true;
    const tick = async () => {
      try {
        const res = await fetch('/api/browser/state', { cache: 'no-store' });
        if (!res.ok) return;
        const st = await res.json();
        if (!alive) return;
        setLiveState(st);
        if (st.is_open) setLiveFrame((n) => n + 1);
      } catch {
        // backend may be starting; keep polling silently
      }
    };
    tick();
    const id = setInterval(tick, 1500);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [liveOn]);

  // Kernel V2 states
  const [eepxTraces, setEepxTraces] = useState<EepxTrace[]>([]);
  const [swarmStages, setSwarmStages] = useState<SwarmStage[]>([]);
  const [deepxThoughts, setDeepxThoughts] = useState<DeepxThought[]>([]);
  const [deepsearchCitations, setDeepsearchCitations] = useState<DeepsearchCitation[]>([]);
  const [mvpBlueprint, setMvpBlueprint] = useState<MvpBlueprint | null>(null);
  const [activeKernelMode, setActiveKernelMode] = useState<string>('standard');

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- yangi screenshot kelganda xato holati darhol tozalanadi
    setImgError(false);
  }, [screenshotUrl]);

  useEffect(() => {
    if (activeTab === 'healer' && taskId) {
      fetch(`/api/healing/events?task_id=${taskId}`)
        .then((r) => r.json())
        .then((data) => {
          if (Array.isArray(data)) setHealingEvents(data);
        })
        .catch(() => {});
    } else if (activeTab === 'yadro') {
      fetch('/api/kernel/telemetry')
        .then((r) => r.json())
        .then((d: KernelTelemetry) => {
          if (d.active_mode) setActiveKernelMode(d.active_mode);
        })
        .catch(() => {});

      if (taskId) {
        fetch(`/api/tasks/${taskId}/eepx`)
          .then((r) => r.json())
          .then((d) => {
            if (Array.isArray(d.traces)) setEepxTraces(d.traces);
          })
          .catch(() => {});

        fetch(`/api/tasks/${taskId}/swarm`)
          .then((r) => r.json())
          .then((d) => {
            if (Array.isArray(d.stages)) setSwarmStages(d.stages);
          })
          .catch(() => {});

        fetch(`/api/tasks/${taskId}/deepx/thoughts`)
          .then((r) => r.json())
          .then((d) => {
            if (Array.isArray(d.thoughts)) setDeepxThoughts(d.thoughts);
          })
          .catch(() => {});

        fetch(`/api/tasks/${taskId}/deepx/citations`)
          .then((r) => r.json())
          .then((d) => {
            if (Array.isArray(d.citations)) setDeepsearchCitations(d.citations);
          })
          .catch(() => {});

        fetch(`/api/tasks/${taskId}/deepx/blueprint`)
          .then((r) => r.json())
          .then((d) => {
            if (d.blueprint) setMvpBlueprint(d.blueprint);
          })
          .catch(() => {});
      }
    }
  }, [activeTab, taskId]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setImgError(false);
    setImgTimestamp(Date.now());
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const handleTriggerSelfHeal = async () => {
    if (!taskId) return;
    setIsSelfHealing(true);
    try {
      const res = await fetch(`/api/tasks/${taskId}/self-heal`, { method: 'POST' });
      if (res.ok) {
        const d = await res.json();
        setHealingEvents((prev) => [d.healing_event, ...prev]);
      }
    } catch (e) {
      console.error('Failed to trigger self heal:', e);
    } finally {
      setIsSelfHealing(false);
    }
  };

  const cacheBust = imgTimestamp || 0;
  // Backend sometimes hands back file:// or bare paths; the browser cannot load
  // those, so fall back to the latest-screenshot endpoint instead.
  const safeScreenshotUrl =
    screenshotUrl && /^(\/|https?:\/\/)/i.test(screenshotUrl) ? screenshotUrl : null;
  const effectiveScreenshotUrl =
    safeScreenshotUrl || `/api/screenshot/latest?t=${cacheBust}`;

  return (
    <div className="flex-1 min-h-0 flex flex-col accent-top bg-[#0a0e1a]/80 overflow-hidden font-sans select-none border-t border-white/10">
      {/* Browser Bar & Tabs */}
      <div className="h-10 px-3 border-b border-white/10 flex items-center justify-between bg-slate-900/60">
        <div className="flex items-center space-x-1 bg-slate-950 p-0.5 rounded-lg border border-white/5 text-[11px]">
          <button
            onClick={() => setActiveTab('jonli')}
            aria-pressed={activeTab === 'jonli'}
            className={`px-2.5 py-1 rounded-md transition font-medium flex items-center space-x-1.5 ${
              activeTab === 'jonli' ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            <span className="relative flex h-2 w-2">
              {liveState.is_open && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              )}
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  liveState.is_open ? 'bg-emerald-400' : 'bg-slate-600'
                }`}
              />
            </span>
            <span>{lang === 'uz' ? 'Jonli' : 'Live'}</span>
          </button>
          <button
            onClick={() => setActiveTab('dalil')}
            aria-pressed={activeTab === 'dalil'}
            className={`px-2.5 py-1 rounded-md transition font-medium flex items-center space-x-1.5 ${
              activeTab === 'dalil' ? 'nav-active text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Camera className="w-3.5 h-3.5" />
            <span>{lang === 'uz' ? 'Dalil' : 'Evidence'}</span>
          </button>
          <button
            onClick={() => setActiveTab('natija')}
            className={`px-2.5 py-1 rounded-md transition font-medium flex items-center space-x-1.5 ${
              activeTab === 'natija' ? 'nav-active text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>{lang === 'uz' ? 'Natija' : 'Result'}</span>
          </button>
          <button
            onClick={() => setActiveTab('hisobot')}
            className={`px-2.5 py-1 rounded-md transition font-medium flex items-center space-x-1.5 ${
              activeTab === 'hisobot' ? 'nav-active text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <FileText className="w-3.5 h-3.5 text-indigo-400" />
            <span>{lang === 'uz' ? 'Hisobot' : 'Report'}</span>
          </button>
          <button
            onClick={() => setActiveTab('healer')}
            className={`px-2.5 py-1 rounded-md transition font-medium flex items-center space-x-1.5 ${
              activeTab === 'healer' ? 'nav-active text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Wrench className="w-3.5 h-3.5 text-amber-400" />
            <span>{lang === 'uz' ? 'Avto-Tuzatish' : 'Self-Heal'}</span>
          </button>
          <button
            onClick={() => setActiveTab('yadro')}
            className={`px-2.5 py-1 rounded-md transition font-medium flex items-center space-x-1.5 ${
              activeTab === 'yadro' ? 'bg-purple-600 text-white shadow-sm shadow-purple-500/20' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Cpu className="w-3.5 h-3.5 text-purple-300" />
            <span>{lang === 'uz' ? 'Yadro' : 'Kernel'}</span>
          </button>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[11px] font-mono text-slate-500 uppercase">
            {lang === 'uz' ? 'Oyna 2' : 'Window 2'}
          </span>
          <button
            onClick={handleRefresh}
            className={`p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition ${
              isRefreshing ? 'animate-spin' : ''
            }`}
            title="Yangilash"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main View Area */}
      <div className="flex-1 overflow-y-auto p-3 flex flex-col">
        {activeTab === 'jonli' ? (
          /* TAB: JONLI — subagent brauzerini real vaqtda ko'rish */
          <div className="flex-1 flex flex-col space-y-2">
            <div className="w-full flex items-center justify-between px-1 text-[11px] font-mono">
              <span className="flex items-center gap-2 min-w-0">
                <span
                  className={`w-2 h-2 rounded-full shrink-0 ${
                    liveState.is_open ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'
                  }`}
                />
                <span className={liveState.is_open ? 'text-emerald-400' : 'text-slate-400'}>
                  {liveState.is_open
                    ? lang === 'uz'
                      ? 'BRAUZER OCHIQ'
                      : 'BROWSER LIVE'
                    : lang === 'uz'
                    ? 'BRAUZER KUTMOQDA'
                    : 'BROWSER IDLE'}
                </span>
                <span className="text-slate-400 truncate">
                  {liveState.url || (lang === 'uz' ? 'subagent sahifa ochmagan' : 'no page yet')}
                </span>
              </span>
              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => setLiveOn((v) => !v)}
                  aria-pressed={liveOn}
                  className={`px-2 py-1 rounded border transition ${
                    liveOn
                      ? 'border-emerald-500/40 text-emerald-300 bg-emerald-500/10'
                      : 'border-white/10 text-slate-400'
                  }`}
                >
                  {liveOn ? (lang === 'uz' ? 'Pauza' : 'Pause') : lang === 'uz' ? 'Davom' : 'Resume'}
                </button>
                <button
                  onClick={() => setLiveFrame((n) => n + 1)}
                  className="px-2 py-1 rounded border border-white/10 text-slate-400 hover:text-white transition"
                >
                  {lang === 'uz' ? 'Yangila' : 'Refresh'}
                </button>
              </div>
            </div>

            <div className="flex-1 min-h-[240px] rounded-lg border border-violet-500/20 bg-[#05070f] overflow-hidden flex items-center justify-center relative shadow-inner shadow-violet-950/30">
              {liveState.is_open && liveOn ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={`/api/browser/frame?t=${liveFrame}`}
                  alt={
                    lang === 'uz'
                      ? 'Subagent brauzerining jonli ko\u2018rinishi'
                      : 'Live view of the subagent browser'
                  }
                  className="w-full h-full object-contain"
                  draggable={false}
                />
              ) : (
                <div className="text-center px-4 py-6 space-y-3 max-w-md">
                  <Globe className="w-6 h-6 text-slate-600 mx-auto" aria-hidden="true" />
                  <p className="text-[11px] text-slate-400">
                    {liveState.is_open
                      ? lang === 'uz'
                        ? 'Jonli ko\u2018rinish pauza qilingan'
                        : 'Live view paused'
                      : lang === 'uz'
                      ? 'Subagent brauzer ochganda shu yerda ko\u2018rinadi'
                      : 'The subagent browser appears here once it opens'}
                  </p>
                  {/* Bo'sh holat amalga aylanadi: URL ochish + quick actions */}
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      openUrl(urlDraft);
                    }}
                    className="flex items-center gap-1.5"
                  >
                    <input
                      type="text"
                      value={urlDraft}
                      onChange={(e) => setUrlDraft(e.target.value)}
                      placeholder={lang === 'uz' ? 'example.com ochish...' : 'open example.com...'}
                      aria-label={lang === 'uz' ? 'Brauzerda ochiladigan manzil' : 'URL to open in browser'}
                      className="flex-1 min-w-0 h-8 px-2.5 rounded-md bg-slate-900 border border-white/10 text-[11px] font-mono text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-violet-500/60"
                    />
                    <button
                      type="submit"
                      disabled={!urlDraft.trim() || isNavigating}
                      className="h-8 px-3 rounded-md btn-accent disabled:opacity-40 text-[11px] font-medium text-white transition shrink-0"
                    >
                      {isNavigating ? '...' : lang === 'uz' ? 'Ochish' : 'Open'}
                    </button>
                  </form>
                  <div className="flex items-center justify-center gap-1.5">
                    {['example.com', 'github.com', 'google.com'].map((site) => (
                      <button
                        key={site}
                        onClick={() => openUrl(site)}
                        className="h-6 px-2 rounded border border-white/10 text-[11px] font-mono text-slate-400 hover:text-white hover:border-blue-500/40 transition"
                      >
                        {site}
                      </button>
                    ))}
                  </div>
                  {navError ? (
                    <p className="text-[11px] font-mono text-rose-400/90 break-all" role="alert">{navError}</p>
                  ) : null}
                  {liveState.last_error ? (
                    <p className="text-[11px] font-mono text-rose-400/80 break-all">
                      {String(liveState.last_error).slice(0, 120)}
                    </p>
                  ) : null}
                </div>
              )}
            </div>

            <p className="text-[11px] text-slate-400 font-mono px-1">
              {lang === 'uz'
                ? `Kadr: ${liveState.frame_count || 0} · yangilanish: 1.5s`
                : `Frames: ${liveState.frame_count || 0} · refresh: 1.5s`}
              {liveState.title ? ` · ${liveState.title}` : ''}
            </p>
          </div>
        ) : activeTab === 'dalil' ? (
          /* TAB: DALIL */
          <div className="flex-1 flex flex-col items-center justify-start space-y-2">
            {!imgError ? (
              <div className="w-full flex-1 flex flex-col items-center justify-start space-y-2">
                <div className="w-full flex items-center justify-between px-1 text-[11px] text-slate-400 font-mono">
                  <span className="flex items-center space-x-1 text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{lang === 'uz' ? 'Haqiqiy maqsad skrinshoti' : 'Live Target Capture'}</span>
                  </span>
                  <a
                    href={effectiveScreenshotUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="hover:text-blue-400 flex items-center space-x-1 transition text-[11px] bg-slate-900 px-2 py-1 rounded border border-white/5"
                  >
                    <span>{lang === 'uz' ? 'Kattalashtirish' : 'Expand'}</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
                <div className="w-full flex-1 rounded-xl overflow-hidden border border-white/10 bg-black/60 p-1.5 flex items-center justify-center">
                  {/* Dinamik API/data-URL rasmlar uchun <img> — next/image optimallashtirish bu yerda qo'llanilmaydi */}
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    key={imgTimestamp}
                    src={effectiveScreenshotUrl}
                    alt="Agent Evidence"
                    onError={() => setImgError(true)}
                    className="max-w-full max-h-[340px] object-contain rounded-lg shadow-lg"
                  />
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
                <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-white/10 flex items-center justify-center text-slate-500 mb-3 shadow-inner">
                  <Camera className="w-6 h-6 stroke-[1.5]" />
                </div>
                <h4 className="text-xs font-semibold text-slate-300 mb-1">
                  {lang === 'uz' ? 'Hali dalil (skrinshot) mavjud emas' : 'No Evidence Screenshot Yet'}
                </h4>
                <p className="text-[11px] text-slate-400 max-w-[220px] leading-relaxed">
                  {lang === 'uz'
                    ? 'Subagent topshiriqni bajarganda olingan skrinshot shu yerda avtomatik ko‘rinadi.'
                    : 'Screenshots captured during task execution will automatically display here.'}
                </p>
              </div>
            )}
          </div>
        ) : activeTab === 'natija' ? (
          /* TAB: NATIJA */
          <div className="flex-1 flex flex-col space-y-3">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-white/10 space-y-2">
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="text-slate-300">
                  {lang === 'uz' ? 'Ijro Natijasi:' : 'Execution Result:'}
                </span>
                <span
                  className={`font-mono text-[11px] font-bold px-2 py-1 rounded border ${
                    taskStatus === 'PASS'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : taskStatus === 'FAIL'
                      ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                      : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  }`}
                >
                  {taskStatus || 'IDLE'}
                </span>
              </div>
              <p className="text-slate-300 font-mono text-[11px] leading-relaxed">
                {taskEvidence ||
                  (lang === 'uz'
                    ? 'Vazifa natijasi va ilova hisoboti kutilmoqda.'
                    : 'Awaiting task outcome and application report.')}
              </p>
            </div>

            {/* Target App Sandbox Status */}
            <div className="p-3 rounded-xl bg-slate-900/40 border border-white/5 space-y-2 text-xs">
              <div className="flex items-center space-x-2 text-slate-300 font-medium">
                <ShieldCheck className="w-4 h-4 text-blue-400" />
                <span>{lang === 'uz' ? 'Xavfsiz Muhit (Sandbox)' : 'Sandboxed Target'}</span>
              </div>
              <div className="text-[11px] font-mono text-slate-400 space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500">Ilova:</span>
                  <span className="text-slate-300">{targetApp || 'General Browser'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Protokol:</span>
                  <span className="text-emerald-400">Command / Report Pydantic</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Host:</span>
                  <span className="text-slate-300">127.0.0.1 (Lokal)</span>
                </div>
              </div>
            </div>
          </div>
        ) : activeTab === 'hisobot' ? (
          /* TAB: HISOBOT (AUDIT REPORT) */
          <div className="flex-1 flex flex-col space-y-3">
            <div className="p-4 rounded-xl bg-slate-900/80 border border-white/10 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-white flex items-center space-x-1.5">
                    <FileText className="w-3.5 h-3.5 text-blue-400" />
                    <span>{lang === 'uz' ? 'Missiya Audit Hisoboti' : 'Mission Audit Report'}</span>
                  </h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    ID: {taskId || 'Faol vazifa tanlanmagan'}
                  </p>
                </div>
                {taskId && (
                  <div className="flex items-center space-x-2">
                    <a
                      href={`/api/tasks/${taskId}/report?format=html`}
                      target="_blank"
                      rel="noreferrer"
                      className="px-2.5 py-1 rounded btn-accent text-white text-[11px] font-semibold flex items-center space-x-1 shadow-sm transition"
                    >
                      <span>HTML</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                    <a
                      href={`/api/tasks/${taskId}/report?format=markdown`}
                      target="_blank"
                      rel="noreferrer"
                      className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-medium flex items-center space-x-1 transition"
                    >
                      <Download className="w-3 h-3" />
                      <span>MD</span>
                    </a>
                  </div>
                )}
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-white/5 text-[11px] text-slate-300 font-mono space-y-1.5 leading-relaxed">
                <div>• Maqsad: {taskEvidence ? taskEvidence.slice(0, 100) : 'Kutilmoqda...'}</div>
                <div>• Holat: {taskStatus || 'Noma\'lum'}</div>
                <div>• Qamrov: Faqat subagent workspace va ruxsat berilgan toollar.</div>
              </div>
            </div>
          </div>
        ) : activeTab === 'healer' ? (
          /* TAB: SELF-HEAL */
          <div className="flex-1 flex flex-col space-y-3">
            <div className="p-3 rounded-xl bg-slate-900/80 border border-white/10 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-amber-400 flex items-center space-x-1.5">
                    <Wrench className="w-3.5 h-3.5" />
                    <span>{lang === 'uz' ? 'O\'z-o\'zini Tuzatish (Self-Healing)' : 'Self-Healing Engine'}</span>
                  </h4>
                  <p className="text-[11px] text-slate-400">
                    Xatoliklarda avtomatik tashxis va qayta tiklash
                  </p>
                </div>
                {taskId && (
                  <button
                    onClick={handleTriggerSelfHeal}
                    disabled={isSelfHealing}
                    className="px-3 py-1 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-[11px] font-bold flex items-center space-x-1 transition shadow-sm"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>{lang === 'uz' ? 'Avto-Tuzatish' : 'Auto-Heal'}</span>
                  </button>
                )}
              </div>
            </div>

            {healingEvents.length === 0 ? (
              <div className="p-6 text-center rounded-xl bg-slate-950/40 border border-white/5 text-slate-500 text-xs">
                {lang === 'uz'
                  ? 'Ushbu vazifada xatolik kuzatilmadi. Tizim barqaror ishladi.'
                  : 'No healing interventions required for this task.'}
              </div>
            ) : (
              <div className="space-y-2">
                {healingEvents.map((evt) => (
                  <div
                    key={evt.id}
                    className="p-3 rounded-xl bg-slate-950/80 border border-amber-500/30 text-xs space-y-1 font-mono"
                  >
                    <div className="flex items-center justify-between text-amber-300 font-bold">
                      <span>[{evt.category}]</span>
                      <span className="text-[11px] text-slate-400">{evt.timestamp?.slice(11, 19)}</span>
                    </div>
                    <p className="text-slate-300 text-[11px]">{evt.diagnosis}</p>
                    <p className="text-emerald-400 text-[11px]">Tuzatish: {evt.remedy}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          /* TAB: YADRO / KERNEL / EEPX / SUPER AGENT */
          <div className="flex-1 flex flex-col space-y-3">
            {/* 1. Header & Quick Mode Switcher */}
            <div className="p-3 rounded-xl bg-slate-900/80 border border-purple-500/30 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-purple-300 flex items-center space-x-1.5">
                    <Cpu className="w-3.5 h-3.5 text-purple-400" />
                    <span>Conduit Yadro Dvigateli (Kernel v2.4)</span>
                  </h4>
                  <p className="text-[11px] text-slate-400">
                    EEPX Chuqur Kognitiv Tafakkur & Super Agent Swarm
                  </p>
                </div>
                <span className="px-2 py-1 rounded bg-purple-500/20 text-purple-300 font-mono text-[11px] border border-purple-500/30 font-bold uppercase">
                  {activeKernelMode}
                </span>
              </div>

              {/* Mode buttons */}
              <div className="grid grid-cols-4 gap-1 pt-1 text-[11px] font-mono">
                <button
                  onClick={async () => {
                    await fetch('/api/kernel/settings', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ active_mode: 'standard' }),
                    });
                    setActiveKernelMode('standard');
                  }}
                  className={`p-1.5.5 rounded-lg border text-center transition font-semibold ${
                    activeKernelMode === 'standard'
                      ? 'nav-active text-white border-violet-400'
                      : 'bg-slate-950 text-slate-400 border-white/5 hover:text-white'
                  }`}
                >
                  STANDART
                </button>
                <button
                  onClick={async () => {
                    await fetch('/api/kernel/settings', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ active_mode: 'eepx' }),
                    });
                    setActiveKernelMode('eepx');
                  }}
                  className={`p-1.5.5 rounded-lg border text-center transition font-semibold flex items-center justify-center space-x-1 ${
                    activeKernelMode === 'eepx'
                      ? 'bg-emerald-600 text-white border-emerald-400 shadow-sm shadow-emerald-500/20'
                      : 'bg-slate-950 text-slate-400 border-white/5 hover:text-emerald-300'
                  }`}
                >
                  <Sparkles className="w-2.5 h-2.5 text-emerald-300" />
                  <span>EEPX</span>
                </button>
                <button
                  onClick={async () => {
                    await fetch('/api/kernel/settings', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ active_mode: 'super_agent' }),
                    });
                    setActiveKernelMode('super_agent');
                  }}
                  className={`p-1.5.5 rounded-lg border text-center transition font-semibold flex items-center justify-center space-x-1 ${
                    activeKernelMode === 'super_agent'
                      ? 'bg-purple-600 text-white border-purple-400 shadow-sm shadow-purple-500/20'
                      : 'bg-slate-950 text-slate-400 border-white/5 hover:text-purple-300'
                  }`}
                >
                  <Layers className="w-2.5 h-2.5 text-purple-300" />
                  <span>SWARM</span>
                </button>
                <button
                  onClick={async () => {
                    await fetch('/api/kernel/settings', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ active_mode: 'deepx' }),
                    });
                    setActiveKernelMode('deepx');
                  }}
                  className={`p-1.5.5 rounded-lg border text-center transition font-semibold flex items-center justify-center space-x-1 ${
                    activeKernelMode === 'deepx'
                      ? 'bg-amber-600 text-white border-amber-400 shadow-sm shadow-amber-500/20'
                      : 'bg-slate-950 text-slate-400 border-white/5 hover:text-amber-300'
                  }`}
                >
                  <ShieldAlert className="w-2.5 h-2.5 text-amber-300" />
                  <span>DEEPX</span>
                </button>
              </div>
            </div>

            {/* 2. EEPX Chuqur Kognitiv Faza Xaritasi */}
            <div className="p-3 rounded-xl bg-slate-900/40 border border-white/5 space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-200">
                <span className="flex items-center space-x-1.5">
                  <Zap className="w-3.5 h-3.5 text-emerald-400" />
                  <span>EEPX Kognitiv Zanjiri</span>
                </span>
                <span className="text-[11px] text-slate-400 font-mono">
                  {eepxTraces.length} ta faza qayd etildi
                </span>
              </div>

              {eepxTraces.length === 0 ? (
                <div className="p-3 rounded-lg bg-slate-950 border border-white/5 text-[11px] text-slate-500 text-center font-mono">
                  EEPX fazalari ushbu vazifada ishga tushmagan (Standart rejim).
                </div>
              ) : (
                <div className="space-y-1.5">
                  {eepxTraces.map((tr) => (
                    <div
                      key={tr.id}
                      className="p-2.5 rounded-lg bg-slate-950 border border-emerald-500/20 text-[11px] font-mono space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-emerald-400 font-bold">[{tr.phase}]</span>
                        <span className="text-[11px] px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                          Ball: {tr.confidence_score}
                        </span>
                      </div>
                      {tr.details && (
                        <div className="text-[11px] text-slate-400 space-y-0.5 pt-0.5">
                          {Object.entries(tr.details).slice(0, 3).map(([k, v]) => (
                            <div key={k} className="flex justify-between">
                              <span className="text-slate-500">{k}:</span>
                              <span className="text-slate-300 font-semibold truncate max-w-[170px]">{String(v)}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 3. Super Agent Swarm Bosqichlari */}
            <div className="p-3 rounded-xl bg-slate-900/40 border border-white/5 space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-200">
                <span className="flex items-center space-x-1.5">
                  <Layers className="w-3.5 h-3.5 text-purple-400" />
                  <span>Super Agent Swarm Bosqichlari</span>
                </span>
                <span className="text-[11px] text-slate-400 font-mono">
                  {swarmStages.length} ta subagent
                </span>
              </div>

              {swarmStages.length === 0 ? (
                <div className="p-3 rounded-lg bg-slate-950 border border-white/5 text-[11px] text-slate-500 text-center font-mono">
                  Swarm orkestratsiyasi kutilmoqda (Super Agent rejimi tanlanganda faollashadi).
                </div>
              ) : (
                <div className="space-y-1.5">
                  {swarmStages.map((stg) => (
                    <div
                      key={stg.id}
                      className="p-2.5 rounded-lg bg-slate-950 border border-purple-500/20 text-[11px] font-mono space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-purple-300 font-bold">
                          {stg.stage_index}. {stg.stage_title}
                        </span>
                        <span
                          className={`text-[11px] px-1.5 py-0.2 rounded font-bold uppercase ${
                            stg.status === 'passed'
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : stg.status === 'running'
                              ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30 animate-pulse'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {stg.status}
                        </span>
                      </div>
                      <div className="flex justify-between text-[11px] text-slate-400">
                        <span>Agent: <strong className="text-white">{stg.target_agent}</strong></span>
                        {stg.output_artifact && (
                          <span className="text-indigo-400 truncate max-w-[140px]">
                            {stg.output_artifact}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 4. DeepX Uzoq Muddat Fikrlash (Extended Reasoning Tree) */}
            <div className="p-3 rounded-xl bg-slate-900/40 border border-amber-500/20 space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-200">
                <span className="flex items-center space-x-1.5">
                  <Activity className="w-3.5 h-3.5 text-amber-400" />
                  <span>DeepX Uzoq Muddatli Tafakkur Zanjiri</span>
                </span>
                <span className="text-[11px] text-amber-400 font-mono">
                  {deepxThoughts.length} ta bosqich
                </span>
              </div>

              {deepxThoughts.length === 0 ? (
                <div className="p-3 rounded-lg bg-slate-950 border border-white/5 text-[11px] text-slate-500 text-center font-mono">
                  DEEPX tafakkuri kutilyapti (DEEPX rejimi tanlanganda ko&apos;p shoxli fikrlash ishga tushadi).
                </div>
              ) : (
                <div className="space-y-1.5">
                  {deepxThoughts.map((th) => (
                    <div
                      key={th.id}
                      className="p-2.5 rounded-lg bg-slate-950 border border-amber-500/20 text-[11px] font-mono space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-amber-300 font-bold">
                          {th.step_number}. {th.thought_title}
                        </span>
                        <span className="text-[11px] px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                          {th.perspective} ({th.confidence})
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
                        {th.thought_content}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 5. DeepSearch Ko'p Manbali Tadqiqot & Iqtiboslar */}
            <div className="p-3 rounded-xl bg-slate-900/40 border border-cyan-500/20 space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-200">
                <span className="flex items-center space-x-1.5">
                  <Search className="w-3.5 h-3.5 text-cyan-400" />
                  <span>DeepSearch Manbalar & Iqtiboslar</span>
                </span>
                <span className="text-[11px] text-cyan-400 font-mono">
                  {deepsearchCitations.length} ta manba
                </span>
              </div>

              {deepsearchCitations.length === 0 ? (
                <div className="p-3 rounded-lg bg-slate-950 border border-white/5 text-[11px] text-slate-500 text-center font-mono">
                  Lokal kod, xotira va hujjatlar bo&apos;yicha qidiruv natijalari shu yerda ko&apos;rinadi.
                </div>
              ) : (
                <div className="space-y-1.5">
                  {deepsearchCitations.map((cit) => (
                    <div
                      key={cit.id}
                      className="p-2 rounded-lg bg-slate-950 border border-cyan-500/20 text-[11px] font-mono space-y-0.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-cyan-300 font-bold truncate max-w-[200px]">{cit.source_title}</span>
                        <span className="text-[11px] text-cyan-400">Moslik: {cit.relevance_score}</span>
                      </div>
                      <p className="text-[11px] text-slate-400 font-sans line-clamp-2">{cit.summary}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 6. Sentinel RedTeam Xavfsizlik Sertifikati & MVP Blueprint */}
            <div className="p-3 rounded-xl bg-slate-900/40 border border-emerald-500/20 space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-200">
                <span className="flex items-center space-x-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Sentinel RedTeam & MVP Spetsifikatsiyasi</span>
                </span>
                <span className={`text-[11px] px-1.5 py-0.2 rounded font-mono border ${
                  mvpBlueprint?.security_spec?.redteam_status === 'Sentinel certified'
                    ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                    : mvpBlueprint?.security_spec?.redteam_status === 'SENTINEL FAIL'
                    ? 'bg-red-500/10 text-red-300 border border-red-500/20'
                    : 'bg-slate-500/10 text-slate-300 border border-white/10'
                }`}>
                  {mvpBlueprint?.security_spec?.redteam_status === 'Sentinel certified'
                    ? `XAVFSIZ ${mvpBlueprint.security_spec.security_score ?? 100}/100`
                    : mvpBlueprint?.security_spec?.redteam_status === 'SENTINEL FAIL'
                    ? `ZAIF ${mvpBlueprint.security_spec.security_score ?? '?'}/100`
                    : 'AUDIT KUTILMOQDA'}
                </span>
              </div>

              {mvpBlueprint ? (
                <div className="p-2.5 rounded-lg bg-slate-950 border border-emerald-500/20 text-[11px] font-mono space-y-1">
                  <div className="flex justify-between text-emerald-300 font-bold">
                    <span>Loyiha: {mvpBlueprint.project_name}</span>
                    <span className="text-slate-400">{mvpBlueprint.scaffold_status}</span>
                  </div>
                  <div className="text-slate-400 space-y-0.5 pt-1">
                    <div>Frontend: <span className="text-slate-200">{mvpBlueprint.frontend_spec?.framework}</span></div>
                    <div>Backend: <span className="text-slate-200">{mvpBlueprint.backend_spec?.framework}</span></div>
                    <div>Xavfsizlik: <span className="text-emerald-400 font-semibold">{mvpBlueprint.security_spec?.redteam_status}</span></div>
                  </div>
                </div>
              ) : (
                <div className="p-3 rounded-lg bg-slate-950 border border-white/5 text-[11px] text-slate-500 text-center font-mono">
                  Sentinel audit hisoboti va ishlab chiqarishga tayyor MVP loyiha karkasi.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
