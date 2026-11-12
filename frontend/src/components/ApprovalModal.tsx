'use client';

import React from 'react';
import { AlertTriangle, ShieldAlert, CheckCircle2, XCircle, FileWarning, Terminal } from 'lucide-react';
import { Language, translations } from '@/lib/translations';

export interface ApprovalItem {
  id?: number;
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

interface ApprovalModalProps {
  approvals: ApprovalItem[];
  onResolve: (approvalId: string, decision: 'approved' | 'rejected') => Promise<void>;
  lang: Language;
}

export const ApprovalModal: React.FC<ApprovalModalProps> = ({
  approvals,
  onResolve,
  lang,
}) => {
  const t = translations[lang];

  if (!approvals || approvals.length === 0) return null;

  const current = approvals[0];

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="max-w-lg w-full bg-slate-900 border-2 border-amber-500/80 rounded-2xl p-6 shadow-2xl shadow-amber-500/10 animate-in fade-in zoom-in-95 duration-200">
        {/* Header with Risk Warning */}
        <div className="flex items-start space-x-3.5">
          <div className="p-3 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/40 shrink-0">
            <AlertTriangle className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30">
                Xavfsizlik Ogohlantirishi
              </span>
              <span className="text-xs font-mono text-slate-500">[{current.approval_id}]</span>
            </div>
            <h3 className="text-base font-bold text-slate-100 mt-1">{t.approvalTitle}</h3>
            <p className="text-xs text-slate-400 mt-0.5">{t.approvalDesc}</p>
          </div>
        </div>

        {/* Risk Details Card */}
        <div className="mt-4 p-4 rounded-xl bg-slate-950/90 border border-slate-800 text-xs space-y-2.5">
          <div className="flex justify-between items-center text-slate-400">
            <span className="font-semibold text-slate-300">Ijrochi Subagent:</span>
            <span className="font-mono text-blue-400 uppercase font-bold">{current.agent_id}</span>
          </div>

          <div className="flex justify-between items-center text-slate-400">
            <span className="font-semibold text-slate-300">Amal turi:</span>
            <span className="font-mono text-amber-400 px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 font-bold">
              {current.action_type}
            </span>
          </div>

          <div className="pt-2 border-t border-slate-800/80">
            <span className="font-semibold text-slate-300 block mb-1">Xavf tafsiloti:</span>
            <p className="text-rose-300/90 bg-rose-500/10 p-2.5 rounded-lg border border-rose-500/20 font-mono text-[11px] leading-relaxed">
              {current.risk_description}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-6 flex items-center justify-end space-x-3">
          <button
            onClick={() => onResolve(current.approval_id, 'rejected')}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition active:scale-95"
          >
            <XCircle className="w-4 h-4 text-rose-400" />
            <span>{t.rejectBtn}</span>
          </button>

          <button
            onClick={() => onResolve(current.approval_id, 'approved')}
            className="flex items-center space-x-1.5 px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition shadow-lg shadow-amber-500/20 active:scale-95"
          >
            <CheckCircle2 className="w-4 h-4 text-slate-950" />
            <span>{t.approveBtn}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
