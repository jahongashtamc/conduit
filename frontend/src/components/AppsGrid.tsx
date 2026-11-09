'use client';

import React from 'react';
import { Box, Sparkles, Film, Video, Layers, Palette, Activity, Check, X } from 'lucide-react';
import { Language, translations } from '@/lib/translations';

interface AppItem {
  id: string;
  name: string;
  category: string;
  status: 'ready' | 'not installed' | 'running';
  icon: string;
  executable?: string;
}

interface AppsGridProps {
  apps: AppItem[];
  lang: Language;
}

const getAppIcon = (id: string) => {
  switch (id) {
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

export const AppsGrid: React.FC<AppsGridProps> = ({ apps, lang }) => {
  const t = translations[lang];

  return (
    <section className="mb-6">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            {t.appsTitle}
          </h2>
          <p className="text-[11px] text-slate-500">{t.appsDesc}</p>
        </div>
        <div className="flex items-center space-x-3 text-[11px] text-slate-400">
          <span className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>{t.appReady}</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
            <span>{t.appRunning}</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-slate-600" />
            <span>{t.appNotInstalled}</span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">
        {apps.map((app) => {
          const Icon = getAppIcon(app.id);
          const isRunning = app.status === 'running';
          const isReady = app.status === 'ready';

          return (
            <div
              key={app.id}
              className={`p-3.5 rounded-xl border transition-all duration-200 relative overflow-hidden flex flex-col justify-between ${
                isRunning
                  ? 'bg-blue-950/20 border-blue-500/50 shadow-md shadow-blue-500/10'
                  : isReady
                  ? 'bg-slate-900/90 border-slate-700/80 hover:border-slate-600'
                  : 'bg-slate-900/40 border-slate-800/60 opacity-75'
              }`}
            >
              <div className="flex items-start justify-between">
                <div
                  className={`p-2 rounded-lg ${
                    isRunning
                      ? 'bg-blue-500 text-white shadow-sm shadow-blue-500/30'
                      : isReady
                      ? 'bg-slate-800 text-blue-400'
                      : 'bg-slate-800/60 text-slate-500'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>

                {/* Status Badge */}
                <div className="flex items-center space-x-1">
                  {isRunning ? (
                    <span className="flex items-center space-x-1 text-[10px] font-semibold text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded border border-blue-500/30">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping" />
                      <span>{t.appRunning}</span>
                    </span>
                  ) : isReady ? (
                    <span className="flex items-center space-x-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/30">
                      <Check className="w-2.5 h-2.5" />
                      <span>{t.appReady}</span>
                    </span>
                  ) : (
                    <span className="flex items-center space-x-1 text-[10px] font-medium text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700/50">
                      <X className="w-2.5 h-2.5" />
                      <span>{t.appNotInstalled}</span>
                    </span>
                  )}
                </div>
              </div>

              <div className="mt-3">
                <h3 className="font-semibold text-xs text-slate-100">{app.name}</h3>
                <p className="text-[10px] text-slate-400 mt-0.5 truncate">{app.category}</p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
