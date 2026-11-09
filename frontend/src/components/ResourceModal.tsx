'use client';

import React, { useState, useEffect } from 'react';
import { 
  Coins, 
  X, 
  Activity, 
  Clock, 
  Cpu, 
  AlertOctagon, 
  Check, 
  Sliders, 
  BarChart3,
  Flame,
  ArrowUpRight
} from 'lucide-react';

interface ResourceSummary {
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_duration_seconds: number;
  total_cost_usd: number;
  max_budget_usd: number;
  max_tokens: number;
  is_blocked: boolean;
  block_reason: string | null;
  by_agent: Record<string, { tokens: number; duration_seconds: number; cost_usd: number }>;
}

interface ResourceModalProps {
  isOpen: boolean;
  onClose: () => void;
  lang: 'uz' | 'en';
}

export const ResourceModal: React.FC<ResourceModalProps> = ({ isOpen, onClose, lang }) => {
  const [data, setData] = useState<ResourceSummary | null>(null);
  const [budgetLimit, setBudgetLimit] = useState('5.0');
  const [tokenLimit, setTokenLimit] = useState('200000');
  const [saving, setSaving] = useState(false);
  const [savedMsg, setSavedMsg] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadResources();
    }
  }, [isOpen]);

  const loadResources = async () => {
    try {
      const res = await fetch('/api/resources');
      if (res.ok) {
        const d = await res.json();
        setData(d);
        setBudgetLimit(d.max_budget_usd.toString());
        setTokenLimit(d.max_tokens.toString());
      }
    } catch (e) {
      console.error('Failed to load resources:', e);
    }
  };

  const handleSaveLimits = async () => {
    setSaving(true);
    try {
      const res = await fetch('/api/resources/limit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          max_budget_usd: parseFloat(budgetLimit) || 5.0,
          max_tokens: parseInt(tokenLimit, 10) || 200000,
        }),
      });
      if (res.ok) {
        const updated = await res.json();
        setData(updated);
        setSavedMsg(true);
        setTimeout(() => setSavedMsg(false), 2500);
      }
    } catch (e) {
      console.error('Failed to update limits:', e);
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  const totalCost = data?.total_cost_usd || 0;
  const maxBudget = data?.max_budget_usd || 5.0;
  const budgetPercent = Math.min(100, Math.round((totalCost / maxBudget) * 100));

  const totalTokens = data?.total_tokens || 0;
  const maxTokens = data?.max_tokens || 200000;
  const tokenPercent = Math.min(100, Math.round((totalTokens / maxTokens) * 100));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/70">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Coins className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white tracking-wide">
                {lang === 'uz' ? 'Resurs va Byudjet Nazorati' : 'Resource & Budget Monitor'}
              </h2>
              <p className="text-xs text-slate-400">
                {lang === 'uz' ? 'Token sarfi, sarflangan pul va avtomatik to\'xtatish chegaralari' : 'Token usage, cost ledger, and auto-halt thresholds'}
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

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {/* LIMIT WARNING BANNER */}
          {data?.is_blocked && (
            <div className="p-3.5 rounded-xl bg-red-950/60 border border-red-500 text-red-200 text-xs flex items-start space-x-3 animate-pulse">
              <AlertOctagon className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-red-300">
                  {lang === 'uz' ? 'LIMITGA YETILDI — AGENT TO\'XTATILGAN' : 'LIMIT REACHED — AGENT HALTED'}
                </p>
                <p className="text-[11px] text-red-300/80 mt-0.5">{data.block_reason}</p>
                <p className="text-[10px] text-red-400 mt-1">
                  Yangi vazifalar boshlanishi uchun quyida byudjet yoki token limitini oshiring.
                </p>
              </div>
            </div>
          )}

          {/* METRIC CARDS */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>{lang === 'uz' ? 'Sarflangan Pul' : 'Cost ($)'}</span>
                <Coins className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-xl font-bold font-mono text-emerald-400">
                ${(data?.total_cost_usd || 0).toFixed(4)}
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
                <div
                  className={`h-full ${budgetPercent > 90 ? 'bg-red-500' : 'bg-emerald-500'}`}
                  style={{ width: `${budgetPercent}%` }}
                />
              </div>
              <div className="text-[10px] text-slate-500 flex justify-between mt-1">
                <span>{budgetPercent}% limit</span>
                <span>Max: ${maxBudget.toFixed(2)}</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>{lang === 'uz' ? 'Jami Tokenlar' : 'Tokens'}</span>
                <Cpu className="w-4 h-4 text-blue-400" />
              </div>
              <div className="text-xl font-bold font-mono text-blue-400">
                {(data?.total_tokens || 0).toLocaleString()}
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
                <div
                  className={`h-full ${tokenPercent > 90 ? 'bg-red-500' : 'bg-blue-500'}`}
                  style={{ width: `${tokenPercent}%` }}
                />
              </div>
              <div className="text-[10px] text-slate-500 flex justify-between mt-1">
                <span>In: {data?.total_prompt_tokens || 0}</span>
                <span>Out: {data?.total_completion_tokens || 0}</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>{lang === 'uz' ? 'Ishlash Vaqti' : 'Runtime'}</span>
                <Clock className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-xl font-bold font-mono text-white">
                {Math.floor((data?.total_duration_seconds || 0) / 60)}m{' '}
                {Math.round((data?.total_duration_seconds || 0) % 60)}s
              </div>
              <p className="text-[10px] text-slate-500 mt-2">
                Jami subagentlar fon jarayonlari davomiyligi
              </p>
            </div>
          </div>

          {/* SUBAGENT BREAKDOWN */}
          <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800 space-y-3">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
              <BarChart3 className="w-3.5 h-3.5 text-blue-400" />
              <span>{lang === 'uz' ? 'Subagentlar Bo\'yicha Taqsimot' : 'Subagent Breakdown'}</span>
            </h3>

            {Object.keys(data?.by_agent || {}).length === 0 ? (
              <p className="text-xs text-slate-500 italic">Hozircha vazifa sarfi qayd etilmagan.</p>
            ) : (
              <div className="space-y-2">
                {Object.entries(data!.by_agent).map(([ag, stats]) => (
                  <div
                    key={ag}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-900 border border-slate-800/80 text-xs font-mono"
                  >
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-blue-400" />
                      <span className="font-bold text-white uppercase">{ag}</span>
                    </div>
                    <div className="flex items-center space-x-4 text-slate-400">
                      <span>{stats.tokens.toLocaleString()} tok</span>
                      <span>{stats.duration_seconds}s</span>
                      <span className="font-bold text-emerald-400">${stats.cost_usd.toFixed(4)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* LIMIT SETTING FORM */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                <Sliders className="w-3.5 h-3.5 text-indigo-400" />
                <span>{lang === 'uz' ? 'Cheklovlarni O\'rnatish (Limits)' : 'Configure Limits'}</span>
              </h3>
              {savedMsg && (
                <span className="text-xs text-emerald-400 flex items-center space-x-1 font-medium">
                  <Check className="w-3.5 h-3.5" />
                  <span>{lang === 'uz' ? 'Limitlar saqlandi!' : 'Limits saved!'}</span>
                </span>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">
                  {lang === 'uz' ? 'Byudjet Chegarasi ($)' : 'Budget Limit ($)'}
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={budgetLimit}
                  onChange={(e) => setBudgetLimit(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">
                  {lang === 'uz' ? 'Tokenlar Chegarasi' : 'Tokens Limit'}
                </label>
                <input
                  type="number"
                  step="10000"
                  value={tokenLimit}
                  onChange={(e) => setTokenLimit(e.target.value)}
                  className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
                />
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <button
                onClick={handleSaveLimits}
                disabled={saving}
                className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-sm transition-all"
              >
                <span>{lang === 'uz' ? 'Limitni Saqlash' : 'Save Limits'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
