'use client';

import React, { useEffect, useRef, useState } from 'react';
import '@xterm/xterm/css/xterm.css';
import { Terminal as TerminalIcon, Play, RefreshCw, Trash2 } from 'lucide-react';

interface Window1TerminalProps {
  lang: 'uz' | 'en';
}

export const Window1Terminal: React.FC<Window1TerminalProps> = ({ lang }) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermInstanceRef = useRef<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [termStatus, setTermStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [retrySeconds, setRetrySeconds] = useState<number>(1);

  useEffect(() => {
    let term: any = null;
    let fitAddon: any = null;
    let isDisposed = false;
    let reconnectTimeout: any = null;
    let pingInterval: any = null;
    let backoffSec = 1;

    const initTerminal = async () => {
      if (!terminalRef.current) return;

      const { Terminal } = await import('@xterm/xterm');
      const { FitAddon } = await import('@xterm/addon-fit');

      if (isDisposed) return;

      term = new Terminal({
        theme: {
          background: '#090d16',
          foreground: '#e2e8f0',
          cursor: '#38bdf8',
          cursorAccent: '#090d16',
          selectionBackground: 'rgba(56, 189, 248, 0.3)',
          black: '#0f172a',
          red: '#f43f5e',
          green: '#10b981',
          yellow: '#f59e0b',
          blue: '#3b82f6',
          magenta: '#a855f7',
          cyan: '#06b6d4',
          white: '#f8fafc',
          brightBlack: '#475569',
          brightRed: '#fb7185',
          brightGreen: '#34d399',
          brightYellow: '#fbbf24',
          brightBlue: '#60a5fa',
          brightMagenta: '#c084fc',
          brightCyan: '#22d3ee',
          brightWhite: '#ffffff',
        },
        fontFamily: 'Consolas, "Fira Code", monospace',
        fontSize: 12,
        lineHeight: 1.25,
        cursorBlink: true,
        allowTransparency: true,
        rows: 16,
      });

      fitAddon = new FitAddon();
      term.loadAddon(fitAddon);

      terminalRef.current.innerHTML = '';
      term.open(terminalRef.current);
      fitAddon.fit();
      xtermInstanceRef.current = term;

      // Handle user key inputs in xterm
      term.onData((data: string) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(data);
        }
      });

      const connectSocket = () => {
        if (isDisposed) return;
        setTermStatus('connecting');

        const wsUrl = `ws://${window.location.hostname}:8000/ws/terminal`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setTermStatus('connected');
          backoffSec = 1;
          setRetrySeconds(1);

          // Clear terminal before replaying persistent session scrollback
          if (term) {
            term.clear();
          }

          // Start ping heartbeat
          if (pingInterval) clearInterval(pingInterval);
          pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send('ping');
            }
          }, 10000);
        };

        ws.onmessage = (e) => {
          if (e.data === 'pong' || e.data === '{"type":"pong"}') {
            return;
          }
          if (term) {
            term.write(e.data);
          }
        };

        ws.onclose = () => {
          setTermStatus('disconnected');
          if (pingInterval) clearInterval(pingInterval);

          if (!isDisposed) {
            // Automatic reconnection with exponential backoff: 1s, 2s, 4s, 8s max
            const delay = backoffSec * 1000;
            setRetrySeconds(backoffSec);
            reconnectTimeout = setTimeout(() => {
              connectSocket();
            }, delay);
            backoffSec = Math.min(backoffSec * 2, 8);
          }
        };

        ws.onerror = () => {
          setTermStatus('disconnected');
          ws.close();
        };
      };

      connectSocket();

      // Resize listener
      const handleResize = () => {
        if (fitAddon) {
          try {
            fitAddon.fit();
          } catch (_) {}
        }
      };
      window.addEventListener('resize', handleResize);
    };

    initTerminal();

    return () => {
      isDisposed = true;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (pingInterval) clearInterval(pingInterval);
      if (wsRef.current) wsRef.current.close();
      if (term) term.dispose();
    };
  }, []);

  const sendQuickCommand = (cmd: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(cmd + '\r');
    }
  };

  const handleClear = () => {
    if (xtermInstanceRef.current) {
      xtermInstanceRef.current.clear();
      sendQuickCommand('cls');
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-[#090d16] border-b border-white/10 overflow-hidden font-mono select-none">
      {/* Terminal Titlebar */}
      <div className="h-10 px-3 border-b border-white/10 flex items-center justify-between bg-slate-900/80">
        <div className="flex items-center space-x-2">
          <TerminalIcon className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-xs font-semibold text-slate-200 uppercase tracking-wide">
            {lang === 'uz' ? 'Oyna 1 — Agent Terminali' : 'Window 1 — Agent Terminal'}
          </span>
          {/* Reactive Status Dot (Emerald = Connected, Amber = Reconnecting, Rose = Disconnected) */}
          <span
            title={
              termStatus === 'connected'
                ? 'ConPTY Sessiya: Ulangan (127.0.0.1)'
                : termStatus === 'connecting'
                ? `Qayta ulanmoqda (${retrySeconds}s)...`
                : 'Ulanish uzildi (Avto tiklanadi)'
            }
            className={`w-2 h-2 rounded-full transition-all ${
              termStatus === 'connected'
                ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50'
                : termStatus === 'connecting'
                ? 'bg-amber-400 animate-ping'
                : 'bg-rose-500'
            }`}
          />
        </div>

        {/* Quick action chips */}
        <div className="flex items-center space-x-1.5 text-[10px]">
          <button
            onClick={() => sendQuickCommand('conduit list')}
            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          >
            conduit list
          </button>
          <button
            onClick={() =>
              sendQuickCommand(
                'conduit run scout "tools.py screenshot http://localhost:3000"'
              )
            }
            className="px-2 py-0.5 rounded bg-blue-900/40 hover:bg-blue-800/60 text-blue-300 border border-blue-500/20 transition flex items-center space-x-1"
          >
            <Play className="w-2.5 h-2.5" />
            <span>run scout</span>
          </button>
          <button
            onClick={handleClear}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition"
            title="Clear"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* xterm.js container */}
      <div className="flex-1 p-2 overflow-hidden relative">
        <div ref={terminalRef} className="w-full h-full" />
      </div>
    </div>
  );
};
