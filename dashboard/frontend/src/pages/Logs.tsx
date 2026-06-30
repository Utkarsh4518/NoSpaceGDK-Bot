import React, { useEffect, useState, useRef } from "react";
import { LogEntry } from "../types";
import { Terminal, Download, Trash2, Filter } from "lucide-react";

interface LogsProps {
  logs: LogEntry[];
  clearLogs: () => void;
}

export default function Logs({ logs, clearLogs }: LogsProps) {
  const [filterLevel, setFilterLevel] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const terminalEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom of logs on new entries
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const filteredLogs = logs.filter((log) => {
    const levelMatch = filterLevel === "ALL" || log.level.toUpperCase() === filterLevel;
    const searchMatch =
      !searchQuery ||
      log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.logger.toLowerCase().includes(searchQuery.toLowerCase());
    return levelMatch && searchMatch;
  });

  const getLogColor = (level: string) => {
    const l = level.toUpperCase();
    if (l === "ERROR" || l === "CRITICAL") return "text-rose-400";
    if (l === "WARNING") return "text-amber-400";
    if (l === "DEBUG") return "text-slate-500";
    return "text-slate-300";
  };

  const handleExport = () => {
    const text = logs
      .map((l) => `[${new Date(l.timestamp * 1000).toISOString()}] [${l.level}] [${l.logger}]: ${l.message}`)
      .join("\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `bot_logs_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-8 max-w-5xl flex flex-col h-[calc(100vh-100px)]">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold mb-2">Live Log Stream</h2>
          <p className="text-sm text-slate-400">
            Real-time stdout console feed from the running bot instance.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-3">
          <button
            onClick={handleExport}
            className="flex items-center space-x-2 px-4 py-2 bg-dark-700 hover:bg-dark-600 border border-slate-800 text-sm text-slate-200 rounded-lg transition-colors cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>Export Logs</span>
          </button>
          <button
            onClick={clearLogs}
            className="flex items-center space-x-2 px-4 py-2 bg-rose-950/15 hover:bg-rose-950/35 border border-rose-500/10 text-sm text-rose-400 rounded-lg transition-colors cursor-pointer"
          >
            <Trash2 className="w-4 h-4" />
            <span>Clear Screen</span>
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4 mb-4">
        <div className="w-40 relative">
          <Filter className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
          <select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 text-xs uppercase"
          >
            <option value="ALL">All Levels</option>
            <option value="INFO">Info</option>
            <option value="WARNING">Warning</option>
            <option value="ERROR">Error</option>
            <option value="DEBUG">Debug</option>
          </select>
        </div>

        <div className="flex-1">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search console logs by matching text pattern..."
            className="w-full px-4 py-2.5 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 placeholder-slate-500 text-xs"
          />
        </div>
      </div>

      {/* Console Window */}
      <div className="flex-1 bg-black border border-slate-900/60 rounded-xl p-5 font-mono text-xs overflow-y-auto shadow-2xl relative">
        <div className="absolute top-4 right-4 flex items-center space-x-2 text-rose-500 text-[10px] uppercase font-semibold">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
          <span>Live Console Stream</span>
        </div>
        <div className="space-y-1.5">
          {filteredLogs.map((log, idx) => (
            <div key={idx} className="leading-5 flex items-start break-all">
              <span className="text-slate-600 select-none mr-3">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
              <span className={`font-bold mr-3 select-none uppercase ${getLogColor(log.level)}`}>[{log.level}]</span>
              <span className="text-indigo-400/80 mr-2 select-none">[{log.logger}]:</span>
              <span className="text-slate-300">{log.message}</span>
            </div>
          ))}

          {filteredLogs.length === 0 && (
            <div className="text-center py-20 text-slate-600">No log entries matched current criteria.</div>
          )}

          <div ref={terminalEndRef} />
        </div>
      </div>
    </div>
  );
}
