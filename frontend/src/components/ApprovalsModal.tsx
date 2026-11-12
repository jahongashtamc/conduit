'use client';

import React, { useState } from 'react';
import { 
  ShieldAlert, 
  AlertTriangle, 
  CheckCheck, 
  Check, 
  X, 
  Terminal, 
  FileWarning, 
  Flame,
  ShieldCheck
} from 'lucide-react';

interface ApprovalItem {
  approval_id: string;
  task_id: string;
  agent_id: string;
  action_type: string;
  risk_description: string;
  details_json: string;
  status: string;
  created_at: string;
  is_dangerous?: boolean;
}

interface ApprovalsModalProps {
  isOpen: boolean;
  onClose: () => void;
  approvals: ApprovalItem[];
  onResolve: (approvalId: string, decision: 'approved' | 'rejected') => void;
  onApproveAll: () => void;
  lang: 'uz' | 'en';
}

export const ApprovalsModal: React.FC<ApprovalsModalProps> = ({
  isOpen,
  onClose,
  approvals,
  onResolve,
  onApproveAll,
  lang,
}) => {
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  if (!isOpen) return null;

  const pendingApprovals = approvals.filter((a) => a.status === 'pending');
  const dangerousCount = pendingApprovals.filter(
    (a) =>
      a.is_dangerous ||
      ['file_delete', 'git_push', 'db_drop'].includes(a.action_type) ||
      ['o\'chirish', 'delete', 'rm', 'git push', 'drop', 'wipe'].some((kw) =>
        a.risk_description.toLowerCase().includes(kw)
      )
  ).length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4" onClick={onClose}>
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/70">
          <div className="flex items-center space-x-3">
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center border transition-all ${
                dangerousCount > 0
                  ? 'bg-red-500/10 border-red-500/40 text-red-400 animate-pulse'
                  : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
              }`}
            >
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-semibold text-white tracking-wide">
                  {lang === 'uz' ? 'Tasdiqlar Navbati' : 'Approval Queue'}
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-slate-800 text-[10px] font-mono text-slate-300">
                  {pendingApprovals.length} {lang === 'uz' ? 'kutilmoqda' : 'pending'}
                </span>
                {dangerousCount > 0 && (
                  <span className="px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/40 text-[10px] font-bold flex items-center space-x-1">
                    <Flame className="w-3 h-3 text-red-400" />
                    <span>{dangerousCount} {lang === 'uz' ? 'xavfli' : 'dangerous'}</span>
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400">
                {lang === 'uz'
                  ? 'Subagentlar xavfsizligi va buyruqlarni nazorat qilish'
                  : 'Subagent permission gates and danger inspection'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {pendingApprovals.length > 0 && (
              <button
                onClick={onApproveAll}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center space-x-1.5 shadow-sm transition-all"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                <span>{lang === 'uz' ? 'Hammasiga ruxsat' : 'Approve All'}</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="w-7 h-7 rounded-lg hover:bg-slate-800 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content list */}
        <div className="flex-1 overflow-y-auto p-6 space-y-3">
          {pendingApprovals.length === 0 ? (
            <div className="py-12 flex flex-col items-center justify-center text-center space-y-2 text-slate-500">
              <ShieldCheck className="w-10 h-10 text-emerald-500/40" />
              <p className="text-xs font-medium text-slate-400">
                {lang === 'uz' ? 'Hozircha kutilayotgan ruxsatlar yo\'q' : 'No pending approval requests'}
              </p>
              <p className="text-[11px] text-slate-600">
                {lang === 'uz'
                  ? 'Xavfli buyruqlar va yangi ilovalar kelib tushganda bu yerda ko\'rsatiladi'
                  : 'Dangerous commands and new integrations will pause here'}
              </p>
            </div>
          ) : (
            pendingApprovals.map((item) => {
              const isDangerous =
                item.is_dangerous ||
                ['file_delete', 'git_push', 'db_drop'].includes(item.action_type) ||
                ['o\'chirish', 'delete', 'rm', 'git push', 'drop', 'wipe'].some((kw) =>
                  item.risk_description.toLowerCase().includes(kw)
                );

              return (
                <div
                  key={item.approval_id}
                  className={`p-4 rounded-xl border transition-all ${
                    isDangerous
                      ? 'border-2 border-red-500 bg-red-950/40 text-red-200 shadow-lg shadow-red-950/50'
                      : 'border-slate-800 bg-slate-950/80 text-slate-200'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start space-x-3">
                      <div
                        className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                          isDangerous
                            ? 'bg-red-500/20 text-red-400 border border-red-500/50'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        }`}
                      >
                        {isDangerous ? (
                          <AlertTriangle className="w-4 h-4 text-red-400" />
                        ) : (
                          <FileWarning className="w-4 h-4 text-amber-400" />
                        )}
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-xs uppercase tracking-wide">
                            {item.action_type}
                          </span>
                          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-slate-300">
                            Agent: {item.agent_id}
                          </span>
                          {isDangerous && (
                            <span className="px-1.5 py-0.5 rounded bg-red-500 text-white text-[9px] font-black uppercase tracking-wider">
                              XAVFLI BUYRUQ
                            </span>
                          )}
                        </div>
                        <p className="text-xs leading-relaxed font-medium">
                          {item.risk_description}
                        </p>
                        <div className="text-[10px] text-slate-400 font-mono">
                          Vazifa ID: {item.task_id}
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2 shrink-0">
                      <button
                        onClick={() => onResolve(item.approval_id, 'rejected')}
                        className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
                      >
                        {lang === 'uz' ? 'Rad etish' : 'Reject'}
                      </button>
                      <button
                        onClick={() => onResolve(item.approval_id, 'approved')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1 shadow-sm transition-all ${
                          isDangerous
                            ? 'bg-red-600 hover:bg-red-500 text-white'
                            : 'bg-emerald-600 hover:bg-emerald-500 text-white'
                        }`}
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>{lang === 'uz' ? 'Ruxsat berish' : 'Approve'}</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
