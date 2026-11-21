'use client';

import React, { useState, useEffect, useRef } from 'react';
import { StudioTopBar } from '@/components/DesktopTitlebar';
import { DesktopStatusBar } from '@/components/DesktopStatusBar';
import { ApprovalItem } from '@/components/ApprovalModal';
import { CommandPalette } from '@/components/CommandPalette';
import { BrainHeartTab } from '@/components/BrainHeartTab';
import { MemoryTab } from '@/components/MemoryTab';
import { GalleryTab } from '@/components/GalleryTab';
import { AppsTab } from '@/components/AppsTab';
import { Language } from '@/lib/translations';
import { soundEngine } from '@/lib/audio';

// Bosqich 2: 4 Top Bar Modals
import { EvolutionModal } from '@/components/EvolutionModal';
import { ApprovalsModal } from '@/components/ApprovalsModal';
import { ResourceModal } from '@/components/ResourceModal';
import { ConnectionsModal } from '@/components/ConnectionsModal';

// 7-Window Layout Components
import { Window6Brand } from '@/components/Window6Brand';
import { Window5Workspace } from '@/components/Window5Workspace';
import { Window7Profile } from '@/components/Window7Profile';
import { Window3BrainGraph } from '@/components/Window3BrainGraph';
import { Window4SubagentDetail } from '@/components/Window4SubagentDetail';
import { Window1Terminal } from '@/components/Window1Terminal';
import { Window2Browser } from '@/components/Window2Browser';

interface BrainState {
  active_subagent?: string;
  active_command?: unknown;
  plan?: unknown[];
  last_report?: unknown;
  short_memory?: unknown[];
  [key: string]: unknown;
}

interface ResourceSummary {
  total_cost_usd?: number;
  [key: string]: unknown;
}

interface Connection {
  id?: string;
  name?: string;
  is_ready?: boolean;
  [key: string]: unknown;
}

interface Subagent {
  id: string;
  name: string;
  display_name_uz: string;
  display_name_en: string;
  role_desc_uz?: string;
  role_desc_en?: string;
  target_app: string;
  status: 'active' | 'later';
  icon?: string;
}

interface Task {
  task_id: string;
  title: string;
  prompt: string;
  target_agent: string;
  status: string;
  current_step: string;
  planner_output?: string;
  doer_output?: string;
  checker_output?: string;
  evidence?: string;
  screenshot_url?: string;
  step_durations?: {
    planner?: number;
    doer?: number;
    checker?: number;
  };
  total_duration?: number;
  created_at: string;
}

interface LogEntry {
  task_id: string;
  agent_name: string;
  level: string;
  message: string;
  timestamp: string;
}

export default function Home() {
  const [lang, setLang] = useState<Language>('uz');
  const [isDark, setIsDark] = useState(true);
  const [wsStatus, setWsStatus] = useState<'connected' | 'connecting' | 'disconnected'>('connecting');
  const [subagents, setSubagents] = useState<Subagent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>('scout');
  const [brainState, setBrainState] = useState<BrainState | null>(null);
  const [agentReports, setAgentReports] = useState<Record<string, { status: 'PASS' | 'FAIL' | 'BLOCKED'; evidence?: string }>>({});
  const [activeTab, setActiveTab] = useState<'evolution' | 'workstation' | 'brain' | 'memory' | 'apps' | 'gallery'>('workstation');
  const [isCmdOpen, setIsCmdOpen] = useState(false);
  // Universal dvigatel ro'yxati (agents.json) — foydalanuvchi UI'da agent
  // CLI'ni ko'radi va tanlaydi (agy, opencode, crush, claude, codex, ...).
  const [engines, setEngines] = useState<string[]>([]);
  const [activeEngine, setActiveEngine] = useState<string>('');
  // Terminal / miya tuguni vertikal nisbati (0.25–0.75, default 0.55 —
  // terminal asosiy ish maydoni bo'lgani uchun ko'proq joy oladi).
  const [terminalFraction, setTerminalFraction] = useState(0.55);
  const terminalResizeRef = useRef<{ col: HTMLElement; startY: number; startFrac: number } | null>(null);

  const handleTerminalResizeStart = React.useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const col = e.currentTarget.parentElement;
    if (!col) return;
    terminalResizeRef.current = { col, startY: e.clientY, startFrac: terminalFraction };
    e.preventDefault();
  }, [terminalFraction]);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      const st = terminalResizeRef.current;
      if (!st) return;
      const rect = st.col.getBoundingClientRect();
      if (rect.height < 100) return;
      const frac = st.startFrac + (e.clientY - st.startY) / rect.height;
      setTerminalFraction(Math.min(0.75, Math.max(0.25, frac)));
    };
    const onUp = () => {
      terminalResizeRef.current = null;
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, []);

  // Dvigatel ro'yxatini yuklash (agents.json — universal).
  useEffect(() => {
    fetch('/api/engine/status')
      .then((r) => r.json())
      .then((d) => {
        const list = Object.keys(d?.engines || {});
        setEngines(list);
        if (d?.active_engine) setActiveEngine(d.active_engine);
      })
      .catch(() => {});
  }, []);

  const selectEngine = React.useCallback((key: string) => {
    fetch('/api/engine/select', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ engine: key }),
    })
      .then((r) => r.json())
      .then((d) => {
        if (d?.active_engine) setActiveEngine(d.active_engine);
      })
      .catch(() => {});
  }, []);

  // Bosqich 2 Modal States
  const [isEvolutionOpen, setIsEvolutionOpen] = useState(false);
  const [isApprovalsOpen, setIsApprovalsOpen] = useState(false);
  const [isResourcesOpen, setIsResourcesOpen] = useState(false);
  const [isConnectionsOpen, setIsConnectionsOpen] = useState(false);
  const [skillsCount, setSkillsCount] = useState(0);
  const [resourceSummary, setResourceSummary] = useState<ResourceSummary | null>(null);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [kernelMode, setKernelMode] = useState<string>('standard');

  // Fetch initial REST data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [agentsRes, tasksRes, apprRes, skillsRes, resRes, connRes, kernelRes] = await Promise.all([
          fetch('/api/subagents').then((r) => r.json()).catch(() => []),
          fetch('/api/tasks').then((r) => r.json()).catch(() => []),
          fetch('/api/approvals').then((r) => r.json()).catch(() => []),
          fetch('/api/skills').then((r) => r.json()).catch(() => []),
          fetch('/api/resources').then((r) => r.json()).catch(() => null),
          fetch('/api/connections').then((r) => r.json()).catch(() => []),
          fetch('/api/kernel/settings').then((r) => r.json()).catch(() => null),
        ]);
        if (Array.isArray(agentsRes)) {
          setSubagents(agentsRes);
          if (agentsRes.length > 0) {
            setSelectedAgentId((prev) => prev ?? agentsRes[0].id);
          }
        }
        if (Array.isArray(apprRes)) setApprovals(apprRes);
        if (Array.isArray(skillsRes)) setSkillsCount(skillsRes.length);
        if (resRes) setResourceSummary(resRes);
        if (Array.isArray(connRes)) setConnections(connRes);
        if (kernelRes && kernelRes.active_mode) setKernelMode(kernelRes.active_mode);
        if (Array.isArray(tasksRes) && tasksRes.length > 0) {
          setTasks(tasksRes);
          setCurrentTask(tasksRes[0]);
          if (tasksRes[0].task_id) {
            fetch(`/api/tasks/${tasksRes[0].task_id}/logs`)
              .then((r) => r.json())
              .then((data) => {
                if (Array.isArray(data)) setLogs(data);
              })
              .catch(() => {});

            fetch(`/api/brain/state/${tasksRes[0].task_id}`)
              .then((r) => r.json())
              .then((data) => {
                if (data && data.goal) {
                  setBrainState(data);
                  if (data.last_report) {
                    setAgentReports({ [data.last_report.from_agent.toLowerCase()]: data.last_report });
                  }
                }
              })
              .catch(() => {});
          }
        }
      } catch (err) {
        console.error('Failed to load initial Conduit data:', err);
      }
    };
    fetchData();
  }, []);

  // WebSocket connection & live streaming
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

    const connectWs = () => {
      setWsStatus('connecting');
      const wsUrl = `ws://${window.location.hostname}:8000/ws/live`;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsStatus('connected');
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'init') {
            if (msg.subagents) setSubagents(msg.subagents);
            if (msg.pending_approvals) setApprovals(msg.pending_approvals);
          } else if (msg.type === 'task_created') {
            const newTask = msg.task;
            setTasks((prev) => [newTask, ...prev.filter((t) => t.task_id !== newTask.task_id)]);
            setCurrentTask(newTask);
            if (newTask.target_agent) {
              setSelectedAgentId(newTask.target_agent);
            }
            setLogs([]);
          } else if (msg.type === 'log') {
            setLogs((prev) => [...prev, msg.data]);
          } else if (msg.type === 'task_update') {
            setCurrentTask((prev) => {
              if (!prev || prev.task_id !== msg.task_id) return prev;
              const updated = { ...prev, ...msg.data };
              if (msg.data.current_step === 'planner' && msg.data.output) {
                updated.planner_output = msg.data.output;
              } else if (msg.data.current_step === 'doer' && msg.data.output) {
                updated.doer_output = msg.data.output;
              } else if (msg.data.current_step === 'checker' && msg.data.output) {
                updated.checker_output = msg.data.output;
              }
              if (msg.data.screenshot_url) updated.screenshot_url = msg.data.screenshot_url;
              if (msg.data.evidence) updated.evidence = msg.data.evidence;
              return updated;
            });
          } else if (msg.type === 'approval_requested') {
            soundEngine.playAlert();
            setApprovals((prev) => [
              ...prev.filter((a) => a.approval_id !== msg.approval_id),
              {
                approval_id: msg.approval_id,
                task_id: msg.task_id,
                agent_id: msg.agent_id || 'scout',
                action_type: 'file_delete',
                risk_description: msg.risk_reason,
                details_json: '{}',
                status: 'pending',
                created_at: new Date().toISOString(),
              },
            ]);
          } else if (msg.type === 'approval_resolved') {
            setApprovals((prev) => prev.filter((a) => a.approval_id !== msg.approval_id));
          } else if (msg.type === 'task_completed') {
            if (msg.status === 'PASS') {
              soundEngine.playSuccess();
            } else {
              soundEngine.playFailure();
            }
            // Windows/desktop notification so the user hears about finished
            // tasks even when the studio window is in the background.
            try {
              if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
                const agent = msg.target_agent || 'Agent';
                new Notification(`Conduit: ${agent} — ${msg.status}`, {
                  body: (msg.evidence || '').slice(0, 140),
                  silent: true,
                });
              }
            } catch {
              // Notification API unavailable (e.g. --app flag edge cases)
            }
            setCurrentTask((prev) => {
              if (!prev || prev.task_id !== msg.task_id) return prev;
              return {
                ...prev,
                status: msg.status,
                evidence: msg.evidence,
                current_step: 'completed',
                step_durations: msg.step_durations || prev.step_durations,
                total_duration: msg.total_duration || prev.total_duration,
                screenshot_url: msg.screenshot_url || prev.screenshot_url,
              };
            });
            if (msg.target_agent) {
              setAgentReports((prev) => ({
                ...prev,
                [String(msg.target_agent || '').toLowerCase()]: {
                  status: msg.status,
                  evidence: msg.evidence,
                },
              }));
            }
          } else if (msg.type === 'brain_update') {
            if (msg.state) {
              setBrainState(msg.state);
              if (msg.state.last_report) {
                const rep = msg.state.last_report;
                const ag = (rep.from_agent || '').toLowerCase();
                if (ag) {
                  setAgentReports((prev) => ({
                    ...prev,
                    [ag]: { status: rep.status, evidence: rep.evidence },
                  }));
                }
              }
            }
          } else if (msg.type === 'brain_event') {
            if (msg.event?.direction === 'report' && msg.event?.payload) {
              const rep = msg.event.payload;
              const ag = (rep.from || msg.event.from_agent || '').toLowerCase();
              if (ag) {
                setAgentReports((prev) => ({
                  ...prev,
                  [ag]: { status: rep.status, evidence: rep.evidence },
                }));
              }
            }
          } else if (msg.type === 'subagent_activated') {
            const ag = (msg.agent || '').toLowerCase();
            setSelectedAgentId(ag);
            setBrainState((prev) => (prev ? { ...prev, active_subagent: ag } : null));
          } else if (msg.type === 'kill_all') {
            setCurrentTask((prev) => (prev ? { ...prev, status: 'FAIL', evidence: 'Terminated' } : null));
            setApprovals([]);
          }
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };

      ws.onclose = () => {
        setWsStatus('disconnected');
        reconnectTimeout = setTimeout(connectWs, 3000);
      };

      ws.onerror = () => {
        setWsStatus('disconnected');
        ws?.close();
      };
    };

    connectWs();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      ws?.close();
    };
  }, []);

  const handleResolveApproval = async (approvalId: string, decision: 'approved' | 'rejected') => {
    try {
      await fetch(`/api/approvals/${approvalId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision }),
      });
      setApprovals((prev) => prev.filter((a) => a.approval_id !== approvalId));
    } catch (err) {
      console.error('Error resolving approval:', err);
    }
  };

  const handleApproveAll = async () => {
    try {
      const res = await fetch('/api/approvals/approve-all', { method: 'POST' });
      if (res.ok) {
        setApprovals([]);
      }
    } catch (err) {
      console.error('Failed to approve all:', err);
    }
  };

  const handleKillAll = async () => {
    try {
      await fetch('/api/kill-all', { method: 'POST' });
    } catch (err) {
      console.error('Failed to trigger kill-all:', err);
    }
  };

  const handleRetryTask = async (taskId: string) => {
    try {
      const res = await fetch(`/api/tasks/${taskId}/retry`, { method: 'POST' });
      const data = await res.json();
      if (data.task_id) {
        setCurrentTask((prev) => (prev ? { ...prev, status: 'working', current_step: 'planner' } : null));
      }
    } catch (err) {
      console.error('Failed to retry task:', err);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) {
        return;
      }

      if (e.ctrlKey && e.shiftKey && (e.key === 'A' || e.key === 'a')) {
        e.preventDefault();
        handleApproveAll();
      } else if (e.ctrlKey && e.shiftKey && (e.key === 'X' || e.key === 'x')) {
        e.preventDefault();
        handleKillAll();
      } else if (e.ctrlKey && e.key === '1') {
        e.preventDefault();
        setIsEvolutionOpen((prev) => !prev);
      } else if (e.ctrlKey && e.key === '2') {
        e.preventDefault();
        setIsApprovalsOpen((prev) => !prev);
      } else if (e.ctrlKey && e.key === '3') {
        e.preventDefault();
        setIsResourcesOpen((prev) => !prev);
      } else if (e.ctrlKey && e.key === '4') {
        e.preventDefault();
        setIsConnectionsOpen((prev) => !prev);
      } else if (e.ctrlKey && (e.key === 'k' || e.key === 'K')) {
        e.preventDefault();
        setIsCmdOpen((prev) => !prev);
      } else if (e.key === 'Escape') {
        // Close whichever overlay is open; modals had no escape handling at all.
        const anyOpen =
          isCmdOpen ||
          isEvolutionOpen ||
          isApprovalsOpen ||
          isResourcesOpen ||
          isConnectionsOpen;
        if (anyOpen) {
          e.preventDefault();
          setIsCmdOpen(false);
          setIsEvolutionOpen(false);
          setIsApprovalsOpen(false);
          setIsResourcesOpen(false);
          setIsConnectionsOpen(false);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    isCmdOpen,
    isEvolutionOpen,
    isApprovalsOpen,
    isResourcesOpen,
    isConnectionsOpen,
  ]);

  const handleModeChange = async (mode: string) => {
    setKernelMode(mode);
    try {
      await fetch('/api/kernel/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active_mode: mode }),
      });
    } catch (e) {
      console.error('Failed to change kernel mode:', e);
    }
  };

  const toggleTheme = () => {
    setIsDark(!isDark);
    if (!isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const selectedAgent = subagents.find((a) => a.id.toLowerCase() === selectedAgentId?.toLowerCase()) || null;

  return (
    <div className="relative flex flex-col w-screen h-screen overflow-hidden text-zinc-100 font-sans">

      {/* 1. Global Native PC Desktop Studio TopBar */}
      <StudioTopBar
        lang={lang}
        onToggleLang={() => setLang(lang === 'uz' ? 'en' : 'uz')}
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
        wsStatus={wsStatus}
        onKillAll={handleKillAll}
        onOpenCmd={() => setIsCmdOpen(true)}
        onOpenEvolution={() => setActiveTab('evolution')}
        onOpenApprovals={() => setIsApprovalsOpen(true)}
        onOpenResources={() => setIsResourcesOpen(true)}
        onOpenConnections={() => setIsConnectionsOpen(true)}
        skillsCount={skillsCount}
        totalCost={resourceSummary?.total_cost_usd || 0}
        hasDangerousApprovals={approvals.some(
          (a) =>
            a.is_dangerous ||
            ['file_delete', 'git_push', 'db_drop'].includes(a.action_type) ||
            ['o\'chirish', 'delete', 'rm', 'git push', 'drop', 'wipe'].some((kw) =>
              (a.risk_description || '').toLowerCase().includes(kw)
            )
        )}
        hasMissingConnections={connections.some((c) => !c.is_ready)}
        pendingApprovalsCount={approvals.length}
        kernelMode={kernelMode}
        onModeChange={handleModeChange}
      />

      {/* 2. Main Studio Viewport */}
      {activeTab === 'evolution' ? (
        /* FULL TAB: EVOLYUTSIYA — birinchi tab: skill qo'shish markazi */
        <main className="flex-1 overflow-hidden flex flex-col">
          <EvolutionModal
            isOpen
            inline
            onClose={() => setActiveTab('workstation')}
            lang={lang}
          />
        </main>
      ) : activeTab === 'brain' ? (
        /* FULL TAB: MIYA & YURAK */
        <main className="flex-1 overflow-hidden p-4 flex flex-col">
          <BrainHeartTab
            currentTask={currentTask}
            tasks={tasks}
            lang={lang}
            onRetryTask={handleRetryTask}
          />
        </main>
      ) : activeTab === 'memory' ? (
        /* FULL TAB: XOTIRA */
        <main className="flex-1 overflow-hidden p-4 flex flex-col">
          <MemoryTab lang={lang} />
        </main>
      ) : activeTab === 'gallery' ? (
        /* FULL TAB: ARTEFAKT GALEREYASI */
        <main className="flex-1 overflow-hidden p-4 flex flex-col">
          <GalleryTab lang={lang} />
        </main>
      ) : activeTab === 'apps' ? (
        /* FULL TAB: ILOVALAR */
        <main className="flex-1 overflow-hidden p-4 flex flex-col">
          <AppsTab lang={lang} />
        </main>
      ) : (
        /* WORKSTATION: uch ustunli ish stoli */
        <div className="flex-1 flex overflow-hidden w-full h-full gap-px">
          {/* ======================================================== */}
          {/* CHAP USTUN: brend, vazifalar, profil                        */}
          {/* ======================================================== */}
          <div className="w-60 xl:w-72 flex flex-col border-r border-white/10 shrink-0 bg-[#0a0e1a]/70 backdrop-blur-md">
            {/* Brend paneli */}
            <Window6Brand wsStatus={wsStatus} />

            {/* Vertikal navigatsiya: Evolyusiya birinchi o'rinda.
                Yuqori tab paneli olib tashlangani uchun navigatsiya shu yerda. */}
            <nav aria-label="Ish maydoni navigatsiyasi" className="px-3 py-2 space-y-1 border-b border-white/10">
              {([
                ['evolution', lang === 'uz' ? 'Evolyusiya' : 'Evolution'],
                ['workstation', lang === 'uz' ? 'Studiya' : 'Studio'],
                ['brain', lang === 'uz' ? 'Miya' : 'Brain'],
                ['memory', lang === 'uz' ? 'Xotira' : 'Memory'],
                ['gallery', lang === 'uz' ? 'Artefakt' : 'Artifacts'],
                ['apps', lang === 'uz' ? 'Ilovalar' : 'Apps'],
              ] as const).map(([tabKey, label]) => (
                <button
                  key={tabKey}
                  onClick={() => setActiveTab(tabKey)}
                  aria-pressed={activeTab === tabKey}
                  className={`w-full px-3 py-1.5 rounded-lg text-xs font-medium text-left transition-all border ${
                    activeTab === tabKey
                      ? 'nav-active text-white'
                      : 'bg-slate-900/60 text-slate-300 hover:text-white border-white/[0.06] hover:border-violet-500/40'
                  }`}
                >
                  {label}
                </button>
              ))}
            </nav>

            {/* Dvigatel tanlash: agents.json'dagi barcha AI agent CLI'lar.
                Faol dvigatel ko'k bilan belgilangan; bosilganda /api/engine/select. */}
            <section aria-label="AI dvigatel tanlash" className="px-3 py-2 border-b border-white/10">
              <p className="px-1 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                {lang === 'uz' ? 'AI Dvigatel' : 'AI Engine'}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {engines.map((key) => (
                  <button
                    key={key}
                    onClick={() => selectEngine(key)}
                    aria-pressed={activeEngine === key}
                    title={key}
                    className={`px-2 py-1 rounded-md text-[11px] font-mono transition-all border ${
                      activeEngine === key
                        ? 'bg-cyan-600 text-white border-cyan-400 shadow-sm'
                        : 'bg-slate-900/60 text-slate-400 hover:text-white border-white/[0.06] hover:border-cyan-500/40'
                    }`}
                  >
                    {key}
                  </button>
                ))}
              </div>
            </section>
            <Window5Workspace
              tasks={tasks}
              activeTaskId={currentTask?.task_id || null}
              onSelectTask={(taskId) => {
                const found = tasks.find((t) => t.task_id === taskId);
                if (found) {
                  setCurrentTask(found);
                  if (found.target_agent) {
                    setSelectedAgentId(found.target_agent);
                  }
                  fetch(`/api/tasks/${taskId}/logs`)
                    .then((r) => r.json())
                    .then((d) => {
                      if (Array.isArray(d)) setLogs(d);
                    })
                    .catch(() => {});
                }
              }}
              onCreateTask={async (prompt, targetAgent) => {
                soundEngine.playDispatch();
                // Ask once for notification permission when the user first
                // dispatches a task, so completions can surface later.
                try {
                  if (typeof Notification !== 'undefined' && Notification.permission === 'default') {
                    Notification.requestPermission().catch(() => {});
                  }
                } catch {
                  // ignore
                }
                const res = await fetch('/api/tasks', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ prompt, target_agent: targetAgent, execution_mode: kernelMode }),
                });
                const d = await res.json();
                if (d.task_id && targetAgent) {
                  setSelectedAgentId(targetAgent);
                }
              }}
              lang={lang}
            />

            {/* Profil paneli */}
            <Window7Profile
              lang={lang}
              onToggleLang={() => setLang(lang === 'uz' ? 'en' : 'uz')}
              isDark={isDark}
              onToggleTheme={toggleTheme}
              onKillAll={handleKillAll}
            />
          </div>

          {/* ======================================================== */}
          {/* MARKAZIY USTUN: jonli brauzer + tafsilotlar               */}
          {/* ======================================================== */}
          <div className="flex-1 min-w-0 flex flex-col border-r border-white/10 bg-[#0a0e1a]/70 backdrop-blur-md">
            {/* Dalil, natija va jonli brauzer paneli — markazda */}
            <div className="flex-[3] min-h-0 flex flex-col">
              <Window2Browser
                taskId={currentTask?.task_id}
                screenshotUrl={currentTask?.screenshot_url}
                taskEvidence={currentTask?.evidence}
                taskStatus={currentTask?.status}
                targetApp={selectedAgent?.target_app}
                lang={lang}
              />
            </div>

            {/* Tanlangan subagent tafsilotlari — brauzer ostida */}
            <div className="flex-[2] min-h-0 flex flex-col">
              <Window4SubagentDetail
                selectedAgent={selectedAgent}
                task={
                  // Show the current task only if it belongs to the selected agent;
                  // otherwise fall back to that agent's most recent task so the
                  // detail panel is never blank while data exists.
                  currentTask?.target_agent?.toLowerCase() === selectedAgentId?.toLowerCase()
                    ? currentTask
                    : tasks.find((t) => t.target_agent?.toLowerCase() === selectedAgentId?.toLowerCase()) || null
                }
                logs={logs}
                lang={lang}
              />
            </div>
          </div>

          {/* ======================================================== */}
          {/* O'NG USTUN: terminal va agent tuguni                      */}
          {/* ======================================================== */}
          <div className="w-[380px] lg:w-[480px] xl:w-[560px] 2xl:w-[640px] flex flex-col shrink-0 bg-[#0a0e1a]/70 backdrop-blur-md">
            {/* Agent CLI terminali — asosiy ish maydoni, sudraladigan
                ajratgich orqali balandligi 25%–75% orasida sozlanadi */}
            <div style={{ flexBasis: `${terminalFraction * 100}%` }} className="min-h-0 flex flex-col grow-0 shrink-0 overflow-hidden">
              <Window1Terminal lang={lang} />
            </div>

            {/* Sudraladigan ajratgich (terminal ↔ miya tuguni) */}
            <div
              role="separator"
              aria-orientation="horizontal"
              aria-label={lang === 'uz' ? 'Terminal va miya tuguni o\u2018lchamini o\u2018zgartirish' : 'Resize terminal and agent node'}
              onMouseDown={handleTerminalResizeStart}
              className="h-1.5 shrink-0 cursor-row-resize bg-white/5 hover:bg-blue-500/40 active:bg-blue-500/60 transition-colors flex items-center justify-center group"
              title={lang === 'uz' ? 'Sudrab terminal balandligini o\u2018zgartiring' : 'Drag to resize terminal'}
            >
              <div className="w-10 h-0.5 rounded-full bg-slate-600 group-hover:bg-blue-400 transition-colors" />
            </div>

            {/* Agent tuguni (kartalar) — qolgan balandlik */}
            <div className="flex-1 min-h-0 flex flex-col">
              <Window3BrainGraph
                subagents={subagents}
                activeAgentId={selectedAgentId}
                onSelectAgent={(agentId) => setSelectedAgentId(agentId)}
                activeAgents={tasks
                  .filter((t) => t.status === 'working' && t.target_agent)
                  .map((t) => t.target_agent.toLowerCase())}
                activeCommandTo={
                  brainState?.active_subagent ||
                  (currentTask?.status === 'working' ? currentTask?.target_agent : undefined)
                }
                agentReports={agentReports}
                currentTaskStatus={currentTask?.status}
                lang={lang}
              />
            </div>
          </div>
        </div>
      )}

      {/* 3. Bottom Native Desktop Status Bar */}
      <DesktopStatusBar
        lang={lang}
        wsStatus={wsStatus}
        activeEngine="Claude / AGY CLI"
        activeSubagent={brainState?.active_subagent || currentTask?.target_agent}
        taskCount={tasks.length}
      />

      {/* Bosqich 2: 4 Top Bar Modals */}
      <EvolutionModal
        isOpen={isEvolutionOpen}
        onClose={() => setIsEvolutionOpen(false)}
        lang={lang}
      />

      <ApprovalsModal
        isOpen={isApprovalsOpen}
        onClose={() => setIsApprovalsOpen(false)}
        approvals={approvals}
        onResolve={handleResolveApproval}
        onApproveAll={handleApproveAll}
        lang={lang}
      />

      <ResourceModal
        isOpen={isResourcesOpen}
        onClose={() => setIsResourcesOpen(false)}
        lang={lang}
      />

      <ConnectionsModal
        isOpen={isConnectionsOpen}
        onClose={() => setIsConnectionsOpen(false)}
        lang={lang}
      />

      {/* Ctrl+K Command Palette */}
      <CommandPalette
        isOpen={isCmdOpen}
        onClose={() => setIsCmdOpen(false)}
        subagents={subagents}
        onSelectAgent={(id) => setSelectedAgentId(id)}
        onKillAll={handleKillAll}
        onToggleLang={() => setLang(lang === 'uz' ? 'en' : 'uz')}
        onTriggerPreset={async (p, a) => {
          await fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: p, target_agent: a }),
          });
        }}
        lang={lang}
      />
      {/* Aurora nur qatlami — panellar USTIDA screen-blend bilan (faqat yoritadi) */}
      <div aria-hidden className="pointer-events-none fixed inset-0 z-[1] mix-blend-screen">
        <div className="absolute -top-48 -left-40 w-[720px] h-[600px] rounded-full opacity-80 blur-[100px]"
          style={{ background: 'radial-gradient(circle, rgba(124,58,237,0.5), transparent 68%)' }} />
        <div className="absolute -top-32 right-0 w-[640px] h-[520px] rounded-full opacity-70 blur-[100px]"
          style={{ background: 'radial-gradient(circle, rgba(34,211,238,0.35), transparent 65%)' }} />
        <div className="absolute bottom-[-200px] left-1/3 w-[760px] h-[500px] rounded-full opacity-60 blur-[120px]"
          style={{ background: 'radial-gradient(circle, rgba(99,102,241,0.35), transparent 65%)' }} />
      </div>
    </div>
  );
}
