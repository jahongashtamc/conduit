'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  Background,
  Controls,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Activity,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  ChevronRight,
  X,
  Search,
  RotateCcw,
  Bot,
  Layers,
  Terminal,
  Loader2,
  FileCheck2,
} from 'lucide-react';
import { Language } from '@/lib/translations';

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
  created_at: string;
}

interface BrainHeartTabProps {
  currentTask: Task | null;
  tasks: Task[];
  lang: Language;
  onRetryTask?: (taskId: string) => Promise<void>;
}

export const BrainHeartTab: React.FC<BrainHeartTabProps> = ({
  currentTask,
  tasks,
  lang,
  onRetryTask,
}) => {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [taskLogs, setTaskLogs] = useState<any[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  // Determine active state in Heart state machine
  const activeTask = currentTask || (tasks.length > 0 ? tasks[0] : null);
  const currentStep = activeTask?.current_step || 'idle';
  const taskStatus = (activeTask?.status || 'idle').toUpperCase();
  const activeAgent = (activeTask?.target_agent || '').toLowerCase();

  const isQueued = taskStatus === 'IDLE' || currentStep === 'idle';
  const isPlanning = currentStep === 'planner' || taskStatus === 'PLANNING';
  const isRunning = currentStep === 'doer' || taskStatus === 'RUNNING' || taskStatus === 'WORKING';
  const isVerifying = currentStep === 'checker' || taskStatus === 'CHECKING';
  const isDone = taskStatus === 'PASS';
  const isFailed = taskStatus === 'FAIL' || taskStatus === 'BLOCKED';

  // Fetch logs when drawer opens
  useEffect(() => {
    if (selectedTask?.task_id) {
      setLoadingLogs(true);
      fetch(`/api/tasks/${selectedTask.task_id}/logs`)
        .then((r) => r.json())
        .then((data) => {
          if (Array.isArray(data)) setTaskLogs(data);
          setLoadingLogs(false);
        })
        .catch(() => setLoadingLogs(false));
    } else {
      setTaskLogs([]);
    }
  }, [selectedTask]);

  // Construct React Flow Nodes
  const nodes: Node[] = useMemo(() => {
    const getNodeStyle = (isActive: boolean, colorClass: string, isTerminalDone = false, isTerminalFail = false) => ({
      padding: '8px 12px',
      borderRadius: '10px',
      fontSize: '11px',
      fontWeight: 600,
      fontFamily: 'monospace',
      border: isActive
        ? isTerminalFail
          ? '2px solid #f43f5e'
          : isTerminalDone
          ? '2px solid #10b981'
          : '2px solid #3b82f6'
        : '1px solid rgba(255, 255, 255, 0.1)',
      backgroundColor: isActive
        ? isTerminalFail
          ? 'rgba(244, 63, 94, 0.2)'
          : isTerminalDone
          ? 'rgba(16, 185, 129, 0.2)'
          : 'rgba(59, 130, 246, 0.2)'
        : 'rgba(15, 23, 42, 0.85)',
      color: isActive ? '#ffffff' : '#94a3b8',
      boxShadow: isActive ? '0 0 15px rgba(59, 130, 246, 0.4)' : 'none',
      width: 140,
      textAlign: 'center' as const,
    });

    return [
      // 1. Miya (Brain Node)
      {
        id: 'brain',
        position: { x: 20, y: 160 },
        data: { label: '🧠 MIYA (Brain)\nQaror AI' },
        style: {
          padding: '10px',
          borderRadius: '12px',
          fontSize: '12px',
          fontWeight: 700,
          border: isPlanning || isRunning ? '2px solid #60a5fa' : '1px solid rgba(255, 255, 255, 0.15)',
          backgroundColor: isPlanning || isRunning ? 'rgba(37, 99, 235, 0.25)' : 'rgba(30, 41, 59, 0.9)',
          color: '#ffffff',
          boxShadow: isPlanning || isRunning ? '0 0 20px rgba(59, 130, 246, 0.5)' : 'none',
          width: 130,
          textAlign: 'center',
          whiteSpace: 'pre-line',
        },
      },

      // 2. Yurak State Machine Nodes
      {
        id: 'state_queued',
        position: { x: 210, y: 30 },
        data: { label: '1. Queued (Navbatda)' },
        style: getNodeStyle(isQueued, 'blue'),
      },
      {
        id: 'state_planning',
        position: { x: 210, y: 95 },
        data: { label: '2. Planning (Reja)' },
        style: getNodeStyle(isPlanning, 'blue'),
      },
      {
        id: 'state_running',
        position: { x: 210, y: 160 },
        data: { label: '3. Running (Ijro)' },
        style: getNodeStyle(isRunning, 'blue'),
      },
      {
        id: 'state_verifying',
        position: { x: 210, y: 225 },
        data: { label: '4. Verifying (Tekshiruv)' },
        style: getNodeStyle(isVerifying, 'blue'),
      },
      {
        id: 'state_terminal',
        position: { x: 210, y: 290 },
        data: {
          label: isDone ? '5. DONE (PASS) ✨' : isFailed ? '5. FAILED / BLOCKED ❌' : '5. Done / Failed',
        },
        style: getNodeStyle(isDone || isFailed, isDone ? 'emerald' : 'rose', isDone, isFailed),
      },

      // 3. Subagents Roster Nodes
      {
        id: 'agent_scout',
        position: { x: 410, y: 50 },
        data: { label: '🌐 Scout\nBrauzer & Qidiruv' },
        style: getNodeStyle(activeAgent === 'scout' && isRunning, 'cyan'),
      },
      {
        id: 'agent_designer',
        position: { x: 410, y: 125 },
        data: { label: '🎨 Designer\nFigma & UI Spec' },
        style: getNodeStyle(activeAgent === 'designer' && isRunning, 'purple'),
      },
      {
        id: 'agent_inspector',
        position: { x: 410, y: 200 },
        data: { label: '🔍 Inspector\nAudit & Dalil' },
        style: getNodeStyle(activeAgent === 'inspector' && isRunning, 'emerald'),
      },
      {
        id: 'agent_coder',
        position: { x: 410, y: 275 },
        data: { label: '💻 Coder\nKod & Terminal' },
        style: getNodeStyle(activeAgent === 'coder' && isRunning, 'indigo'),
      },
    ];
  }, [isQueued, isPlanning, isRunning, isVerifying, isDone, isFailed, activeAgent]);

  // Construct React Flow Edges
  const edges: Edge[] = useMemo(() => [
    // Miya -> States
    {
      id: 'e-brain-planning',
      source: 'brain',
      target: 'state_planning',
      animated: isPlanning,
      style: { stroke: isPlanning ? '#60a5fa' : '#475569', strokeWidth: isPlanning ? 2 : 1 },
      markerEnd: { type: MarkerType.ArrowClosed, color: isPlanning ? '#60a5fa' : '#475569' },
    },
    {
      id: 'e-planning-running',
      source: 'state_planning',
      target: 'state_running',
      animated: isRunning,
      style: { stroke: isRunning ? '#60a5fa' : '#475569', strokeWidth: isRunning ? 2 : 1 },
      markerEnd: { type: MarkerType.ArrowClosed, color: isRunning ? '#60a5fa' : '#475569' },
    },
    {
      id: 'e-running-verifying',
      source: 'state_running',
      target: 'state_verifying',
      animated: isVerifying,
      style: { stroke: isVerifying ? '#60a5fa' : '#475569', strokeWidth: isVerifying ? 2 : 1 },
      markerEnd: { type: MarkerType.ArrowClosed, color: isVerifying ? '#60a5fa' : '#475569' },
    },
    {
      id: 'e-verifying-terminal',
      source: 'state_verifying',
      target: 'state_terminal',
      animated: isDone || isFailed,
      style: {
        stroke: isDone ? '#10b981' : isFailed ? '#f43f5e' : '#475569',
        strokeWidth: isDone || isFailed ? 2 : 1,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: isDone ? '#10b981' : isFailed ? '#f43f5e' : '#475569',
      },
    },

    // Running -> Subagents
    {
      id: 'e-run-scout',
      source: 'state_running',
      target: 'agent_scout',
      animated: activeAgent === 'scout' && isRunning,
      style: { stroke: activeAgent === 'scout' ? '#06b6d4' : '#334155' },
    },
    {
      id: 'e-run-designer',
      source: 'state_running',
      target: 'agent_designer',
      animated: activeAgent === 'designer' && isRunning,
      style: { stroke: activeAgent === 'designer' ? '#a855f7' : '#334155' },
    },
    {
      id: 'e-run-inspector',
      source: 'state_verifying',
      target: 'agent_inspector',
      animated: activeAgent === 'inspector' && isRunning,
      style: { stroke: activeAgent === 'inspector' ? '#10b981' : '#334155' },
    },
    {
      id: 'e-run-coder',
      source: 'state_running',
      target: 'agent_coder',
      animated: activeAgent === 'coder' && isRunning,
      style: { stroke: activeAgent === 'coder' ? '#818cf8' : '#334155' },
    },
  ], [isPlanning, isRunning, isVerifying, isDone, isFailed, activeAgent]);

  // Filter tasks
  const filteredTasks = tasks.filter((t) =>
    t.prompt.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.task_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.target_agent.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleRetry = async (taskId: string) => {
    if (!onRetryTask) return;
    setIsRetrying(true);
    try {
      await onRetryTask(taskId);
    } finally {
      setIsRetrying(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col lg:flex-row gap-4 h-full overflow-hidden select-none">
      {/* LEFT: React Flow Graph of Miya & Yurak */}
      <div className="flex-1 bg-slate-900/60 border border-white/[0.08] rounded-2xl flex flex-col overflow-hidden shadow-xl">
        <div className="p-3.5 border-b border-white/[0.08] flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center space-x-2">
            <span className="text-base">🧠</span>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              {lang === 'uz' ? 'Miya va Yurak Oqim Grafi' : 'Brain & Heart State Graph'}
            </h3>
          </div>
          <span className="text-[10px] font-mono text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-white/5">
            Holat: <span className="text-blue-400 font-bold">{taskStatus}</span>
          </span>
        </div>

        <div className="flex-1 w-full h-[380px] lg:h-full bg-slate-950/70">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            minZoom={0.6}
            maxZoom={1.5}
            attributionPosition="bottom-left"
          >
            <Background color="#1e293b" gap={16} />
            <Controls className="bg-slate-900 border border-slate-700 text-white rounded-lg" />
          </ReactFlow>
        </div>
      </div>

      {/* RIGHT: Task Queue Table */}
      <div className="w-full lg:w-[480px] bg-slate-900/60 border border-white/[0.08] rounded-2xl flex flex-col overflow-hidden shadow-xl">
        <div className="p-3.5 border-b border-white/[0.08] flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-blue-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              {lang === 'uz' ? 'Vazifalar Navbati va Tarixi' : 'Task Queue & History'}
            </h3>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            {filteredTasks.length} {lang === 'uz' ? 'ta' : 'items'}
          </span>
        </div>

        {/* Search Bar */}
        <div className="p-2.5 border-b border-white/[0.06] bg-slate-950/30">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={lang === 'uz' ? 'Vazifa yoki ID bo\'yicha qidirish...' : 'Search tasks...'}
              className="w-full bg-slate-950/80 border border-white/[0.06] rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/80"
            />
          </div>
        </div>

        {/* Table Content */}
        <div className="scroll-area flex-1 divide-y divide-white/[0.04]">
          {filteredTasks.length === 0 ? (
            <div className="py-12 px-4 text-center text-slate-500">
              <Bot className="w-8 h-8 text-slate-600 mx-auto mb-2 stroke-[1.5]" />
              <p className="text-xs font-medium text-slate-400">
                {lang === 'uz' ? 'Hozircha vazifalar mavjud emas' : 'No tasks recorded'}
              </p>
              <p className="text-[11px] text-slate-600 mt-0.5">
                {lang === 'uz' ? 'Vazifa yuborilgach, uning navbati va natijasi shu yerda to\'planadi' : 'Dispatched tasks will appear here'}
              </p>
            </div>
          ) : (
            filteredTasks.map((t) => {
              const isPass = t.status.toUpperCase() === 'PASS';
              const isFail = t.status.toUpperCase() === 'FAIL';
              const isBlocked = t.status.toUpperCase() === 'BLOCKED';
              const isWorking = !isPass && !isFail && !isBlocked;

              return (
                <div
                  key={t.task_id}
                  onClick={() => setSelectedTask(t)}
                  className="p-3 hover:bg-white/[0.03] cursor-pointer transition flex items-center justify-between group"
                >
                  <div className="min-w-0 flex-1 pr-3">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-mono text-[10px] text-slate-500">
                        {t.task_id}
                      </span>
                      <span className="px-1.5 py-0.2 rounded bg-slate-800 text-[9px] font-mono uppercase text-slate-300">
                        {t.target_agent}
                      </span>
                    </div>
                    <p className="text-xs text-slate-200 font-medium truncate">
                      {t.prompt}
                    </p>
                    <div className="flex items-center space-x-2 text-[10px] text-slate-500 mt-1">
                      <Clock className="w-3 h-3 text-slate-600" />
                      <span>{t.created_at?.split('T')[1]?.substring(0, 8) || t.created_at}</span>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div className="flex items-center space-x-2 shrink-0">
                    {isPass ? (
                      <span className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 text-[10px] font-bold">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>PASS</span>
                      </span>
                    ) : isFail ? (
                      <span className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-300 text-[10px] font-bold">
                        <XCircle className="w-3 h-3" />
                        <span>FAIL</span>
                      </span>
                    ) : isBlocked ? (
                      <span className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 text-[10px] font-bold">
                        <AlertCircle className="w-3 h-3" />
                        <span>BLOCKED</span>
                      </span>
                    ) : (
                      <span className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-300 text-[10px] font-bold animate-pulse">
                        <Activity className="w-3 h-3" />
                        <span>{t.current_step}</span>
                      </span>
                    )}
                    <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-300 group-hover:translate-x-0.5 transition" />
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* DETAIL DRAWER */}
      {selectedTask && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-lg bg-slate-900 border-l border-white/[0.08] h-full flex flex-col shadow-2xl p-5 overflow-y-auto animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.08] mb-4">
              <div>
                <span className="text-[10px] font-mono text-slate-500">
                  {selectedTask.task_id}
                </span>
                <h3 className="text-sm font-bold text-white mt-0.5">
                  {selectedTask.prompt}
                </h3>
              </div>
              <button
                onClick={() => setSelectedTask(null)}
                className="p-1 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Task Info & Status */}
            <div className="space-y-4 text-xs">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-white/[0.06]">
                <span className="text-slate-400">Ijrochi subagent:</span>
                <span className="font-mono font-semibold uppercase text-blue-400">
                  {selectedTask.target_agent}
                </span>
              </div>

              {/* Status and Action */}
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-white/[0.06]">
                <span className="text-slate-400">Holat:</span>
                <div className="flex items-center space-x-2">
                  <span className={`font-bold px-2.5 py-0.5 rounded-full text-[11px] ${
                    selectedTask.status.toUpperCase() === 'PASS'
                      ? 'bg-emerald-500/15 text-emerald-300'
                      : selectedTask.status.toUpperCase() === 'FAIL'
                      ? 'bg-rose-500/15 text-rose-300'
                      : 'bg-amber-500/15 text-amber-300'
                  }`}>
                    {selectedTask.status}
                  </span>
                  {(selectedTask.status.toUpperCase() === 'FAIL' || selectedTask.status.toUpperCase() === 'BLOCKED') && (
                    <button
                      onClick={() => handleRetry(selectedTask.task_id)}
                      disabled={isRetrying}
                      className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-semibold transition active:scale-95"
                    >
                      <RotateCcw className={`w-3 h-3 ${isRetrying ? 'animate-spin' : ''}`} />
                      <span>{lang === 'uz' ? 'Qayta urinish' : 'Retry'}</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Evidence */}
              {selectedTask.evidence && (
                <div className="space-y-1.5">
                  <span className="text-[11px] font-bold uppercase text-slate-400">
                    Dalil & Natija:
                  </span>
                  <div className="p-3 rounded-xl bg-slate-950 border border-white/[0.06] font-mono text-[11px] text-slate-300 whitespace-pre-wrap">
                    {selectedTask.evidence}
                  </div>
                </div>
              )}

              {/* Steps Output */}
              {selectedTask.planner_output && (
                <div className="space-y-1">
                  <span className="text-[11px] font-semibold text-blue-400">Planner Rejasi:</span>
                  <div className="p-2.5 rounded-lg bg-slate-950/80 border border-white/[0.04] text-[11px] text-slate-300 whitespace-pre-wrap">
                    {selectedTask.planner_output}
                  </div>
                </div>
              )}

              {selectedTask.doer_output && (
                <div className="space-y-1">
                  <span className="text-[11px] font-semibold text-amber-400">Doer Amali:</span>
                  <div className="p-2.5 rounded-lg bg-slate-950/80 border border-white/[0.04] text-[11px] text-slate-300 whitespace-pre-wrap">
                    {selectedTask.doer_output}
                  </div>
                </div>
              )}

              {/* Logs */}
              <div className="space-y-1.5 pt-2">
                <span className="text-[11px] font-bold uppercase text-slate-400 flex items-center space-x-1">
                  <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Jarayon Loglari:</span>
                </span>
                <div className="h-44 overflow-y-auto p-2.5 rounded-xl bg-slate-950 border border-white/[0.06] font-mono text-[10px] space-y-1">
                  {loadingLogs ? (
                    <div className="flex items-center justify-center h-full text-slate-500">
                      <Loader2 className="w-4 h-4 animate-spin mr-1.5" />
                      <span>Yuklanmoqda...</span>
                    </div>
                  ) : taskLogs.length === 0 ? (
                    <div className="text-center py-8 text-slate-600">Loglar mavjud emas</div>
                  ) : (
                    taskLogs.map((log, idx) => (
                      <div key={idx} className="border-b border-white/[0.02] pb-1">
                        <span className="text-slate-500 mr-1.5">[{log.agent_name}]</span>
                        <span className="text-slate-300">{log.message}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
