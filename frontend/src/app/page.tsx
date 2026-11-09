'use client';

import React, { useState, useEffect, useRef } from 'react';
import gsap from 'gsap';
import { StudioTopBar } from '@/components/DesktopTitlebar';
import { DesktopStatusBar } from '@/components/DesktopStatusBar';
import { ApprovalModal, ApprovalItem } from '@/components/ApprovalModal';
import { CommandPalette } from '@/components/CommandPalette';
import { BrainHeartTab } from '@/components/BrainHeartTab';
import { MemoryTab } from '@/components/MemoryTab';
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

interface AppItem {
  id: string;
  name: string;
  category: string;
  status: 'ready' | 'not installed' | 'running';
  icon: string;
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
  const [apps, setApps] = useState<AppItem[]>([]);
  const [subagents, setSubagents] = useState<Subagent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>('scout');
  const [brainState, setBrainState] = useState<any>(null);
  const [agentReports, setAgentReports] = useState<Record<string, { status: 'PASS' | 'FAIL' | 'BLOCKED'; evidence?: string }>>({});
  const [activeTab, setActiveTab] = useState<'workstation' | 'brain' | 'memory' | 'apps'>('workstation');
  const [isCmdOpen, setIsCmdOpen] = useState(false);

  // Bosqich 2 Modal States
  const [isEvolutionOpen, setIsEvolutionOpen] = useState(false);
  const [isApprovalsOpen, setIsApprovalsOpen] = useState(false);
  const [isResourcesOpen, setIsResourcesOpen] = useState(false);
  const [isConnectionsOpen, setIsConnectionsOpen] = useState(false);
  const [skillsCount, setSkillsCount] = useState(3);
  const [resourceSummary, setResourceSummary] = useState<any>(null);
  const [connections, setConnections] = useState<any[]>([]);
  const [kernelMode, setKernelMode] = useState<string>('standard');

  // Fetch initial REST data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [appsRes, agentsRes, tasksRes, apprRes, skillsRes, resRes, connRes, kernelRes] = await Promise.all([
          fetch('/api/apps').then((r) => r.json()).catch(() => []),
          fetch('/api/subagents').then((r) => r.json()).catch(() => []),
          fetch('/api/tasks').then((r) => r.json()).catch(() => []),
          fetch('/api/approvals').then((r) => r.json()).catch(() => []),
          fetch('/api/skills').then((r) => r.json()).catch(() => []),
          fetch('/api/resources').then((r) => r.json()).catch(() => null),
          fetch('/api/connections').then((r) => r.json()).catch(() => []),
          fetch('/api/kernel/settings').then((r) => r.json()).catch(() => null),
        ]);
        if (Array.isArray(appsRes)) setApps(appsRes);
        if (Array.isArray(agentsRes)) {
          setSubagents(agentsRes);
          if (agentsRes.length > 0 && !selectedAgentId) {
            setSelectedAgentId(agentsRes[0].id);
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
    let reconnectTimeout: any = null;

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
            if (msg.apps) setApps(msg.apps);
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
                [msg.target_agent.toLowerCase()]: {
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
            setBrainState((prev: any) => (prev ? { ...prev, active_subagent: ag } : null));
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
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

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
    <div className="flex flex-col w-screen h-screen overflow-hidden bg-black text-zinc-100 font-sans">
      {/* 1. Global Native PC Desktop Studio TopBar */}
      <StudioTopBar
        lang={lang}
        onToggleLang={() => setLang(lang === 'uz' ? 'en' : 'uz')}
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
        wsStatus={wsStatus}
        onKillAll={handleKillAll}
        onOpenCmd={() => setIsCmdOpen(true)}
        onOpenEvolution={() => setIsEvolutionOpen(true)}
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
        showDetails={true}
      />

      {/* 2. Main Studio Viewport */}
      {activeTab === 'brain' ? (
        /* FULL TAB: MIYA & YURAK */
        <main className="flex-1 overflow-hidden p-4 bg-black flex flex-col">
          <BrainHeartTab
            currentTask={currentTask}
            tasks={tasks}
            lang={lang}
            onRetryTask={handleRetryTask}
          />
        </main>
      ) : activeTab === 'memory' ? (
        /* FULL TAB: XOTIRA */
        <main className="flex-1 overflow-hidden p-4 bg-black flex flex-col">
          <MemoryTab lang={lang} />
        </main>
      ) : activeTab === 'apps' ? (
        /* FULL TAB: ILOVALAR */
        <main className="flex-1 overflow-hidden p-4 bg-black flex flex-col">
          <AppsTab lang={lang} />
        </main>
      ) : (
        /* WORKSTATION: 7-OYNALI ANIQ JOYLASHUV (7-WINDOW LAYOUT) */
        <div className="flex-1 flex overflow-hidden w-full h-full bg-black">
          {/* ======================================================== */}
          {/* CHAP USTUN (LEFT COLUMN): OYNA 6, OYNA 5, OYNA 7         */}
          {/* ======================================================== */}
          <div className="w-64 lg:w-72 flex flex-col border-r border-white/10 shrink-0 bg-black/95">
            {/* Oyna 6 (chap yuqori, kichik): Faqat Conduit logosi */}
            <Window6Brand wsStatus={wsStatus} />

            {/* Oyna 5 (chap, uzun): Tasklar va Widgetlar rejimi */}
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

            {/* Oyna 7 (chap pastki, kichik): Profil va Sozlamalar modal */}
            <Window7Profile
              lang={lang}
              onToggleLang={() => setLang(lang === 'uz' ? 'en' : 'uz')}
              isDark={isDark}
              onToggleTheme={toggleTheme}
              onKillAll={handleKillAll}
            />
          </div>

          {/* ======================================================== */}
          {/* MARKAZIY USTUN (CENTER COLUMN): OYNA 3, OYNA 4           */}
          {/* ======================================================== */}
          <div className="flex-1 min-w-0 flex flex-col border-r border-white/10 bg-black">
            {/* Oyna 3 (katta, markaz-yuqori): Bosh agent tuguni & subagentlar (faqat nomlari, jonli animatsiya) */}
            <Window3BrainGraph
              subagents={subagents}
              activeAgentId={selectedAgentId}
              onSelectAgent={(agentId) => setSelectedAgentId(agentId)}
              activeAgents={tasks.filter((t) => t.status === 'working').map((t) => t.target_agent.toLowerCase())}
              activeCommandTo={brainState?.active_subagent || currentTask?.target_agent}
              agentReports={agentReports}
              currentTaskStatus={currentTask?.status}
              lang={lang}
            />

            {/* Oyna 4 (markaz-pastki): Subagent ishi, qadamlar tarixi, skrinshot va loglar */}
            <Window4SubagentDetail
              selectedAgent={selectedAgent}
              task={currentTask?.target_agent.toLowerCase() === selectedAgentId?.toLowerCase() ? currentTask : null}
              logs={logs}
              lang={lang}
            />
          </div>

          {/* ======================================================== */}
          {/* O'NG USTUN (RIGHT COLUMN): OYNA 1, OYNA 2                */}
          {/* ======================================================== */}
          <div className="w-[420px] lg:w-[520px] xl:w-[620px] 2xl:w-[720px] flex flex-col shrink-0 bg-black/95">
            {/* Oyna 1 (yuqori o'ng): Agent CLI Terminali (xterm.js + ws/terminal) */}
            <Window1Terminal lang={lang} />

            {/* Oyna 2 (pastki o'ng, tor va uzun): Brauzer & Natija / Dalil paneli */}
            <Window2Browser
              taskId={currentTask?.task_id}
              screenshotUrl={currentTask?.screenshot_url}
              taskEvidence={currentTask?.evidence}
              taskStatus={currentTask?.status}
              targetApp={selectedAgent?.target_app}
              lang={lang}
            />
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
    </div>
  );
}
