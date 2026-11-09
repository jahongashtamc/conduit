'use client';

import React, { useState } from 'react';
import { Cpu, CheckCircle2, XCircle, Code, Copy, Check, ChevronDown, ChevronUp, ExternalLink, Power } from 'lucide-react';
import { Language, translations } from '@/lib/translations';

interface AgentInfo {
  is_connected: boolean;
  agent_name: string;
  protocol: string;
  transport: string;
  last_heartbeat?: string;
  mcp_config_sample?: any;
}

interface AgentConnectionBannerProps {
  agentInfo: AgentInfo;
  onToggleConnection: () => Promise<void>;
  lang: Language;
}

export const AgentConnectionBanner: React.FC<AgentConnectionBannerProps> = ({
  agentInfo,
  onToggleConnection,
  lang,
}) => {
  const [showConfig, setShowConfig] = useState(false);
  const [copied, setCopied] = useState(false);

  const configText = JSON.stringify(agentInfo.mcp_config_sample || {
    "mcpServers": {
      "conduit": {
        "command": "python",
        "args": ["backend/mcp_server.py"]
      }
    }
  }, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(configText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mb-5 rounded-2xl bg-slate-900/90 border border-slate-800 p-3.5 shadow-md">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        {/* Left: Agent Info */}
        <div className="flex items-center space-x-3">
          <div
            className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${
              agentInfo.is_connected
                ? 'bg-blue-600/20 text-blue-400 border-blue-500/40 shadow-sm shadow-blue-500/20'
                : 'bg-slate-800 text-slate-500 border-slate-700'
            }`}
          >
            <Cpu className="w-5 h-5" />
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-slate-100">
                {lang === 'uz' ? 'AI Agent Ulanishi:' : 'AI Agent Connection:'}
              </span>
              <span
                className={`text-[11px] font-semibold px-2 py-0.5 rounded-full flex items-center space-x-1 ${
                  agentInfo.is_connected
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                    : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    agentInfo.is_connected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
                  }`}
                />
                <span>
                  {agentInfo.is_connected
                    ? lang === 'uz'
                      ? 'Ulangan (MCP Faol)'
                      : 'Connected (MCP Active)'
                    : lang === 'uz'
                    ? 'Agent Ulanmagan'
                    : 'Agent Disconnected'}
                </span>
              </span>
            </div>

            <p className="text-[11px] text-slate-400 mt-0.5 flex items-center space-x-2">
              <span className="font-semibold text-slate-300">{agentInfo.agent_name}</span>
              <span className="text-slate-600">•</span>
              <span className="text-slate-500 font-mono text-[10px]">{agentInfo.protocol}</span>
            </p>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center space-x-2 self-end sm:self-auto">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-300 border border-slate-700 text-xs font-medium transition"
          >
            <Code className="w-3.5 h-3.5 text-cyan-400" />
            <span>mcp.json</span>
            {showConfig ? <ChevronUp className="w-3 h-3 ml-0.5" /> : <ChevronDown className="w-3 h-3 ml-0.5" />}
          </button>

          <button
            onClick={onToggleConnection}
            className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-semibold border transition ${
              agentInfo.is_connected
                ? 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border-rose-500/30'
                : 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
            }`}
            title="Simulate Agent Connect / Disconnect"
          >
            <Power className="w-3 h-3" />
            <span>
              {agentInfo.is_connected
                ? lang === 'uz'
                  ? 'Uzish'
                  : 'Disconnect'
                : lang === 'uz'
                ? 'Ulash'
                : 'Connect'}
            </span>
          </button>
        </div>
      </div>

      {/* Expandable MCP Configuration Guide */}
      {showConfig && (
        <div className="mt-3 pt-3 border-t border-slate-800/80 animate-in fade-in duration-150">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] font-semibold text-slate-300">
              {lang === 'uz'
                ? "Antigravity yoki Claude Desktop uchun mcp.json namunasi:"
                : 'mcp.json snippet for Antigravity or Claude Desktop:'}
            </span>
            <button
              onClick={handleCopy}
              className="flex items-center space-x-1 text-[10px] text-blue-400 hover:text-blue-300 transition"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? (lang === 'uz' ? 'Nusxalandi!' : 'Copied!') : lang === 'uz' ? 'Nusxa olish' : 'Copy'}</span>
            </button>
          </div>

          <pre className="p-3 rounded-xl bg-slate-950 font-mono text-[11px] text-cyan-300 border border-slate-800 overflow-x-auto leading-relaxed">
            {configText}
          </pre>
          <p className="text-[10px] text-slate-500 mt-1 italic">
            {lang === 'uz'
              ? "Ushbu konfiguratsiyani MCP mijozingiz sozlamalariga joylang. Agent avtomatik ravishda list_subagents va run_task toollaridan foydalanadi."
              : 'Add this config to your MCP client. The agent automatically interacts via list_subagents and run_task tools.'}
          </p>
        </div>
      )}
    </div>
  );
};
