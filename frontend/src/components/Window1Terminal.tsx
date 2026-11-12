'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import '@xterm/xterm/css/xterm.css';
import { Terminal as TerminalIcon, Play, RefreshCw, Trash2, Send, CornerDownLeft, Power } from 'lucide-react';

interface Window1TerminalProps {
  lang: 'uz' | 'en';
}

export const Window1Terminal: React.FC<Window1TerminalProps> = ({ lang }) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermInstanceRef = useRef<any>(null);
  const fitAddonRef = useRef<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [termStatus, setTermStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [retrySeconds, setRetrySeconds] = useState<number>(1);
  const [inputCmd, setInputCmd] = useState<string>('');
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState<number>(-1);

  // Send command helper
  const sendCommand = useCallback((cmd: string) => {
    const trimmed = cmd.trim();
    if (!trimmed) return;

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'run', command: trimmed }));
    }

    setHistory((prev) => [...prev, trimmed]);
    setHistoryIndex(-1);
    setInputCmd('');
  }, []);

  useEffect(() => {
    let term: any = null;
    let fitAddon: any = null;
    let isDisposed = false;
    let reconnectTimeout: any = null;
    let pingInterval: any = null;
    let backoffSec = 1;
    let resizeObserver: ResizeObserver | null = null;
    let handleUnload: () => void = () => {};

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
        rows: 14,
        convertEol: false, // haqiqiy PTY \r\n beradi — qayta o'girish kerak emas
      });

      fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      fitAddonRef.current = fitAddon;

      terminalRef.current.innerHTML = '';
      term.open(terminalRef.current);
      xtermInstanceRef.current = term;

      // Fit + o'lcham o'zgarishini backend PTY'ga xabar qilish
      const sendResize = () => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && term) {
          wsRef.current.send(JSON.stringify({ type: 'resize', cols: term.cols, rows: term.rows }));
        }
      };
      setTimeout(() => {
        if (!isDisposed && fitAddon) {
          try {
            fitAddon.fit();
            sendResize();
          } catch (_) {}
        }
      }, 150);

      // Handle user key inputs directly in xterm canvas
      term.onData((data: string) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(data);
        }
      });

      const connectSocket = () => {
        if (isDisposed) return;
        setTermStatus('connecting');

        const host = window.location.hostname || '127.0.0.1';
        const wsUrl = `ws://${host}:8000/ws/terminal`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setTermStatus('connected');
          backoffSec = 1;
          setRetrySeconds(1);

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

      // ResizeObserver to automatically adapt xterm rows/cols
      if (terminalRef.current && typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver(() => {
          if (fitAddon) {
            try {
              fitAddon.fit();
              sendResize();
            } catch (_) {}
          }
        });
        resizeObserver.observe(terminalRef.current);
      }

      // Sahifa yopilganda PTY jarayonini to'liq yopish (zombie bo'lmasin)
      handleUnload = () => {
        try {
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'close' }));
          }
        } catch (_) {}
      };
      window.addEventListener('beforeunload', handleUnload);
    };

    initTerminal();

    return () => {
      isDisposed = true;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (pingInterval) clearInterval(pingInterval);
      if (resizeObserver) resizeObserver.disconnect();
      window.removeEventListener('beforeunload', handleUnload);
      if (wsRef.current) wsRef.current.close();
      if (term) term.dispose();
    };
  }, []);

  const handleClear = () => {
    if (xtermInstanceRef.current) {
      xtermInstanceRef.current.clear();
    }
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'clear' }));
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendCommand(inputCmd);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (history.length > 0) {
        const nextIdx = historyIndex === -1 ? history.length - 1 : Math.max(0, historyIndex - 1);
        setHistoryIndex(nextIdx);
        setInputCmd(history[nextIdx]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex !== -1) {
        const nextIdx = historyIndex + 1;
        if (nextIdx < history.length) {
          setHistoryIndex(nextIdx);
          setInputCmd(history[nextIdx]);
        } else {
          setHistoryIndex(-1);
          setInputCmd('');
        }
      }
    }
  };

  const focusTerminal = () => {
    if (xtermInstanceRef.current) {
      xtermInstanceRef.current.focus();
    }
  };

  return (
    <div className="flex-1 min-h-0 flex flex-col bg-[#090d16] border-b border-white/10 overflow-hidden font-mono">
      {/* Terminal Titlebar */}
      <div className="h-10 px-3 border-b border-white/10 flex items-center justify-between bg-slate-900/80 shrink-0">
        <div className="flex items-center space-x-2">
          <TerminalIcon className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-xs font-semibold text-slate-200 uppercase tracking-wide">
            {lang === 'uz' ? 'Agent terminali' : 'Agent Terminal'}
          </span>
          {/* Status Dot */}
          <span
            title={
              termStatus === 'connected'
                ? 'Terminal: Ulangan (127.0.0.1:8000)'
                : termStatus === 'connecting'
                ? `Qayta ulanmoqda (${retrySeconds}s)...`
                : 'Ulanish uzildi'
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
            onClick={() => sendCommand('conduit list')}
            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          >
            conduit list
          </button>
          <button
            onClick={() => sendCommand('conduit run scout "tools.py screenshot http://localhost:3000"')}
            className="px-2 py-0.5 rounded bg-blue-900/40 hover:bg-blue-800/60 text-blue-300 border border-blue-500/20 transition flex items-center space-x-1"
          >
            <Play className="w-2.5 h-2.5" />
            <span>run scout</span>
          </button>
          <button
            onClick={() => {
              if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: 'close' }));
              }
            }}
            className="p-1 rounded hover:bg-rose-900/40 text-slate-400 hover:text-rose-300 transition"
            title={lang === 'uz' ? 'Terminal sessiyasini to\u2018xtatish (PTY yopiladi)' : 'Stop terminal session (PTY closes)'}
          >
            <Power className="w-3 h-3" />
          </button>
          <button
            onClick={handleClear}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition"
            title="Tozalash"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* xterm.js interactive canvas area */}
      <div
        onClick={focusTerminal}
        className="flex-1 p-2 overflow-hidden relative cursor-text min-h-[160px]"
      >
        <div ref={terminalRef} className="w-full h-full" />
      </div>

      {/* Direct Interactive Command Input Bar */}
      <form
        onSubmit={handleFormSubmit}
        className="h-9 px-2.5 bg-slate-950/95 border-t border-white/10 flex items-center space-x-2 shrink-0"
      >
        <span className="text-emerald-400 font-bold text-xs select-none">$</span>
        <input
          type="text"
          value={inputCmd}
          onChange={(e) => setInputCmd(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            lang === 'uz'
              ? 'Buyruq kiriting (conduit list, dir, ...) va Enter bosing'
              : 'Enter command (conduit list, dir, ...) and press Enter'
          }
          className="flex-1 bg-transparent text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none font-mono"
        />
        <button
          type="submit"
          disabled={!inputCmd.trim()}
          className="px-2 py-1 text-[10px] rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-30 disabled:hover:bg-blue-600 text-white font-sans flex items-center space-x-1 transition"
          title="Yuborish"
        >
          <CornerDownLeft className="w-3 h-3" />
          <span>{lang === 'uz' ? 'Yuborish' : 'Send'}</span>
        </button>
      </form>
    </div>
  );
};
