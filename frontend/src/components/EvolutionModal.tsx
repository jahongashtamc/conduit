'use client';

import React, { useState, useEffect } from 'react';
import { 
  Search,
  Sparkles, 
  X, 
  Plus, 
  Play, 
  Check, 
  AlertTriangle, 
  BookOpen, 
  Layers, 
  Trash2, 
  Power, 
  Save,
  CheckCircle2,

  FileText
} from 'lucide-react';

interface Skill {
  id: string;
  name: string;
  description: string;
  prompt_template: string;
  target_subagents: string[];
  enabled: boolean;
  trigger_keywords: string[];
  source_task_id?: string;
  updated_at: string;
}

interface Lesson {
  id: string;
  task_id: string;
  title: string;
  summary: string;
  proposed_skill: Record<string, unknown>;
  status: 'suggested' | 'approved' | 'dismissed';
  created_at: string;
}

interface ToolCandidate {
  repo: string;
  name: string;
  author?: string;
  url?: string;
  source?: string;
  license?: string;
  license_status?: string;
  score?: number;
  verdict?: string;
  risk_factors?: string[];
}

interface ResearchReport {
  filename: string;
  topic: string;
  path: string;
  updated_at: string;
  size_bytes: number;
}

interface SkillTestResult {
  success?: boolean;
  verdict?: string;
  output?: string;
  error?: string;
  [key: string]: unknown;
}

interface EvolutionModalProps {
  isOpen: boolean;
  onClose: () => void;
  lang: 'uz' | 'en';
  /** true bo'lsa modal overlay emas, to'liq tab ko'rinishida render qilinadi */
  inline?: boolean;
}

export const EvolutionModal: React.FC<EvolutionModalProps> = ({ isOpen, onClose, lang, inline = false }) => {
  const [activeSubTab, setActiveSubTab] = useState<'skills' | 'memory' | 'lessons' | 'research'>('skills');
  const [researchReports, setResearchReports] = useState<ResearchReport[]>([]);
  const [toolCandidates, setToolCandidates] = useState<ToolCandidate[]>([]);
  const [selectedReport, setSelectedReport] = useState<ResearchReport & { content?: string } | null>(null);
  const [researchInput, setResearchInput] = useState('');
  const [searchingTools, setSearchingTools] = useState(false);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState<SkillTestResult | null>(null);
  const [testInput, setTestInput] = useState('');
  const [testingSkillId, setTestingSkillId] = useState<string | null>(null);

  // New Skill Form State
  const [showNewSkillForm, setShowNewSkillForm] = useState(false);
  const [skillName, setSkillName] = useState('');
  const [skillDesc, setSkillDesc] = useState('');
  const [skillPrompt, setSkillPrompt] = useState('');
  const [skillAgent, setSkillAgent] = useState('scout');
  const [skillKeywords, setSkillKeywords] = useState('');
  const [conflictWarning, setConflictWarning] = useState<string | null>(null);

  // Memory Files State
  const [activeMemoryFile, setActiveMemoryFile] = useState<'project' | 'decisions' | 'errors'>('project');
  const [memoryContent, setMemoryContent] = useState('');
  const [memorySavedMsg, setMemorySavedMsg] = useState(false);

  const loadMemoryBlock = async (name: string) => {
    try {
      const res = await fetch(`/api/memory/${name}`);
      if (res.ok) {
        const data = await res.json();
        setMemoryContent(data.content || '');
      }
    } catch (e) {
      console.error('Failed to load memory:', e);
    }
  };

  const loadReportContent = async (topic: string) => {
    try {
      const res = await fetch(`/api/research/${topic}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedReport(data);
      }
    } catch (e) {
      console.error('Failed to load report:', e);
    }
  };

  const loadResearchData = async () => {
    try {
      const repRes = await fetch('/api/research');
      if (repRes.ok) {
        const data = await repRes.json();
        setResearchReports(data.reports || []);
        if (data.reports?.length > 0 && !selectedReport) {
          loadReportContent(data.reports[0].topic);
        }
      }
      const candRes = await fetch('/api/tools/candidates');
      if (candRes.ok) {
        const data = await candRes.json();
        setToolCandidates(data.candidates || []);
      }
    } catch (e) {
      console.error('Error loading research data:', e);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeSubTab === 'skills') {
        const res = await fetch('/api/skills');
        if (res.ok) {
          const data = await res.json();
          setSkills(data);
        }
      } else if (activeSubTab === 'lessons') {
        const res = await fetch('/api/lessons');
        if (res.ok) {
          const data = await res.json();
          setLessons(data);
        }
      } else if (activeSubTab === 'memory') {
        loadMemoryBlock(activeMemoryFile);
      } else if (activeSubTab === 'research') {
        await loadResearchData();
      }
    } catch (e) {
      console.error('Error loading evolution data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- loadData birinchi await'dan oldin holatni belgilaydi; ma'lumot yuklash effekti uchun ataylab
      loadData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- loadData barqaror, tab almashganda yuklanadi
  }, [isOpen, activeSubTab]);

  // Modal ochilganda barcha yorliq hisoblari bir marta yuklanadi —
  // aks holda tablar 0 ko'rsatardi (lazy yuklash yorliqlarni soxta kichik qilardi).
  useEffect(() => {
    if (!isOpen) return;
    const loadCounts = async () => {
      try {
        const [rRes, lRes] = await Promise.all([fetch('/api/research'), fetch('/api/lessons')]);
        if (rRes.ok) {
          const rData = await rRes.json();
          setResearchReports(rData.reports || []);
        }
        if (lRes.ok) {
          const lData = await lRes.json();
          setLessons(Array.isArray(lData) ? lData : []);
        }
      } catch (e) {
        console.error('Error loading evolution tab counts:', e);
      }
    };
    loadCounts();
  }, [isOpen]);


  const handleSaveMemory = async () => {
    try {
      const res = await fetch(`/api/memory/${activeMemoryFile}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: memoryContent }),
      });
      if (res.ok) {
        setMemorySavedMsg(true);
        setTimeout(() => setMemorySavedMsg(false), 2500);
      }
    } catch (e) {
      console.error('Failed to save memory:', e);
    }
  };

  // Conflict Check while typing skill name or keywords
  useEffect(() => {
    // reset — prop o'zgarganda holatni darhol tozalash ataylab sinxron qilinadi
    if (!skillName.trim()) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- input tozalanishi darhol amalga oshishi kerak
      setConflictWarning(null);
      return;
    }
    const cleanName = skillName.trim().toLowerCase();
    const kws = skillKeywords.split(',').map((k) => k.trim().toLowerCase()).filter(Boolean);
    const existing = skills.find(
      (s) => s.name.toLowerCase() === cleanName || s.trigger_keywords.some((k) => kws.includes(k.toLowerCase()))
    );
    if (existing) {
      setConflictWarning(`DIQQAT: Ushbu nom yoki kalit so'zlar '${existing.name}' skilli bilan to'qnashmoqda!`);
    } else {
      setConflictWarning(null);
    }
  }, [skillName, skillKeywords, skills]);

  const handleCreateSkill = async (force: boolean = false) => {
    if (!skillName.trim() || !skillPrompt.trim()) return;
    try {
      const res = await fetch('/api/skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: skillName.trim(),
          description: skillDesc.trim() || skillName.trim(),
          prompt_template: skillPrompt.trim(),
          target_subagents: [skillAgent],
          trigger_keywords: skillKeywords.split(',').map((k) => k.trim()).filter(Boolean),
          force,
        }),
      });
      if (res.status === 409) {
        const err = await res.json();
        setConflictWarning(err.message || 'Ziddiyat aniqlandi!');
        return;
      }
      if (res.ok) {
        setSkillName('');
        setSkillDesc('');
        setSkillPrompt('');
        setSkillKeywords('');
        setShowNewSkillForm(false);
        setConflictWarning(null);
        loadData();
      }
    } catch (e) {
      console.error('Failed to create skill:', e);
    }
  };

  const handleToggleSkill = async (id: string, currentEnabled: boolean) => {
    try {
      await fetch(`/api/skills/${id}/toggle`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !currentEnabled }),
      });
      setSkills((prev) =>
        prev.map((s) => (s.id === id ? { ...s, enabled: !currentEnabled } : s))
      );
    } catch (e) {
      console.error('Failed to toggle skill:', e);
    }
  };

  const handleDeleteSkill = async (id: string) => {
    try {
      await fetch(`/api/skills/${id}`, { method: 'DELETE' });
      setSkills((prev) => prev.filter((s) => s.id !== id));
    } catch (e) {
      console.error('Failed to delete skill:', e);
    }
  };

  const handleTestSkill = async (skill: Skill) => {
    setTestingSkillId(skill.id);
    setTestResult(null);
    try {
      const res = await fetch(`/api/skills/${skill.id}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ test_prompt: testInput || 'Sinov uchun namuna parametr' }),
      });
      if (res.ok) {
        const data = await res.json();
        setTestResult(data);
      }
    } catch (e) {
      console.error('Failed to test skill:', e);
    }
  };

  const handleApproveLesson = async (id: string) => {
    try {
      await fetch(`/api/lessons/${id}/approve`, { method: 'POST' });
      loadData();
    } catch (e) {
      console.error('Failed to approve lesson:', e);
    }
  };




  const handleRunDeepSearch = async () => {
    if (!researchInput.trim()) return;
    setSearchingTools(true);
    try {
      const res = await fetch('/api/tools/deepsearch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: researchInput.trim() })
      });
      if (res.ok) {
        await loadResearchData();
        setResearchInput('');
      }
    } catch (e) {
      console.error('Failed to run deepsearch:', e);
    } finally {
      setSearchingTools(false);
    }
  };

  const handleDismissLesson = async (id: string) => {
    try {
      await fetch(`/api/lessons/${id}/dismiss`, { method: 'POST' });
      loadData();
    } catch (e) {
      console.error('Failed to dismiss lesson:', e);
    }
  };

  if (!isOpen) return null;

  const shell = inline
    ? "relative h-full w-full flex items-center justify-center bg-slate-950 p-4"
    : "fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-4";
  const panel = inline
    ? "bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-5xl h-full flex flex-col shadow-2xl overflow-hidden"
    : "bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-4xl max-h-[88vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150";

  return (
    <div className={shell} onClick={inline ? undefined : onClose}>
      <div className={panel} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-slate-500/10 border border-slate-500/30 flex items-center justify-center text-slate-400">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white tracking-wide">
                {lang === 'uz' ? 'Evolyutsiya Markazi' : 'Evolution Center'}
              </h2>
              <p className="text-xs text-slate-400">
                {lang === 'uz' ? 'Skillar, xotira bloklari va saboqlar boshqaruvi' : 'Manage skills, memory blocks, and lessons'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-lg hover:bg-slate-800 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Subtabs Navigation */}
        <div className="flex items-center space-x-2 px-6 pt-3 pb-2 border-b border-slate-800/80 bg-slate-900/50">
          <button
            onClick={() => setActiveSubTab('skills')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center space-x-2 transition-all ${
              activeSubTab === 'skills'
                ? 'nav-active text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>{lang === 'uz' ? 'Skillar' : 'Skills'} ({skills.length})</span>
          </button>
          <button
            onClick={() => setActiveSubTab('research')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center space-x-2 transition-all ${
              activeSubTab === 'research'
                ? 'nav-active text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <Search className="w-3.5 h-3.5" />
            <span>{lang === 'uz' ? 'Tadqiqot va Asboblar' : 'Research & Tools'} ({researchReports.length})</span>
          </button>
          <button
            onClick={() => setActiveSubTab('memory')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center space-x-2 transition-all ${
              activeSubTab === 'memory'
                ? 'nav-active text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>{lang === 'uz' ? 'Xotira Bloklari' : 'Memory Blocks'}</span>
          </button>
          <button
            onClick={() => setActiveSubTab('lessons')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center space-x-2 transition-all ${
              activeSubTab === 'lessons'
                ? 'nav-active text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>{lang === 'uz' ? 'Saboqlar' : 'Lessons'} ({lessons.filter((l) => l.status === 'suggested').length})</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loading && (
            <p className="text-[11px] text-slate-500 font-mono animate-pulse">
              {lang === 'uz' ? 'Yuklanmoqda...' : 'Loading...'}
            </p>
          )}
          {/* TAB 1: SKILLAR */}
          {activeSubTab === 'skills' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    {lang === 'uz' ? 'Faol Skillar Ro\'yxati' : 'Active Skills Catalog'}
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    {lang === 'uz'
                      ? 'Subagentlar ishida qayta ishlatiladigan ko\'rsatmalar'
                      : 'Reusable skills bound to subagents'}
                  </p>
                </div>
                <button
                  onClick={() => setShowNewSkillForm(!showNewSkillForm)}
                  className="px-3 py-1.5 rounded-lg btn-accent text-white text-xs font-semibold flex items-center space-x-1.5 transition-all"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>{lang === 'uz' ? 'Yangi Skill Qo\'shish' : 'New Skill'}</span>
                </button>
              </div>

              {/* Skill test prompt: handleTestSkill shu matnni yuboradi */}
              <input
                value={testInput}
                onChange={(e) => setTestInput(e.target.value)}
                placeholder={lang === 'uz' ? 'Test prompt (bo\'sh bo\'lsa namuna parametr yuboriladi)' : 'Test prompt (empty sends a sample parameter)'}
                className="w-full px-3 py-2 rounded-lg bg-slate-800/80 border border-white/10 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-slate-500"
              />

              {/* New Skill Form Drawer */}
              {showNewSkillForm && (
                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-500/30 space-y-3">
                  <h4 className="text-xs font-bold text-slate-400 flex items-center space-x-2">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>{lang === 'uz' ? 'Yangi Skill Parametrlari' : 'Skill Configuration'}</span>
                  </h4>

                  {conflictWarning && (
                    <div className="p-2.5 rounded-lg bg-amber-950/60 border border-amber-500/40 text-amber-300 text-xs flex items-center space-x-2">
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                      <span>{conflictWarning}</span>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] text-slate-400 block mb-1">
                        {lang === 'uz' ? 'Skill Nomi' : 'Skill Name'}
                      </label>
                      <input
                        type="text"
                        value={skillName}
                        onChange={(e) => setSkillName(e.target.value)}
                        placeholder="masalan: API xatoliklarini tekshirish"
                        className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-slate-500"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-400 block mb-1">
                        {lang === 'uz' ? 'Biriktiriladigan Subagent' : 'Target Subagent'}
                      </label>
                      <select
                        value={skillAgent}
                        onChange={(e) => setSkillAgent(e.target.value)}
                        className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-slate-500"
                      >
                        <option value="scout">Scout (Veb & Tahlil)</option>
                        <option value="sculptor">Sculptor (3D & Blender)</option>
                        <option value="inspector">Inspector (Audit & Kod)</option>
                        <option value="designer">Designer (Figma & UI)</option>
                        <option value="animator">Animator (Video & Motion)</option>
                        <option value="*">Barcha Subagentlar (*)</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="text-[11px] text-slate-400 block mb-1">
                      {lang === 'uz' ? 'Kalit so\'zlar (vergul bilan ajrating)' : 'Trigger Keywords'}
                    </label>
                    <input
                      type="text"
                      value={skillKeywords}
                      onChange={(e) => setSkillKeywords(e.target.value)}
                      placeholder="masalan: api, xato, debug, endpoint"
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-slate-500"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] text-slate-400 block mb-1">
                      {lang === 'uz' ? 'Ko\'rsatma va qoidalar (Prompt Template)' : 'Prompt Instructions'}
                    </label>
                    <textarea
                      rows={3}
                      value={skillPrompt}
                      onChange={(e) => setSkillPrompt(e.target.value)}
                      placeholder="Agent bu skill ishga tushganda aynan qanday qadamlarni bajarishi kerak..."
                      className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-slate-500 font-mono resize-none"
                    />
                  </div>

                  <div className="flex items-center justify-end space-x-2 pt-2">
                    <button
                      onClick={() => setShowNewSkillForm(false)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300"
                    >
                      {lang === 'uz' ? 'Bekor qilish' : 'Cancel'}
                    </button>
                    {conflictWarning && (
                      <button
                        onClick={() => handleCreateSkill(true)}
                        className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold"
                      >
                        {lang === 'uz' ? 'Ziddiyatga qaramay saqlash' : 'Force Save'}
                      </button>
                    )}
                    <button
                      onClick={() => handleCreateSkill(false)}
                      className="px-3 py-1.5 rounded-lg btn-accent text-white text-xs font-semibold"
                    >
                      {lang === 'uz' ? 'Skillni Saqlash' : 'Save Skill'}
                    </button>
                  </div>
                </div>
              )}

              {/* Skills List */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {skills.map((skill) => (
                  <div
                    key={skill.id}
                    className={`p-3.5 rounded-xl border transition-all ${
                      skill.enabled
                        ? 'bg-slate-950/70 border-slate-800 hover:border-slate-700'
                        : 'bg-slate-950/30 border-slate-900 opacity-60'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-semibold text-xs text-white">{skill.name}</span>
                          <span className="px-1.5 py-1 rounded bg-slate-500/10 text-slate-400 border border-slate-500/20 text-[11px] font-mono">
                            {skill.target_subagents.join(', ')}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                          {skill.description}
                        </p>
                      </div>
                      <div className="flex items-center space-x-1 shrink-0">
                        <button
                          onClick={() => handleToggleSkill(skill.id, skill.enabled)}
                          title={skill.enabled ? 'O\'chirish' : 'Yoqish'}
                          className={`p-1.5.5 rounded-lg transition-colors ${
                            skill.enabled
                              ? 'text-emerald-400 hover:bg-emerald-950/40'
                              : 'text-slate-600 hover:bg-slate-800'
                          }`}
                        >
                          <Power className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDeleteSkill(skill.id)}
                          title="O'chirish"
                          className="p-1.5.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-950/30 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
                      <div className="flex items-center space-x-1 text-slate-500">
                        <span>Keywords:</span>
                        <span className="text-slate-400 font-mono">
                          {skill.trigger_keywords.length > 0 ? skill.trigger_keywords.join(', ') : 'avto'}
                        </span>
                      </div>
                      <button
                        onClick={() => handleTestSkill(skill)}
                        className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-300 font-medium flex items-center space-x-1 transition-colors"
                      >
                        <Play className="w-2.5 h-2.5" />
                        <span>{lang === 'uz' ? 'Sinab ko\'r' : 'Test'}</span>
                      </button>
                    </div>

                    {/* Test result display */}
                    {testingSkillId === skill.id && testResult && (
                      <div className="mt-2.5 p-2 rounded-lg bg-slate-950/40 border border-slate-500/30 text-[11px] space-y-1 animate-in fade-in">
                        <div className="flex items-center space-x-1.5 text-slate-300 font-semibold">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Sinov natijasi: {String(testResult.status ?? '-')} ({String(testResult.tested_with_agent ?? '-')})</span>
                        </div>
                        <p className="text-slate-300 font-mono text-[11px]">{String(testResult.result_preview ?? '')}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 1.5: TADQIQOT VA ASBOBLAR */}
          {activeSubTab === 'research' && (
            <div className="space-y-4">
              {/* DeepSearch formasi */}
              <div className="p-4 rounded-xl bg-slate-900/70 border border-white/10 space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  {lang === 'uz' ? 'DeepSearch — Asbob Izlash' : 'DeepSearch — Tool Research'}
                </h3>
                <p className="text-[11px] text-slate-400">
                  {lang === 'uz'
                    ? 'Mavzu bo\'yicha GitHub/npm/PyPI dan nomzod asboblar topiladi, DeepX baholaydi va hisobot yaratadi.'
                    : 'Finds candidate tools from GitHub/npm/PyPI, evaluates them via DeepX and generates a report.'}
                </p>
                <div className="flex space-x-2">
                  <input
                    value={researchInput}
                    onChange={(e) => setResearchInput(e.target.value)}
                    placeholder={lang === 'uz' ? 'Mavzu: masalan, blender 3d render automation' : 'Topic: e.g. blender 3d render automation'}
                    className="flex-1 px-3 py-2 rounded-lg bg-slate-800/80 border border-white/10 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-slate-500"
                  />
                  <button
                    onClick={handleRunDeepSearch}
                    disabled={searchingTools || !researchInput.trim()}
                    className="px-4 py-2 rounded-lg btn-accent disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-semibold flex items-center space-x-1.5 transition-all"
                  >
                    <Search className="w-3.5 h-3.5" />
                    <span>{searchingTools ? (lang === 'uz' ? 'Izlanmoqda...' : 'Searching...') : (lang === 'uz' ? 'Ishga Tushirish' : 'Run DeepSearch')}</span>
                  </button>
                </div>
              </div>

              {/* Baholangan nomzodlar */}
              {toolCandidates.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    {lang === 'uz' ? `Baholangan Nomzodlar (${toolCandidates.length})` : `Evaluated Candidates (${toolCandidates.length})`}
                  </h3>
                  {toolCandidates.slice(0, 12).map((c, i) => (
                    <div key={`${c.repo}-${i}`} className="p-3 rounded-lg bg-slate-900/60 border border-white/[0.06] flex items-start justify-between space-x-3">
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-white truncate">{c.name}</p>
                        <p className="text-[11px] text-slate-400 font-mono truncate">{c.repo}{c.license ? ` · ${c.license}` : ''}</p>
                        {Array.isArray(c.risk_factors) && c.risk_factors.length > 0 && (
                          <p className="text-[10px] text-amber-400/80 mt-0.5 truncate">⚠ {String(c.risk_factors[0])}</p>
                        )}
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold shrink-0 ${
                        c.verdict === 'APPROVED' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                        : c.verdict === 'REJECTED' ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                        : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      }`}>
                        {c.score}/100
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Hisobotlar */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  {lang === 'uz' ? `Tadqiqot Hisobotlari (${researchReports.length})` : `Research Reports (${researchReports.length})`}
                </h3>
                {researchReports.length === 0 && (
                  <p className="text-[11px] text-slate-500">
                    {lang === 'uz' ? 'Hozircha hisobot yo\'q — yuqoridan DeepSearch ishga tushiring.' : 'No reports yet — run DeepSearch above.'}
                  </p>
                )}
                {researchReports.map((r) => (
                  <button
                    key={r.filename}
                    onClick={() => loadReportContent(r.topic)}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      selectedReport?.topic === r.topic
                        ? 'bg-slate-950/60 border-slate-500/50'
                        : 'bg-slate-900/60 border-white/[0.06] hover:border-slate-500/40'
                    }`}
                  >
                    <p className="text-xs font-semibold text-white">{r.topic}</p>
                    <p className="text-[10px] text-slate-500 font-mono">{r.updated_at} · {Math.round((r.size_bytes || 0) / 1024)} KB</p>
                  </button>
                ))}
              </div>

              {/* Tanlangan hisobot mazmuni */}
              {selectedReport?.content && (
                <pre className="p-4 rounded-xl bg-slate-950/80 border border-white/10 text-[11px] text-slate-300 whitespace-pre-wrap font-mono max-h-96 overflow-y-auto">
                  {selectedReport.content}
                </pre>
              )}
            </div>
          )}

          {/* TAB 2: XOTIRA BLOKLARI */}
          {activeSubTab === 'memory' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    {lang === 'uz' ? 'Yurak Xotirasi Fayllari' : 'Heart Memory Blocks'}
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    memory/ papkasidagi project.md, decisions.md, errors.md bloklari
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  {memorySavedMsg && (
                    <span className="text-xs text-emerald-400 flex items-center space-x-1 font-medium">
                      <Check className="w-3.5 h-3.5" />
                      <span>{lang === 'uz' ? 'Saqlandi!' : 'Saved!'}</span>
                    </span>
                  )}
                  <button
                    onClick={handleSaveMemory}
                    className="px-3 py-1.5 rounded-lg btn-accent text-white text-xs font-semibold flex items-center space-x-1.5 transition-colors"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>{lang === 'uz' ? 'Saqlash' : 'Save'}</span>
                  </button>
                </div>
              </div>

              {/* Memory file selector tabs */}
              <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                {(['project', 'decisions', 'errors'] as const).map((fname) => (
                  <button
                    key={fname}
                    onClick={() => {
                      setActiveMemoryFile(fname);
                      loadMemoryBlock(fname);
                    }}
                    className={`px-3 py-1 rounded-md text-xs font-mono transition-colors flex items-center space-x-1.5 ${
                      activeMemoryFile === fname
                        ? 'bg-slate-800 text-slate-400 font-bold border border-slate-700'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <FileText className="w-3 h-3" />
                    <span>{fname}.md</span>
                  </button>
                ))}
              </div>

              {/* Memory editor textarea */}
              <textarea
                rows={14}
                value={memoryContent}
                onChange={(e) => setMemoryContent(e.target.value)}
                className="w-full p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 font-mono focus:outline-none focus:border-slate-500/80 resize-none leading-relaxed"
                placeholder="Xotira blokining mazmuni..."
              />
            </div>
          )}

          {/* TAB 3: SABOQLAR */}
          {activeSubTab === 'lessons' && (
            <div className="space-y-4">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  {lang === 'uz' ? 'Muvaffaqiyatli Vazifalardan Olingan Saboqlar' : 'Task Lessons & Auto Evolution'}
                </h3>
                <p className="text-[11px] text-slate-400">
                  Vazifa PASS bo&apos;lgach bosh agent tomonidan taklif qilingan tajribalar
                </p>
              </div>

              {lessons.length === 0 ? (
                <div className="p-8 text-center rounded-xl bg-slate-950/40 border border-slate-800 text-slate-500 text-xs">
                  {lang === 'uz' ? 'Hozircha saboqlar mavjud emas. Vazifalar yakunlangach bu yerda taklif paydo bo\'ladi.' : 'No lessons recorded yet.'}
                </div>
              ) : (
                <div className="space-y-3">
                  {lessons.map((lesson) => (
                    <div
                      key={lesson.id}
                      className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2.5"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold text-xs text-white">{lesson.title}</span>
                            <span
                              className={`px-1.5 py-1 rounded text-[11px] font-mono uppercase ${
                                lesson.status === 'approved'
                                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                                  : lesson.status === 'dismissed'
                                  ? 'bg-slate-800 text-slate-500'
                                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                              }`}
                            >
                              {lesson.status}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-1">{lesson.summary}</p>
                        </div>
                        {lesson.status === 'suggested' && (
                          <div className="flex items-center space-x-2 shrink-0">
                            <button
                              onClick={() => handleDismissLesson(lesson.id)}
                              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 text-xs"
                            >
                              {lang === 'uz' ? 'Rad etish' : 'Dismiss'}
                            </button>
                            <button
                              onClick={() => handleApproveLesson(lesson.id)}
                              className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-sm"
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>{lang === 'uz' ? 'Skill qilib saqlash' : 'Save as Skill'}</span>
                            </button>
                          </div>
                        )}
                      </div>

                      {lesson.proposed_skill && lesson.proposed_skill.name && (
                        <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 text-[11px] text-slate-300 font-mono">
                          <span className="text-slate-400 font-bold">Taklif qilingan skill:</span> {String(lesson.proposed_skill.name)} (Subagent: {Array.isArray(lesson.proposed_skill.target_subagents) ? lesson.proposed_skill.target_subagents.join(', ') : 'scout'})
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
