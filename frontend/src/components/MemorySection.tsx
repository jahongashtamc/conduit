'use client';

import React, { useState, useEffect } from 'react';
import { Database, Edit3, Save, CheckCircle, RefreshCw, BookOpen, GitCommit, AlertTriangle } from 'lucide-react';
import { Language } from '@/lib/translations';

interface MemorySectionProps {
  lang: Language;
}

export const MemorySection: React.FC<MemorySectionProps> = ({ lang }) => {
  const [activeTab, setActiveTab] = useState<'project' | 'decisions' | 'errors'>('project');
  const [content, setContent] = useState<Record<string, string>>({
    project: '',
    decisions: '',
    errors: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const fetchMemory = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/memory');
      if (res.ok) {
        const data = await res.json();
        setContent(data);
      }
    } catch (err) {
      console.error('Failed to load memory:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMemory();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      const res = await fetch(`/api/memory/${activeTab}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content[activeTab] }),
      });
      if (res.ok) {
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 2500);
      }
    } catch (err) {
      console.error('Failed to save memory block:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const tabs = [
    { id: 'project', label: lang === 'uz' ? 'project.md (Kontekst)' : 'project.md (Context)', icon: BookOpen },
    { id: 'decisions', label: lang === 'uz' ? 'decisions.md (Qarorlar)' : 'decisions.md (Decisions)', icon: GitCommit },
    { id: 'errors', label: lang === 'uz' ? 'errors.md (Xatolar & Saboqlar)' : 'errors.md (Errors & Lessons)', icon: AlertTriangle },
  ];

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 mb-6 backdrop-blur-md shadow-lg">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 mb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Database className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              {lang === 'uz' ? 'Uzoq Muddatli Xotira (memory/)' : 'Long-Term Memory (memory/)'}
            </h3>
            <p className="text-[11px] text-slate-400">
              {lang === 'uz'
                ? 'Oddiy fayl bloklari. Faqat yurak yozadi, inson tahrirlashi mumkin.'
                : 'Transparent file blocks. Written by Heart, editable by user.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchMemory}
            disabled={isLoading}
            className="p-1.5 text-xs rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center gap-1 transition"
            title="Yangilash"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-3 py-1 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-1.5 shadow transition disabled:opacity-50"
          >
            {saveSuccess ? (
              <>
                <CheckCircle className="w-3.5 h-3.5 text-white" />
                <span>{lang === 'uz' ? 'Saqlandi!' : 'Saved!'}</span>
              </>
            ) : isSaving ? (
              <span>{lang === 'uz' ? 'Saqlanmoqda...' : 'Saving...'}</span>
            ) : (
              <>
                <Save className="w-3.5 h-3.5" />
                <span>{lang === 'uz' ? 'Saqlash' : 'Save'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 mb-3 overflow-x-auto pb-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition shrink-0 border ${
                isActive
                  ? 'bg-slate-800 text-emerald-400 border-emerald-500/40 shadow-sm'
                  : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Editor Textarea */}
      <div className="relative">
        <textarea
          value={content[activeTab] || ''}
          onChange={(e) => setContent({ ...content, [activeTab]: e.target.value })}
          rows={7}
          className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500/50 resize-y leading-relaxed"
          placeholder={lang === 'uz' ? 'Xotira bloki bo\'sh...' : 'Memory block empty...'}
        />
        <div className="absolute top-2 right-2 flex items-center gap-1 text-[10px] text-slate-500 bg-slate-900/80 px-2 py-0.5 rounded border border-slate-800">
          <Edit3 className="w-3 h-3" />
          <span>Tahrirlash rejimi</span>
        </div>
      </div>
    </div>
  );
};
