'use client';

import React, { useState, useEffect } from 'react';
import { Image as ImageIcon, Film, FileText, RefreshCw, FolderOpen, Loader2 } from 'lucide-react';
import { Language } from '@/lib/translations';

interface Artifact {
  agent: string;
  file: string;
  path: string;
  ext: string;
  kind: 'media' | 'text';
  mime: string;
  bytes: number;
  modified: number;
}

interface GalleryTabProps {
  lang: Language;
}

const fmtBytes = (b: number) =>
  b > 1024 * 1024 ? `${(b / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB`;

const fmtTime = (ts: number) =>
  new Date(ts * 1000).toLocaleString('uz-UZ', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });

export const GalleryTab: React.FC<GalleryTabProps> = ({ lang }) => {
  const [items, setItems] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'media' | 'text'>('all');
  const [preview, setPreview] = useState<Artifact | null>(null);
  const [textContent, setTextContent] = useState<string>('');

  useEffect(() => {
    if (!preview || preview.kind !== 'text') return;
    let alive = true;
    setTextContent('');
    fetch(`/api/artifacts/file?path=${encodeURIComponent(preview.path)}`)
      .then((r) => r.text())
      .then((t) => {
        if (alive) setTextContent(t.slice(0, 20000));
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [preview]);

  const fetchArtifacts = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/artifacts', { cache: 'no-store' });
      if (res.ok) {
        const d = await res.json();
        setItems(d.artifacts || []);
      }
    } catch {
      // backend starting
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArtifacts();
  }, []);

  const shown = items.filter((i) => (filter === 'all' ? true : i.kind === filter));
  const agents = [...new Set(items.map((i) => i.agent))];

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-900/60 border border-white/[0.08] rounded-2xl overflow-hidden shadow-xl select-none">
      <div className="p-4 border-b border-white/[0.08] flex items-center justify-between gap-3 bg-slate-950/40">
        <div>
          <h2 className="text-sm font-bold text-white flex items-center space-x-2">
            <ImageIcon className="w-4 h-4 text-cyan-400" aria-hidden="true" />
            <span>{lang === 'uz' ? 'Artefakt Galereyasi' : 'Artifact Gallery'}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            {lang === 'uz'
              ? `${items.length} ta fayl · ${agents.length} ta agent workspace'i`
              : `${items.length} files · ${agents.length} agent workspaces`}
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          {(['all', 'media', 'text'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              aria-pressed={filter === f}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-medium border transition ${
                filter === f
                  ? 'bg-cyan-600 text-white border-cyan-500'
                  : 'bg-slate-900/90 text-slate-400 border-white/[0.08] hover:text-white'
              }`}
            >
              {f === 'all' ? (lang === 'uz' ? 'Hammasi' : 'All') : f === 'media' ? (lang === 'uz' ? 'Media' : 'Media') : (lang === 'uz' ? 'Matn' : 'Text')}
            </button>
          ))}
          <button
            onClick={fetchArtifacts}
            aria-label={lang === 'uz' ? 'Yangilash' : 'Refresh'}
            className="p-1.5 rounded-lg border border-white/[0.08] text-slate-400 hover:text-white transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} aria-hidden="true" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className="flex items-center justify-center py-16 text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin text-cyan-500 mr-2" aria-hidden="true" />
            <span className="text-xs">{lang === 'uz' ? 'Yuklanmoqda...' : 'Loading...'}</span>
          </div>
        ) : shown.length === 0 ? (
          <p className="text-xs text-slate-500 text-center py-16">
            {lang === 'uz'
              ? 'Hali artefakt yo\\u2018q. Vazifa bering — yaratilgan fayllar shu yerda paydo bo\\u2018ladi.'
              : 'No artifacts yet. Run a task — created files appear here.'}
          </p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3">
            {shown.map((a) => (
              <button
                key={a.path}
                onClick={() => setPreview(a)}
                aria-label={`${a.agent}: ${a.file}`}
                className="group rounded-xl border border-white/[0.08] bg-slate-950/60 overflow-hidden text-left hover:border-cyan-500/40 transition"
              >
                <div className="h-28 bg-black/40 flex items-center justify-center overflow-hidden">
                  {a.kind === 'media' && a.ext !== '.mp4' && a.ext !== '.webm' ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={`/api/artifacts/file?path=${encodeURIComponent(a.path)}`}
                      alt={a.file}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                      loading="lazy"
                    />
                  ) : a.kind === 'media' ? (
                    <Film className="w-8 h-8 text-slate-600" aria-hidden="true" />
                  ) : (
                    <FileText className="w-8 h-8 text-slate-600" aria-hidden="true" />
                  )}
                </div>
                <div className="p-2">
                  <p className="text-[11px] font-medium text-white truncate">{a.file}</p>
                  <p className="text-[10px] text-slate-500 font-mono flex justify-between">
                    <span>{a.agent}</span>
                    <span>{fmtBytes(a.bytes)}</span>
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Preview modal */}
      {preview && (
        <div
          className="absolute inset-0 bg-black/80 flex items-center justify-center p-8 z-50"
          role="dialog"
          aria-modal="true"
          onClick={() => setPreview(null)}
        >
          <div
            className="max-w-4xl w-full bg-slate-950 border border-white/10 rounded-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-4 py-2.5 flex items-center justify-between border-b border-white/10">
              <div className="min-w-0">
                <p className="text-xs font-semibold text-white truncate">{preview.file}</p>
                <p className="text-[10px] text-slate-500 font-mono">
                  {preview.agent} · {fmtBytes(preview.bytes)} · {fmtTime(preview.modified)}
                </p>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                <a
                  href={`/api/artifacts/file?path=${encodeURIComponent(preview.path)}`}
                  download={preview.file}
                  className="px-2 py-1 rounded-lg border border-white/10 text-[11px] text-slate-300 hover:text-white transition"
                >
                  {lang === 'uz' ? 'Yuklab olish' : 'Download'}
                </a>
                <button
                  onClick={() => setPreview(null)}
                  aria-label={lang === 'uz' ? 'Yopish' : 'Close'}
                  className="px-2 py-1 rounded-lg border border-white/10 text-[11px] text-slate-300 hover:text-rose-300 transition"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="max-h-[70vh] overflow-auto bg-black/50 flex items-center justify-center">
              {preview.kind === 'media' && preview.ext !== '.mp4' && preview.ext !== '.webm' ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={`/api/artifacts/file?path=${encodeURIComponent(preview.path)}`}
                  alt={preview.file}
                  className="max-w-full max-h-[70vh] object-contain"
                />
              ) : preview.kind === 'media' ? (
                <video
                  src={`/api/artifacts/file?path=${encodeURIComponent(preview.path)}`}
                  controls
                  className="max-w-full max-h-[70vh]"
                />
              ) : (
                <pre className="p-4 text-[11px] text-slate-300 whitespace-pre-wrap max-w-full">
                  {textContent || '...'}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
