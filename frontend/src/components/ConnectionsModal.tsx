'use client';

import React, { useState, useEffect } from 'react';
import { 
  Radio, 
  X, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw, 
  Terminal, 
  ExternalLink,
  ShieldCheck,
  Check
} from 'lucide-react';

interface ConnectionTool {
  id: string;
  name: string;
  category: string;
  status: 'ready' | 'missing';
  path: string;
  is_ready: boolean;
}

interface ConnectionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  lang: 'uz' | 'en';
}

export const ConnectionsModal: React.FC<ConnectionsModalProps> = ({ isOpen, onClose, lang }) => {
  const [tools, setTools] = useState<ConnectionTool[]>([]);
  const [loading, setLoading] = useState(false);
  const [checkingId, setCheckingId] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadConnections();
    }
  }, [isOpen]);

  const loadConnections = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/connections');
      if (res.ok) {
        const data = await res.json();
        setTools(data);
      }
    } catch (e) {
      console.error('Failed to load connections:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckTool = async (id: string) => {
    setCheckingId(id);
    try {
      const res = await fetch(`/api/connections/check/${id}`, { method: 'POST' });
      if (res.ok) {
        const updated = await res.json();
        setTools((prev) =>
          prev.map((t) =>
            t.id === id ? { ...t, status: updated.status, path: updated.path, is_ready: updated.is_ready } : t
          )
        );
      }
    } catch (e) {
      console.error('Failed to recheck tool:', e);
    } finally {
      setTimeout(() => setCheckingId(null), 400);
    }
  };

  if (!isOpen) return null;

  const readyCount = tools.filter((t) => t.is_ready).length;
  const missingCount = tools.filter((t) => !t.is_ready).length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4" onClick={onClose}>
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/70">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Radio className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-semibold text-white tracking-wide">
                  {lang === 'uz' ? 'CLI Vositalari Ulanish Holati' : 'CLI Tools Connection Status'}
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] font-mono">
                  {readyCount} {lang === 'uz' ? 'faol' : 'ready'}
                </span>
                {missingCount > 0 && (
                  <span className="px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30 text-[10px] font-mono">
                    {missingCount} {lang === 'uz' ? 'topilmadi' : 'missing'}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400">
                {lang === 'uz' ? 'Claude, GitHub, Figma, Python, Node va media dvigatellari holati' : 'Engine status for Claude, GitHub, Figma, runtimes, and media CLIs'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={loadConnections}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              title="Qayta yuklash"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-400' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="w-7 h-7 rounded-lg hover:bg-slate-800 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Body list */}
        <div className="flex-1 overflow-y-auto p-6 space-y-2.5">
          {tools.map((tool) => {
            const isReady = tool.is_ready;
            const isChecking = checkingId === tool.id;

            return (
              <div
                key={tool.id}
                className={`p-3.5 rounded-xl border transition-all flex items-center justify-between ${
                  isReady
                    ? 'bg-slate-950/70 border-slate-800/80 hover:border-slate-700'
                    : 'bg-rose-950/20 border-rose-500/40 hover:border-rose-500/60'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center border shrink-0 ${
                      isReady
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                        : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                    }`}
                  >
                    {isReady ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-rose-400" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-xs text-white">{tool.name}</span>
                      <span className="text-[10px] text-slate-500 font-mono">({tool.category})</span>
                    </div>
                    <p className="text-[11px] text-slate-400 font-mono mt-0.5 truncate max-w-sm">
                      {tool.path}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wide ${
                      isReady
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                    }`}
                  >
                    {isReady ? (lang === 'uz' ? 'Ulangan' : 'Connected') : (lang === 'uz' ? 'Ulanmagan' : 'Missing')}
                  </span>

                  <button
                    onClick={() => handleCheckTool(tool.id)}
                    disabled={isChecking}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1 transition-all ${
                      isReady
                        ? 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                        : 'bg-rose-600 hover:bg-rose-500 text-white shadow-sm'
                    }`}
                  >
                    <RefreshCw className={`w-3 h-3 ${isChecking ? 'animate-spin' : ''}`} />
                    <span>
                      {isReady
                        ? (lang === 'uz' ? 'Tekshirish' : 'Check')
                        : (lang === 'uz' ? 'Ulash / Tekshirish' : 'Connect / Check')}
                    </span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
