import React, { useEffect, useState } from "react";
import axios from "axios";
import { SystemStats } from "../types";
import { Server, Users, Activity, Clock, Terminal } from "lucide-react";

export default function Overview() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = () => {
    axios
      .get("/api/stats")
      .then((res) => {
        setStats(res.data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const formatUptime = (sec: number) => {
    const hrs = Math.floor(sec / 3600);
    const mins = Math.floor((sec % 3600) / 60);
    return `${hrs}h ${mins}m`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl">
      <h2 className="text-2xl font-bold mb-6">Dashboard Overview</h2>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 mb-8">
        <div className="p-6 glass-panel flex items-center space-x-4">
          <div className="p-3 bg-indigo-500/10 rounded-lg text-indigo-400">
            <Server className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-extrabold">{stats?.guild_count}</div>
            <div className="text-xs text-slate-400">Server Count</div>
          </div>
        </div>

        <div className="p-6 glass-panel flex items-center space-x-4">
          <div className="p-3 bg-violet-500/10 rounded-lg text-violet-400">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-extrabold">{stats?.user_count}</div>
            <div className="text-xs text-slate-400">Total Users</div>
          </div>
        </div>

        <div className="p-6 glass-panel flex items-center space-x-4">
          <div className="p-3 bg-emerald-500/10 rounded-lg text-emerald-400">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-extrabold">{stats?.latency_ms} ms</div>
            <div className="text-xs text-slate-400">API Latency</div>
          </div>
        </div>

        <div className="p-6 glass-panel flex items-center space-x-4">
          <div className="p-3 bg-rose-500/10 rounded-lg text-rose-400">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-extrabold">
              {stats ? formatUptime(stats.uptime_seconds) : "0h 0m"}
            </div>
            <div className="text-xs text-slate-400">Uptime</div>
          </div>
        </div>
      </div>

      {/* System Specs panel */}
      <div className="glass-panel p-6 mb-8">
        <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
          <Terminal className="w-5 h-5 text-indigo-400" />
          <span>System Specifications</span>
        </h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex justify-between p-3 bg-dark-900/50 rounded-lg border border-slate-800/30">
            <span className="text-slate-400">Platform OS</span>
            <span className="font-semibold text-slate-200">{stats?.platform}</span>
          </div>
          <div className="flex justify-between p-3 bg-dark-900/50 rounded-lg border border-slate-800/30">
            <span className="text-slate-400">Python Version</span>
            <span className="font-semibold text-slate-200">{stats?.python_version}</span>
          </div>
          <div className="flex justify-between p-3 bg-dark-900/50 rounded-lg border border-slate-800/30">
            <span className="text-slate-400">Active Music Stream Players</span>
            <span className="font-semibold text-slate-200">{stats?.active_music_players}</span>
          </div>
          <div className="flex justify-between p-3 bg-dark-900/50 rounded-lg border border-slate-800/30">
            <span className="text-slate-400">Bot Heartbeat State</span>
            <span className="font-semibold text-emerald-400">ACTIVE</span>
          </div>
        </div>
      </div>
    </div>
  );
}
