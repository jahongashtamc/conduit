'use client';

import React, { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Play, 
  Plus, 
  RotateCw, 
  Sparkles, 
  Layers, 
  LayoutGrid, 
  Activity, 
  Cpu, 
  AlertTriangle,
  FileText,
  Search,
  Box,
  ShieldCheck,
  Video
} from 'lucide-react';

export interface TaskItem {
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

interface Window5WorkspaceProps {
  tasks: TaskItem[];
  activeTaskId: string | null;
  onSelectTask: (taskId: string) => void;
  onCreateTask: (prompt: string, targetAgent: string) => Promise<void>;
  lang: 'uz' | 'en';
}

export const Window5Workspace: React.FC<Window5WorkspaceProps> = ({
  tasks,
  activeTaskId,
  onSelectTask,
  onCreateTask,
  lang,
}) => {
  const [mode, setMode] = useState<'tasks' | 'widgets'>('tasks');
  const [showNewTaskForm, setShowNewTaskForm] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('scout');
  const [scratchpadNote, setScratchpadNote] = useState('Conduit arxitekturasi: Miya (qaror) + Yurak (holat).');

  const runningTasks = tasks.filter((t) => t.status === 'working');
  const finishedTasks = tasks.filter((t) => t.status !== 'working');

  const presets = [
    { label: 'Scout: Veb qidiruv', agent: 'scout', prompt: 'Google orqali Conduit haqida qidiruv va tahlil' },
    { label: 'Sculptor: 3D render', agent: 'sculptor', prompt: '3D kubik geometriya render qilish' },
    { label: 'Inspector: Kod auditi', agent: 'inspector', prompt: 'Xavfsizlik va zaifliklar auditi' },
    { label: 'Designer: Figma UI', agent: 'designer', prompt: 'Figma dizayn tokenlari tekshiruvi' },
    { label: 'Animator: Video', agent: 'animator', prompt: 'Launch video generatsiyasi' },
  ];

  const handleLaunchPreset = (prompt: string, agent: string) => {
    onCreateTask(prompt, agent);
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customPrompt.trim()) return;
    onCreateTask(customPrompt.trim(), selectedAgent);
    setCustomPrompt('');
    setShowNewTaskForm(false);
  };

  return (
    <div className="flex-1 flex flex-col bg-slate-950/60 overflow-hidden select-none border-b border-white/5">
      {/* 1. Mode Switcher: Tasklar | Widgetlar */}
      <div className="px-3 pt-2.5 pb-2 border-b border-white/10 bg-slate-900/60">
        <div className="flex items-center p-0.5 rounded-lg bg-slate-950 border border-white/10">
          <button
            onClick={() => setMode('tasks')}
            className={`flex-1 py-1 rounded-md text-[11px] font-semibold transition-all flex items-center justify-center space-x-1.5 ${
              mode === 'tasks'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>{lang === 'uz' ? 'Tasklar' : 'Tasks'}</span>
            <span className="px-1.5 py-0.2 rounded-full bg-black/30 text-[9px] font-mono">
              {tasks.length}
            </span>
          </button>
          <button
            onClick={() => setMode('widgets')}
            className={`flex-1 py-1 rounded-md text-[11px] font-semibold transition-all flex items-center justify-center space-x-1.5 ${
              mode === 'widgets'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            <span>{lang === 'uz' ? 'Widgetlar' : 'Widgets'}</span>
          </button>
        </div>
      </div>

      {/* 2. BODY CONTENT */}
      {mode === 'tasks' ? (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header Controls: Presets & New Task Button */}
          <div className="p-3 border-b border-white/5 bg-slate-950/40 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                {lang === 'uz' ? 'Tezkor Shablonlar' : 'Quick Templates'}
              </span>
              <button
                onClick={() => setShowNewTaskForm(!showNewTaskForm)}
                className="px-2 py-0.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-semibold flex items-center space-x-1 transition shadow-sm"
              >
                <Plus className="w-3 h-3" />
                <span>{lang === 'uz' ? 'Yangi vazifa' : 'New Task'}</span>
              </button>
            </div>

            {/* Presets Grid */}
            <div className="flex flex-wrap gap-1.5">
              {presets.map((p) => (
                <button
                  key={p.label}
                  onClick={() => handleLaunchPreset(p.prompt, p.agent)}
                  className="px-2 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-white/5 hover:border-blue-500/30 text-[10px] text-slate-300 hover:text-white transition-all flex items-center space-x-1"
                >
                  <Play className="w-2.5 h-2.5 text-blue-400" />
                  <span>{p.label}</span>
                </button>
              ))}
            </div>

            {/* Custom New Task Drawer */}
            {showNewTaskForm && (
              <form onSubmit={handleCustomSubmit} className="p-2.5 rounded-lg bg-slate-900 border border-blue-500/30 space-y-2 animate-in fade-in">
                <input
                  type="text"
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="Yangi vazifa prompti..."
                  className="w-full px-2.5 py-1.5 rounded bg-slate-950 border border-white/10 text-xs text-white focus:outline-none focus:border-blue-500"
                />
                <div className="flex items-center justify-between gap-2">
                  <select
                    value={selectedAgent}
                    onChange={(e) => setSelectedAgent(e.target.value)}
                    className="px-2 py-1 rounded bg-slate-950 border border-white/10 text-[11px] text-slate-300"
                  >
                    <option value="scout">Scout</option>
                    <option value="sculptor">Sculptor</option>
                    <option value="inspector">Inspector</option>
                    <option value="designer">Designer</option>
                    <option value="animator">Animator</option>
                  </select>
                  <div className="flex items-center space-x-1">
                    <button
                      type="button"
                      onClick={() => setShowNewTaskForm(false)}
                      className="px-2 py-1 rounded bg-slate-800 text-slate-400 text-[10px]"
                    >
                      Bekor
                    </button>
                    <button
                      type="submit"
                      className="px-2.5 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-bold"
                    >
                      Boshlash
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>

          {/* Task Lists (Scrollable) */}
          <div className="flex-1 overflow-y-auto p-2.5 space-y-3">
            {/* 1. Ishlayotgan (Parallel) Vazifalar */}
            {runningTasks.length > 0 && (
              <div className="space-y-1.5">
                <div className="flex items-center justify-between px-1">
                  <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider flex items-center space-x-1.5">
                    <RotateCw className="w-3 h-3 animate-spin text-amber-400" />
                    <span>{lang === 'uz' ? 'Ishlayotgan (Parallel)' : 'Running Parallel'} ({runningTasks.length})</span>
                  </span>
                </div>
                {runningTasks.map((task) => {
                  const isSelected = activeTaskId === task.task_id;
                  return (
                    <div
                      key={task.task_id}
                      onClick={() => onSelectTask(task.task_id)}
                      className={`p-2.5 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-amber-950/40 border-amber-500/60 shadow-md shadow-amber-950/30'
                          : 'bg-slate-900/80 border-amber-500/20 hover:border-amber-500/40'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[10px] font-mono uppercase font-bold">
                          {task.target_agent}
                        </span>
                        <span className="text-[10px] text-amber-300 font-mono flex items-center space-x-1">
                          <RotateCw className="w-2.5 h-2.5 animate-spin" />
                          <span>{task.current_step}</span>
                        </span>
                      </div>
                      <p className="text-xs text-white font-medium line-clamp-1">{task.prompt}</p>
                      <div className="text-[9px] text-slate-400 font-mono mt-1">ID: {task.task_id}</div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* 2. Navbatdagi & Yakunlangan Vazifalar */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-1 block">
                {lang === 'uz' ? 'Vazifalar Tarixi & Holati' : 'Task History & Queue'} ({finishedTasks.length})
              </span>

              {finishedTasks.length === 0 ? (
                <div className="p-4 rounded-xl border border-dashed border-white/10 text-center text-slate-500 text-xs">
                  {lang === 'uz' ? 'Hozircha yakunlangan vazifa yo\'q' : 'No tasks yet'}
                </div>
              ) : (
                finishedTasks.map((task) => {
                  const isSelected = activeTaskId === task.task_id;
                  const isPass = task.status === 'PASS';
                  const isFail = task.status === 'FAIL';
                  const isBlocked = task.status === 'BLOCKED';

                  return (
                    <div
                      key={task.task_id}
                      onClick={() => onSelectTask(task.task_id)}
                      className={`p-2.5 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? 'bg-blue-950/40 border-blue-500/60 shadow-md shadow-blue-950/30'
                          : 'bg-slate-900/50 border-white/5 hover:border-white/10 hover:bg-slate-900/80'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center space-x-1.5">
                          <span className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 border border-white/5 text-[10px] font-mono uppercase font-bold">
                            {task.target_agent}
                          </span>
                          <span
                            className={`px-1.5 py-0.2 rounded text-[9px] font-mono font-black uppercase ${
                              isPass
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : isFail
                                ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                                : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                            }`}
                          >
                            {task.status}
                          </span>
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {task.total_duration ? `${task.total_duration}s` : ''}
                        </span>
                      </div>
                      <p className="text-xs text-slate-200 line-clamp-1">{task.prompt}</p>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      ) : (
        /* WIDGETLAR REJIMI (FORMER EMPTY SLOT NOW HOUSES REAL WIDGETS) */
        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          {/* Widget 1: System Quick Stats */}
          <div className="p-3 rounded-xl bg-slate-900/80 border border-white/10 space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-200">
              <span className="flex items-center space-x-1.5">
                <Activity className="w-3.5 h-3.5 text-blue-400" />
                <span>{lang === 'uz' ? 'Tizim Statistikasi' : 'System Metrics'}</span>
              </span>
              <span className="px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-mono">
                WAL FAOL
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <div className="p-2 rounded bg-slate-950 border border-white/5">
                <div className="text-slate-400 text-[10px]">Parallel Limit</div>
                <div className="text-sm font-bold text-white">N = 3</div>
              </div>
              <div className="p-2 rounded bg-slate-950 border border-white/5">
                <div className="text-slate-400 text-[10px]">Heartbeat Timeout</div>
                <div className="text-sm font-bold text-white">30s</div>
              </div>
            </div>
          </div>

          {/* Widget 2: Scratchpad / Tezkor Qaydlar */}
          <div className="p-3 rounded-xl bg-slate-900/80 border border-white/10 space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-200">
              <span className="flex items-center space-x-1.5">
                <FileText className="w-3.5 h-3.5 text-indigo-400" />
                <span>{lang === 'uz' ? 'Qaydlar (Scratchpad)' : 'Scratchpad'}</span>
              </span>
            </div>
            <textarea
              rows={4}
              value={scratchpadNote}
              onChange={(e) => setScratchpadNote(e.target.value)}
              className="w-full p-2 rounded-lg bg-slate-950 border border-white/5 text-[11px] text-slate-300 font-mono resize-none focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Widget 3: Subagentlar Ish Maydoni */}
          <div className="p-3 rounded-xl bg-slate-900/80 border border-white/10 space-y-2">
            <div className="text-xs font-semibold text-slate-200 flex items-center space-x-1.5">
              <Box className="w-3.5 h-3.5 text-cyan-400" />
              <span>{lang === 'uz' ? 'Subagentlar Porti' : 'Subagents Ports'}</span>
            </div>
            <div className="space-y-1 text-[10px] font-mono text-slate-400">
              <div className="flex justify-between p-1 rounded bg-slate-950/60">
                <span>scout (interact_web)</span>
                <span className="text-emerald-400">FAOL</span>
              </div>
              <div className="flex justify-between p-1 rounded bg-slate-950/60">
                <span>sculptor (blender)</span>
                <span className="text-emerald-400">FAOL</span>
              </div>
              <div className="flex justify-between p-1 rounded bg-slate-950/60">
                <span>inspector (audit)</span>
                <span className="text-emerald-400">FAOL</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
