'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Sparkles,
  Film,
  Video,
  Layers,
  Palette,
  Plus,
  Check,
  X,
  AlertTriangle,
  Loader2,
  FolderOpen,
  FileCode,
  Activity,
  ToggleLeft,
  ToggleRight,
  ExternalLink,
} from 'lucide-react';
import { Language } from '@/lib/translations';

interface AppItem {
  id: string;
  name: string;
  category: string;
  status: 'ready' | 'not installed' | 'running';
  status_badge?: string; // "Faol" | "O'rnatilmagan" | "Keyinroq"
  enabled?: boolean;
  is_installed?: boolean;
  is_running?: boolean;
  icon: string;
  executable?: string;
  exe_path?: string;
  run_template?: string;
  extension?: string;
  supported_formats?: string[];
}

interface AppsTabProps {
  lang: Language;
}

const getAppIcon = (id: string) => {
  switch (id.toLowerCase()) {
    case 'blender':
      return Box;
    case 'after_effects':
      return Sparkles;
    case 'davinci':
      return Film;
    case 'premiere':
      return Video;
    case 'maya':
      return Layers;
    case 'figma':
      return Palette;
    default:
      return Box;
  }
};

export const AppsTab: React.FC<AppsTabProps> = ({ lang }) => {
  const [apps, setApps] = useState<AppItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add App Modal
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [name, setName] = useState('');
  const [exePath, setExePath] = useState('');
  const [runTemplate, setRunTemplate] = useState('');
  const [extension, setExtension] = useState('');
  const [category, setCategory] = useState('Creative');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchApps = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/apps');
      if (!res.ok) throw new Error('Ilovalarni yuklashda xatolik yuz berdi');
      const data = await res.json();
      if (Array.isArray(data)) {
        setApps(data);
      } else {
        setApps([]);
      }
    } catch (err: any) {
      setError(err.message || 'Xatolik');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApps();
  }, []);

  const handleToggle = async (appId: string, currentEnabled: boolean) => {
    const newEnabled = !currentEnabled;
    // Optimistic update
    setApps((prev) =>
      prev.map((a) =>
        a.id === appId
          ? {
              ...a,
              enabled: newEnabled,
              status_badge: !newEnabled ? 'Keyinroq' : a.is_installed ? 'Faol' : 'O\'rnatilmagan',
            }
          : a
      )
    );

    try {
      const res = await fetch(`/api/apps/${appId}/toggle`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: newEnabled }),
      });
      if (!res.ok) throw new Error('O\'zgartirib bo\'lmadi');
    } catch (err) {
      // Revert on failure
      fetchApps();
    }
  };

  const handleAddApp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !exePath.trim()) return;
    setIsSubmitting(true);
    try {
      const res = await fetch('/api/apps', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          exe_path: exePath.trim(),
          run_template: runTemplate.trim(),
          extension: extension.trim(),
          category: category.trim(),
        }),
      });
      if (!res.ok) throw new Error('Ilova qo\'shib bo\'lmadi');
      const data = await res.json();
      if (data.apps) setApps(data.apps);
      setIsAddOpen(false);
      setName('');
      setExePath('');
      setRunTemplate('');
      setExtension('');
    } catch (err: any) {
      alert(err.message || 'Xatolik');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-900/60 border border-white/[0.08] rounded-2xl overflow-hidden shadow-xl select-none">
      {/* Header */}
      <div className="p-4 border-b border-white/[0.08] flex items-center justify-between bg-slate-950/40">
        <div>
          <h2 className="text-sm font-bold text-white flex items-center space-x-2">
            <span>🎨</span>
            <span>{lang === 'uz' ? 'Studio Ilovalari Ekotizimi' : 'Studio Apps Ecosystem'}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            {lang === 'uz'
              ? 'Conduit agentlari boshqara oladigan dasturlar va ularning holati'
              : 'Applications integrated with Conduit subagents'}
          </p>
        </div>

        <button
          onClick={() => setIsAddOpen(true)}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md transition active:scale-95"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>{lang === 'uz' ? 'Ilova qo\'shish' : 'Add App'}</span>
        </button>
      </div>

      {/* Grid Content */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-5">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-500">
            <Loader2 className="w-7 h-7 animate-spin text-blue-500 mb-2" />
            <span className="text-xs">
              {lang === 'uz' ? 'Ilovalar ro\'yxati yuklanmoqda...' : 'Loading applications...'}
            </span>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-500">
            <AlertTriangle className="w-8 h-8 text-rose-500 mb-2" />
            <span className="text-xs text-rose-400 font-medium">
              {lang === 'uz' ? 'Ilovalarni yuklashda xatolik yuz berdi' : 'Failed to load applications'}
            </span>
            <button onClick={fetchApps} className="mt-3 text-xs text-blue-400 hover:underline">
              {lang === 'uz' ? 'Qayta urinish' : 'Retry'}
            </button>
          </div>
        ) : apps.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-slate-500 text-center px-4">
            <Box className="w-10 h-10 text-slate-600 mb-2 stroke-[1.5]" />
            <p className="text-xs font-semibold text-slate-300">
              {lang === 'uz'
                ? 'Ulangan ilovalar topilmadi. "Ilova qo\'shish" tugmasi orqali yangi dastur qo\'shing.'
                : 'No apps found. Click "Add App" to register a creative application.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {apps.map((app) => {
              const IconComponent = getAppIcon(app.id);
              const isEnabled = app.enabled !== false;
              const badgeText = app.status_badge || (isEnabled ? (app.is_installed ? 'Faol' : 'O\'rnatilmagan') : 'Keyinroq');

              const isFaol = badgeText === 'Faol';
              const isKeyinroq = badgeText === 'Keyinroq';
              const isNotInstalled = badgeText === "O'rnatilmagan";

              return (
                <div
                  key={app.id}
                  className={`rounded-2xl p-4 border transition-all duration-200 flex flex-col justify-between ${
                    isEnabled
                      ? isFaol
                        ? 'bg-slate-950/80 border-emerald-500/20 hover:border-emerald-500/40'
                        : 'bg-slate-950/80 border-white/[0.08] hover:border-white/20'
                      : 'bg-slate-950/40 border-white/[0.04] opacity-60'
                  }`}
                >
                  <div>
                    {/* Top Row: Icon + Name + Toggle */}
                    <div className="flex items-start justify-between gap-2 mb-2.5">
                      <div className="flex items-center space-x-2.5 min-w-0">
                        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${
                          isFaol
                            ? 'bg-blue-600/10 border-blue-500/30 text-blue-400'
                            : 'bg-slate-800/80 border-white/10 text-slate-400'
                        }`}>
                          <IconComponent className="w-4 h-4" />
                        </div>
                        <div className="min-w-0">
                          <h4 className="text-xs font-bold text-white truncate">{app.name}</h4>
                          <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">
                            {app.category}
                          </span>
                        </div>
                      </div>

                      {/* Enable/Disable Switch */}
                      <button
                        type="button"
                        onClick={() => handleToggle(app.id, isEnabled)}
                        className="text-slate-400 hover:text-white transition p-1"
                        title={isEnabled ? 'O\'chirish' : 'Yoqish'}
                      >
                        {isEnabled ? (
                          <ToggleRight className="w-6 h-6 text-blue-500" />
                        ) : (
                          <ToggleLeft className="w-6 h-6 text-slate-600" />
                        )}
                      </button>
                    </div>

                    {/* Exe Path (Small) */}
                    <div className="bg-slate-900/90 rounded-lg p-2 border border-white/[0.04] mb-3">
                      <div className="flex items-center space-x-1 text-[10px] text-slate-500 mb-0.5">
                        <FolderOpen className="w-3 h-3 text-slate-600" />
                        <span>Yo'l:</span>
                      </div>
                      <p className="font-mono text-[10px] text-slate-300 truncate" title={app.exe_path || app.executable}>
                        {app.exe_path || app.executable || '—'}
                      </p>
                    </div>

                    {/* Run template if available */}
                    {app.run_template && (
                      <div className="text-[10px] font-mono text-slate-500 truncate mb-1.5">
                        <span className="text-slate-600">shablon: </span>
                        <span>{app.run_template}</span>
                      </div>
                    )}

                    {/* Supported Formats */}
                    {app.supported_formats && app.supported_formats.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-2.5">
                        {app.supported_formats.slice(0, 4).map((fmt) => (
                          <span key={fmt} className="px-1.5 py-0.2 rounded bg-slate-900 border border-slate-800 text-[9px] font-mono text-cyan-400">
                            {fmt}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Bottom: Status Badge */}
                  <div className="flex items-center justify-between pt-2 border-t border-white/[0.04] text-[10px]">
                    <span className="text-slate-500">Holat:</span>
                    <span className={`px-2 py-0.5 rounded-full font-bold flex items-center space-x-1 ${
                      isFaol
                        ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                        : isKeyinroq
                        ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                        : 'bg-slate-800 text-slate-400 border border-white/5'
                    }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        isFaol ? 'bg-emerald-400' : isKeyinroq ? 'bg-amber-400' : 'bg-slate-500'
                      }`} />
                      <span>{badgeText}</span>
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ADD APP MODAL */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-slate-900 border border-white/[0.08] rounded-2xl p-5 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.08] mb-4">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Plus className="w-4 h-4 text-blue-400" />
                <span>{lang === 'uz' ? 'Yangi Studio Ilovasini Qo\'shish' : 'Add Creative Application'}</span>
              </h3>
              <button
                onClick={() => setIsAddOpen(false)}
                className="p-1 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddApp} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">
                  {lang === 'uz' ? 'Ilova nomi:' : 'Application Name:'}
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="masalan, Cinema 4D"
                  className="w-full bg-slate-950 border border-white/[0.08] rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">
                  {lang === 'uz' ? 'Ishga tushirish fayli (Exe Path):' : 'Executable Path:'}
                </label>
                <input
                  type="text"
                  required
                  value={exePath}
                  onChange={(e) => setExePath(e.target.value)}
                  placeholder="C:\Program Files\Maxon\CINEMA 4D.exe"
                  className="w-full bg-slate-950 border border-white/[0.08] rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 font-mono text-[11px]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">
                    {lang === 'uz' ? 'Kategoriya:' : 'Category:'}
                  </label>
                  <input
                    type="text"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    placeholder="3D & Animation"
                    className="w-full bg-slate-950 border border-white/[0.08] rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">
                    {lang === 'uz' ? 'Fayl kengaytmasi:' : 'File Extension:'}
                  </label>
                  <input
                    type="text"
                    value={extension}
                    onChange={(e) => setExtension(e.target.value)}
                    placeholder=".c4d"
                    className="w-full bg-slate-950 border border-white/[0.08] rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">
                  {lang === 'uz' ? 'CLI buyruq shabloni (ixtiyoriy):' : 'Command Template (Optional):'}
                </label>
                <input
                  type="text"
                  value={runTemplate}
                  onChange={(e) => setRunTemplate(e.target.value)}
                  placeholder="{exe} -nogui {script}"
                  className="w-full bg-slate-950 border border-white/[0.08] rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 font-mono text-[11px]"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAddOpen(false)}
                  className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition"
                >
                  {lang === 'uz' ? 'Bekor qilish' : 'Cancel'}
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !name.trim() || !exePath.trim()}
                  className="px-4 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white shadow-md transition active:scale-95 disabled:opacity-50"
                >
                  {isSubmitting ? 'Qo\'shilmoqda...' : lang === 'uz' ? 'Qo\'shish' : 'Add App'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
