'use client';

import React, { useState } from 'react';
import {
  User,
  Settings,
  Shield,
  Sliders,
  FolderLock,
  Globe,
  Moon,
  Sun,
  X,
  Power,
  CheckCircle2,
  Lock,
  AlertOctagon,
  FileCode,
} from 'lucide-react';

interface Window7ProfileProps {
  lang: 'uz' | 'en';
  onToggleLang: () => void;
  isDark: boolean;
  onToggleTheme: () => void;
  onKillAll: () => void;
}

export const Window7Profile: React.FC<Window7ProfileProps> = ({
  lang,
  onToggleLang,
  isDark,
  onToggleTheme,
  onKillAll,
}) => {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // Settings State (persisted in local state / read-only parameters)
  const [userProfile, setUserProfile] = useState({
    name: 'Kapitan',
    email: 'kapitan@gmail.com',
    authProvider: 'Google OAuth 2.0 (Lokal)',
  });

  const [securityRules, setSecurityRules] = useState({
    confirmFileDelete: true,
    confirmAppAdd: true,
    confirmExternalNetwork: true,
  });

  const [executionLimits, setExecutionLimits] = useState({
    maxSteps: 8,
    maxLoops: 3,
    tokenLimit: 50000,
  });

  const [permissionMode, setPermissionMode] = useState<'ask_always' | 'ask_dangerous_only' | 'free_in_workspace'>('ask_dangerous_only');

  React.useEffect(() => {
    fetch('/api/settings/permission-mode')
      .then((r) => r.json())
      .then((d) => {
        if (d && d.mode) setPermissionMode(d.mode);
      })
      .catch(() => {});
  }, []);

  const handleUpdatePermissionMode = async (mode: 'ask_always' | 'ask_dangerous_only' | 'free_in_workspace') => {
    setPermissionMode(mode);
    try {
      await fetch('/api/settings/permission-mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode }),
      });
    } catch (e) {
      console.error('Failed to update permission mode:', e);
    }
  };

  const [paths] = useState({
    workspaceDir: 'C:\\Users\\Kapitan\\.gemini\\antigravity\\scratch\\conduit\\workspaces',
    staticScreenshots: 'C:\\Users\\Kapitan\\.gemini\\antigravity\\scratch\\conduit\\backend\\static\\screenshots',
    browserBinary: 'Default System Chromium / Playwright',
  });

  return (
    <>
      {/* Window 7 Profile Button in Bottom-Left */}
      <div className="h-20 px-3 py-2 border-t border-white/10 bg-slate-900/70 flex items-center justify-between">
        <button
          onClick={() => setIsSettingsOpen(true)}
          className="flex-1 flex items-center space-x-3 p-1.5 rounded-xl hover:bg-white/5 transition text-left group"
        >
          {/* Avatar */}
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-blue-500/20 group-hover:scale-105 transition">
              K
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-500 border-2 border-slate-950" />
          </div>

          {/* User Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-1.5">
              <span className="text-xs font-semibold text-white truncate">{userProfile.name}</span>
              <span className="text-[9px] px-1 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Google
              </span>
            </div>
            <p className="text-[10px] text-slate-400 truncate font-mono">{userProfile.email}</p>
          </div>

          {/* Gear icon */}
          <div className="p-1.5 rounded-lg text-slate-400 group-hover:text-white group-hover:bg-white/5 transition">
            <Settings className="w-4 h-4" />
          </div>
        </button>
      </div>

      {/* Settings Modal */}
      {isSettingsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-2xl bg-slate-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-slate-950/60">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
                  <Settings className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">
                    {lang === 'uz' ? 'Tizim Sozlamalari & Xavfsizlik' : 'System Settings & Security'}
                  </h3>
                  <p className="text-xs text-slate-400">
                    {lang === 'uz' ? 'Profil, xavfsizlik va ish parametrlari' : 'Profile, security and runtime rules'}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsSettingsOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6 overflow-y-auto flex-1 font-sans text-xs">
              {/* 1. Foydalanuvchi Profili (Faqat Google OAuth) */}
              <div className="p-4 rounded-xl bg-slate-950/50 border border-white/5 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-slate-300 font-medium">
                    <User className="w-4 h-4 text-blue-400" />
                    <span>{lang === 'uz' ? 'Foydalanuvchi Profili' : 'User Profile'}</span>
                  </div>
                  <span className="text-[10px] text-emerald-400 font-mono flex items-center space-x-1">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>{userProfile.authProvider}</span>
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-slate-300">
                  <div className="space-y-1">
                    <label className="text-[11px] text-slate-400">{lang === 'uz' ? 'Ism (Agent murojaati)' : 'User Name'}</label>
                    <input
                      type="text"
                      value={userProfile.name}
                      onChange={(e) => setUserProfile({ ...userProfile, name: e.target.value })}
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 text-white font-mono focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] text-slate-400">{lang === 'uz' ? 'Email (OAuth)' : 'Email'}</label>
                    <input
                      type="text"
                      disabled
                      value={userProfile.email}
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-900/50 border border-white/5 text-slate-400 font-mono cursor-not-allowed"
                    />
                  </div>
                </div>
                <p className="text-[10px] text-slate-400">
                  {lang === 'uz'
                    ? '* Parol yoki kalitlar saqlanmaydi. Autentifikatsiya faqat xavfsiz lokal token orqali amalga oshiriladi.'
                    : '* No passwords stored. Authentication is purely local token-based.'}
                </p>
              </div>

              {/* 2. Til & Tema */}
              <div className="p-4 rounded-xl bg-slate-950/50 border border-white/5 space-y-3">
                <div className="flex items-center space-x-2 text-slate-300 font-medium">
                  <Globe className="w-4 h-4 text-indigo-400" />
                  <span>{lang === 'uz' ? "Til & Ko'rinish" : 'Language & Appearance'}</span>
                </div>
                <div className="flex items-center space-x-4">
                  <button
                    onClick={onToggleLang}
                    className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 hover:border-blue-500 text-slate-200 transition"
                  >
                    <Globe className="w-3.5 h-3.5 text-blue-400" />
                    <span>{lang === 'uz' ? "Til: O'zbekcha" : 'Language: English'}</span>
                  </button>

                  <button
                    onClick={onToggleTheme}
                    className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 hover:border-blue-500 text-slate-200 transition"
                  >
                    {isDark ? <Moon className="w-3.5 h-3.5 text-amber-400" /> : <Sun className="w-3.5 h-3.5 text-amber-400" />}
                    <span>{isDark ? (lang === 'uz' ? "Tema: Qorong'i" : 'Theme: Dark') : (lang === 'uz' ? "Tema: Yorug'" : 'Theme: Light')}</span>
                  </button>
                </div>
              </div>

              {/* 3. Xavfsizlik Qoidalari & Tasdiqlar */}
              <div className="p-4 rounded-xl bg-slate-950/50 border border-white/5 space-y-3">
                <div className="flex items-center justify-between text-slate-300 font-medium">
                  <div className="flex items-center space-x-2">
                    <Shield className="w-4 h-4 text-emerald-400" />
                    <span>{lang === 'uz' ? 'Xavfsizlik Perimetri & Tasdiqlar' : 'Security Perimeter & Approvals'}</span>
                  </div>
                  <span className="text-[10px] text-emerald-400 font-mono">Xavfsiz Sandboxed</span>
                </div>
                <div className="space-y-2">
                  <label className="flex items-center space-x-2.5 text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={securityRules.confirmFileDelete}
                      onChange={(e) => setSecurityRules({ ...securityRules, confirmFileDelete: e.target.checked })}
                      className="rounded bg-slate-900 border-white/20 text-blue-500 focus:ring-0"
                    />
                    <span>{lang === 'uz' ? "Fayllarni o'chirishdan oldin inson tasdig'ini so'rash" : 'Require human approval before deleting files'}</span>
                  </label>
                  <label className="flex items-center space-x-2.5 text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={securityRules.confirmAppAdd}
                      onChange={(e) => setSecurityRules({ ...securityRules, confirmAppAdd: e.target.checked })}
                      className="rounded bg-slate-900 border-white/20 text-blue-500 focus:ring-0"
                    />
                    <span>{lang === 'uz' ? "Yangi ilova yoki subagent o'rnatishda tasdiq so'rash" : 'Require approval when installing new apps/subagents'}</span>
                  </label>
                  <label className="flex items-center space-x-2.5 text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={securityRules.confirmExternalNetwork}
                      onChange={(e) => setSecurityRules({ ...securityRules, confirmExternalNetwork: e.target.checked })}
                      className="rounded bg-slate-900 border-white/20 text-blue-500 focus:ring-0"
                    />
                    <span>{lang === 'uz' ? "Tashqi tarmoq so'rovlarida xavfsizlik auditini o'tkazish" : 'Audit external network actions'}</span>
                  </label>
                </div>

                {/* Ruxsat darajasi tanlovi (Bosqich 3) */}
                <div className="space-y-1.5 pt-2 border-t border-white/5">
                  <label className="text-[11px] font-bold text-slate-300 block">
                    {lang === 'uz' ? 'Ruxsat Darajasi (Permission Level):' : 'Permission Level:'}
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    {[
                      {
                        id: 'ask_always',
                        labelUz: 'Har qadamda so\'ra',
                        labelEn: 'Ask always',
                        descUz: 'Barcha amallar uchun tasdiq so\'raladi',
                      },
                      {
                        id: 'ask_dangerous_only',
                        labelUz: 'Faqat xavfli amalda so\'ra',
                        labelEn: 'Dangerous only',
                        descUz: 'Fayl o\'chirish va git push da so\'raydi',
                      },
                      {
                        id: 'free_in_workspace',
                        labelUz: 'Ish papkasida erkin',
                        labelEn: 'Free in workspace',
                        descUz: 'Subagent o\'z papkasida erkin ishlaydi',
                      },
                    ].map((opt) => (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() => handleUpdatePermissionMode(opt.id as any)}
                        className={`p-2 rounded-xl border text-left transition-all ${
                          permissionMode === opt.id
                            ? 'bg-blue-600/20 border-blue-500 text-white shadow-sm'
                            : 'bg-slate-900/80 border-white/10 text-slate-400 hover:text-slate-200 hover:border-white/20'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-0.5">
                          <span className="text-[11px] font-bold">
                            {lang === 'uz' ? opt.labelUz : opt.labelEn}
                          </span>
                          {permissionMode === opt.id && (
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                          )}
                        </div>
                        <p className="text-[9px] text-slate-400 leading-tight">
                          {opt.descUz}
                        </p>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* 4. Ish Qoidalari (Limits) */}
              <div className="p-4 rounded-xl bg-slate-950/50 border border-white/5 space-y-3">
                <div className="flex items-center space-x-2 text-slate-300 font-medium">
                  <Sliders className="w-4 h-4 text-cyan-400" />
                  <span>{lang === 'uz' ? 'Ijro Chegaralari (Limits)' : 'Execution Limits'}</span>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="text-[11px] text-slate-400">{lang === 'uz' ? 'Maks Qadam' : 'Max Steps'}</label>
                    <input
                      type="number"
                      value={executionLimits.maxSteps}
                      onChange={(e) => setExecutionLimits({ ...executionLimits, maxSteps: parseInt(e.target.value) || 8 })}
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 text-white font-mono"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] text-slate-400">{lang === 'uz' ? 'Maks Sikl' : 'Max Loops'}</label>
                    <input
                      type="number"
                      value={executionLimits.maxLoops}
                      onChange={(e) => setExecutionLimits({ ...executionLimits, maxLoops: parseInt(e.target.value) || 3 })}
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 text-white font-mono"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] text-slate-400">{lang === 'uz' ? 'Token Limiti' : 'Token Limit'}</label>
                    <input
                      type="number"
                      value={executionLimits.tokenLimit}
                      onChange={(e) => setExecutionLimits({ ...executionLimits, tokenLimit: parseInt(e.target.value) || 50000 })}
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 text-white font-mono"
                    />
                  </div>
                </div>
              </div>

              {/* 5. Papkalar va Ilova Yo'llari */}
              <div className="p-4 rounded-xl bg-slate-950/50 border border-white/5 space-y-3 font-mono text-[11px]">
                <div className="flex items-center space-x-2 text-slate-300 font-sans text-xs font-medium">
                  <FolderLock className="w-4 h-4 text-amber-400" />
                  <span>{lang === 'uz' ? "Papkalar & Ilova Yo'llari" : 'Paths & Directories'}</span>
                </div>
                <div className="space-y-2 text-slate-400">
                  <div>
                    <span className="text-slate-500">Workspaces:</span>
                    <p className="text-slate-300 break-all bg-slate-900/60 p-1.5 rounded border border-white/5">
                      {paths.workspaceDir}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-500">Skrinshotlar:</span>
                    <p className="text-slate-300 break-all bg-slate-900/60 p-1.5 rounded border border-white/5">
                      {paths.staticScreenshots}
                    </p>
                  </div>
                </div>
              </div>

              {/* Muhim bildirishnoma: Engine va Model UI da yo'q */}
              <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-300 flex items-start space-x-2.5">
                <FileCode className="w-4 h-4 text-blue-400 mt-0.5 shrink-0" />
                <p className="text-[11px] leading-relaxed">
                  {lang === 'uz'
                    ? "Eslatma: Dvigatel, model va OmniRoute kalitlari UI ga kiritilmagan. Ular qat'iy ravishda lokal config/engine.json faylida shifrlangan saqlanadi."
                    : 'Notice: Engine, model and OmniRoute configurations remain strictly stored in local config/engine.json.'}
                </p>
              </div>

              {/* Favqulodda to'xtatish */}
              <div className="pt-2 flex items-center justify-between border-t border-white/10">
                <span className="text-xs text-rose-400 font-medium">
                  {lang === 'uz' ? 'Favqulodda Harakatlar:' : 'Emergency Actions:'}
                </span>
                <button
                  onClick={() => {
                    onKillAll();
                    setIsSettingsOpen(false);
                  }}
                  className="px-4 py-2 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 flex items-center space-x-2 transition font-medium text-xs shadow-lg shadow-rose-500/10"
                >
                  <AlertOctagon className="w-4 h-4 text-rose-400" />
                  <span>{lang === 'uz' ? "Hammasini to'xtatish (Kill All)" : 'Emergency Kill All'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
