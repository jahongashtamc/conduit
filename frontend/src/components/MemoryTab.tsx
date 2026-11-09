'use client';

import React, { useState, useEffect } from 'react';
import {
  Database,
  Search,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  AlertTriangle,
  Loader2,
  Clock,
  Sparkles,
} from 'lucide-react';
import { Language } from '@/lib/translations';

interface MemoryItem {
  id: number;
  key: string;
  value: string;
  source_task: string;
  created_at: string;
  updated_at: string;
}

interface MemoryTabProps {
  lang: Language;
}

export const MemoryTab: React.FC<MemoryTabProps> = ({ lang }) => {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  // Inline edit state
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editKey, setEditKey] = useState('');
  const [editValue, setEditValue] = useState('');

  // Delete modal state
  const [deleteTarget, setDeleteTarget] = useState<MemoryItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // New item modal state
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [newSource, setNewSource] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  // Fetch memories
  const fetchMemories = async (query = '') => {
    setLoading(true);
    setError(null);
    try {
      const url = query ? `/api/memory?search=${encodeURIComponent(query)}` : '/api/memory';
      const res = await fetch(url);
      if (!res.ok) throw new Error('Yuklashda xatolik yuz berdi');
      const data = await res.json();
      if (Array.isArray(data)) {
        setMemories(data);
      } else {
        setMemories([]);
      }
    } catch (err: any) {
      setError(err.message || 'Xatolik yuz berdi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories(search);
  }, [search]);

  // Handle Save Edit
  const handleSaveEdit = async (id: number) => {
    if (!editKey.trim() || !editValue.trim()) return;
    try {
      const res = await fetch(`/api/memory/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: editKey, value: editValue }),
      });
      if (!res.ok) throw new Error('Tahrirlashda xatolik');
      const updated = await res.json();
      setMemories((prev) => prev.map((m) => (m.id === id ? updated : m)));
      setEditingId(null);
    } catch (err: any) {
      alert(err.message || 'Xatolik');
    }
  };

  // Handle Delete
  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      const res = await fetch(`/api/memory/${deleteTarget.id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('O\'chirishda xatolik');
      setMemories((prev) => prev.filter((m) => m.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch (err: any) {
      alert(err.message || 'Xatolik');
    } finally {
      setIsDeleting(false);
    }
  };

  // Handle Add New
  const handleCreateMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim() || !newValue.trim()) return;
    setIsAdding(true);
    try {
      const res = await fetch('/api/memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          key: newKey,
          value: newValue,
          source_task: newSource || 'Foydalanuvchi xotirasi',
        }),
      });
      if (!res.ok) throw new Error('Qo\'shishda xatolik');
      const created = await res.json();
      setMemories((prev) => [created, ...prev]);
      setIsAddOpen(false);
      setNewKey('');
      setNewValue('');
      setNewSource('');
    } catch (err: any) {
      alert(err.message || 'Xatolik');
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-900/60 border border-white/[0.08] rounded-2xl overflow-hidden shadow-xl select-none">
      {/* Top Header & Search Bar */}
      <div className="p-4 border-b border-white/[0.08] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-slate-950/40">
        <div>
          <h2 className="text-sm font-bold text-white flex items-center space-x-2">
            <span>💾</span>
            <span>{lang === 'uz' ? 'Tizim Xotirasi (Neural Memory)' : 'System Memory Vault'}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            {lang === 'uz'
              ? 'Vazifalar, qabul qilingan arxitektura qarorlari va o\'rganilgan xotira yozuvlari'
              : 'Tasks, architectural decisions, and registered memory entries'}
          </p>
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          {/* Search Box */}
          <div className="relative flex-1 sm:w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={lang === 'uz' ? 'Xotiradan qidirish...' : 'Search memory...'}
              className="w-full bg-slate-950/80 border border-white/[0.06] rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Add New Memory Button */}
          <button
            onClick={() => setIsAddOpen(true)}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md transition active:scale-95 shrink-0"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>{lang === 'uz' ? 'Yozuv qo\'shish' : 'Add Entry'}</span>
          </button>
        </div>
      </div>

      {/* Table Content */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-500">
            <Loader2 className="w-7 h-7 animate-spin text-blue-500 mb-2" />
            <span className="text-xs">{lang === 'uz' ? 'Xotira yozuvlari yuklanmoqda...' : 'Loading memories...'}</span>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-500">
            <AlertTriangle className="w-8 h-8 text-rose-500 mb-2" />
            <span className="text-xs text-rose-400 font-medium">
              {lang === 'uz' ? 'Xotirani yuklashda xatolik yuz berdi' : 'Failed to load memory'}
            </span>
            <button
              onClick={() => fetchMemories(search)}
              className="mt-3 text-xs text-blue-400 hover:underline"
            >
              {lang === 'uz' ? 'Qayta urinish' : 'Retry'}
            </button>
          </div>
        ) : memories.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-slate-500 text-center px-4">
            <Database className="w-10 h-10 text-slate-600 mb-2 stroke-[1.5]" />
            <p className="text-xs font-semibold text-slate-300">
              {lang === 'uz'
                ? 'Xotira bo\'sh. Vazifalar bajarilgach shu yerda to\'planadi.'
                : 'Memory is empty. Executed tasks will accumulate knowledge here.'}
            </p>
            <p className="text-[11px] text-slate-500 mt-1 max-w-sm">
              {lang === 'uz'
                ? 'Bosh agent avtomatik ravishda muhim qarorlar va xatolarni xotiraga yozib boradi.'
                : 'The core agent automatically commits architectural decisions and lessons.'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-white/[0.04]">
            {/* Table Header */}
            <div className="grid grid-cols-12 gap-3 px-4 py-2.5 bg-slate-950/60 text-[11px] font-bold uppercase tracking-wider text-slate-400 sticky top-0 z-10 border-b border-white/[0.06]">
              <div className="col-span-3">{lang === 'uz' ? 'Kalit (Key)' : 'Key'}</div>
              <div className="col-span-5">{lang === 'uz' ? 'Qiymat (Value)' : 'Value'}</div>
              <div className="col-span-2">{lang === 'uz' ? 'Manba vazifa' : 'Source'}</div>
              <div className="col-span-1">{lang === 'uz' ? 'Sana' : 'Date'}</div>
              <div className="col-span-1 text-right">{lang === 'uz' ? 'Amallar' : 'Actions'}</div>
            </div>

            {/* Rows */}
            {memories.map((m) => {
              const isEditing = editingId === m.id;

              return (
                <div
                  key={m.id}
                  className="grid grid-cols-12 gap-3 px-4 py-3 items-center text-xs hover:bg-white/[0.02] transition"
                >
                  {/* Key */}
                  <div className="col-span-3">
                    {isEditing ? (
                      <input
                        type="text"
                        value={editKey}
                        onChange={(e) => setEditKey(e.target.value)}
                        className="w-full bg-slate-950 border border-blue-500 rounded px-2 py-1 text-xs text-white"
                      />
                    ) : (
                      <span className="font-semibold text-slate-200 flex items-center space-x-1.5">
                        <Sparkles className="w-3 h-3 text-blue-400 shrink-0" />
                        <span className="truncate">{m.key}</span>
                      </span>
                    )}
                  </div>

                  {/* Value */}
                  <div className="col-span-5">
                    {isEditing ? (
                      <textarea
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        rows={2}
                        className="w-full bg-slate-950 border border-blue-500 rounded px-2 py-1 text-xs text-white resize-none"
                      />
                    ) : (
                      <p className="text-slate-300 leading-relaxed font-mono text-[11px] line-clamp-2">
                        {m.value}
                      </p>
                    )}
                  </div>

                  {/* Source */}
                  <div className="col-span-2 text-slate-400 text-[11px] truncate">
                    <span className="px-2 py-0.5 rounded bg-slate-800/80 border border-white/5 font-mono">
                      {m.source_task || '—'}
                    </span>
                  </div>

                  {/* Date */}
                  <div className="col-span-1 text-slate-500 text-[10px] font-mono">
                    {m.updated_at ? m.updated_at.substring(0, 10) : '—'}
                  </div>

                  {/* Actions */}
                  <div className="col-span-1 flex items-center justify-end space-x-1.5">
                    {isEditing ? (
                      <>
                        <button
                          onClick={() => handleSaveEdit(m.id)}
                          className="p-1 hover:bg-emerald-500/20 text-emerald-400 rounded transition"
                          title="Saqlash"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          className="p-1 hover:bg-slate-800 text-slate-400 rounded transition"
                          title="Bekor qilish"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() => {
                            setEditingId(m.id);
                            setEditKey(m.key);
                            setEditValue(m.value);
                          }}
                          className="p-1 hover:bg-blue-500/20 text-slate-400 hover:text-blue-300 rounded transition"
                          title="Tahrirlash"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setDeleteTarget(m)}
                          className="p-1 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 rounded transition"
                          title="O'chirish"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* CONFIRM DELETE MODAL */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-slate-900 border border-rose-500/30 rounded-2xl p-5 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center space-x-3 text-rose-400 mb-3">
              <AlertTriangle className="w-6 h-6" />
              <h3 className="text-sm font-bold text-white">
                {lang === 'uz' ? 'Xotira yozuvini o\'chirish' : 'Delete Memory Entry'}
              </h3>
            </div>
            <p className="text-xs text-slate-300 mb-4">
              {lang === 'uz' ? (
                <>
                  Haqiqatan ham <strong className="text-white">"{deleteTarget.key}"</strong> xotira yozuvini o'chirmoqchimisiz? Bu amalni ortga qaytarib bo'lmaydi.
                </>
              ) : (
                `Are you sure you want to delete "${deleteTarget.key}"?`
              )}
            </p>
            <div className="flex items-center justify-end space-x-2">
              <button
                onClick={() => setDeleteTarget(null)}
                className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition"
              >
                {lang === 'uz' ? 'Bekor qilish' : 'Cancel'}
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                className="px-4 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-xs font-semibold text-white shadow-md transition active:scale-95 disabled:opacity-50"
              >
                {isDeleting ? 'O\'chirilmoqda...' : lang === 'uz' ? 'O\'chirish' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ADD NEW MEMORY MODAL */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-slate-900 border border-white/[0.08] rounded-2xl p-5 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.08] mb-4">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Database className="w-4 h-4 text-blue-400" />
                <span>{lang === 'uz' ? 'Yangi Xotira Yozuvi' : 'New Memory Entry'}</span>
              </h3>
              <button
                onClick={() => setIsAddOpen(false)}
                className="p-1 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateMemory} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">
                  {lang === 'uz' ? 'Kalit (Key):' : 'Key:'}
                </label>
                <input
                  type="text"
                  required
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  placeholder="masalan, Figma Token Qoidasi"
                  className="w-full bg-slate-950 border border-white/[0.08] rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">
                  {lang === 'uz' ? 'Qiymat (Value):' : 'Value:'}
                </label>
                <textarea
                  required
                  rows={3}
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  placeholder="Qoidalar, arxitektura faktlari yoki parametrlar..."
                  className="w-full bg-slate-950 border border-white/[0.08] rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">
                  {lang === 'uz' ? 'Manba vazifa (ixtiyoriy):' : 'Source Task:'}
                </label>
                <input
                  type="text"
                  value={newSource}
                  onChange={(e) => setNewSource(e.target.value)}
                  placeholder="masalan, UI Spec tekshiruvi"
                  className="w-full bg-slate-950 border border-white/[0.08] rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500"
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
                  disabled={isAdding || !newKey.trim() || !newValue.trim()}
                  className="px-4 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white shadow-md transition active:scale-95 disabled:opacity-50"
                >
                  {isAdding ? 'Saqlanmoqda...' : lang === 'uz' ? 'Saqlash' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
