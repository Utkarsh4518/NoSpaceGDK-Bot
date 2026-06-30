import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { Case } from "../types";
import { Shield, User, Calendar, Trash2 } from "lucide-react";

export default function Moderation() {
  const { guildId } = useParams<{ guildId: string }>();
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!guildId) return;
    axios
      .get(`/api/guilds/${guildId}/moderation`)
      .then((res) => {
        setCases(res.data.cases || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [guildId]);

  const getBadgeColor = (type: string) => {
    const t = type.toUpperCase();
    if (t.includes("BAN")) return "bg-rose-500/10 text-rose-400 border-rose-500/20";
    if (t.includes("KICK")) return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    if (t.includes("TIMEOUT")) return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
    if (t.includes("WARN")) return "bg-orange-500/10 text-orange-400 border-orange-500/20";
    return "bg-slate-500/10 text-slate-400 border-slate-500/20";
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
      <h2 className="text-2xl font-bold mb-2">Moderation Case Logs</h2>
      <p className="text-sm text-slate-400 mb-8">
        Inspect historical warning cases, bans, and timeout infractions logged by the bot.
      </p>

      <div className="glass-panel overflow-hidden border border-slate-800/40 rounded-xl shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800/40 bg-dark-800/40 text-xs text-slate-400 uppercase tracking-wider font-semibold">
                <th className="py-4 px-6">Case ID</th>
                <th className="py-4 px-6">Infraction Type</th>
                <th className="py-4 px-6">User Target</th>
                <th className="py-4 px-6">Moderator</th>
                <th className="py-4 px-6">Reason</th>
                <th className="py-4 px-6">Logged At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/30 text-sm">
              {cases.map((c) => (
                <tr key={c.id} className="hover:bg-dark-800/25 transition-colors">
                  <td className="py-4 px-6 font-semibold text-slate-400">#{c.id}</td>
                  <td className="py-4 px-6">
                    <span className={`px-2.5 py-1 text-xs rounded-full border ${getBadgeColor(c.type)}`}>
                      {c.type}
                    </span>
                  </td>
                  <td className="py-4 px-6 font-medium text-slate-300">
                    <div className="flex items-center space-x-2">
                      <User className="w-4 h-4 text-slate-500" />
                      <span>ID {c.user_id}</span>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-slate-400">ID {c.moderator_id}</td>
                  <td className="py-4 px-6 text-slate-300">{c.reason}</td>
                  <td className="py-4 px-6 text-slate-500 font-mono text-xs">
                    {new Date(c.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}

              {cases.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center py-20 text-slate-500">
                    No moderation cases recorded on this server.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
