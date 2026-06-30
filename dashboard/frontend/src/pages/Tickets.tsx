import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { Ticket } from "../types";
import { ShieldAlert, CheckCircle, Clock, ExternalLink, MessageSquare } from "lucide-react";

export default function Tickets() {
  const { guildId } = useParams<{ guildId: string }>();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!guildId) return;
    axios
      .get(`/api/guilds/${guildId}/tickets`)
      .then((res) => {
        setTickets(res.data.tickets || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [guildId]);

  const getStatusBadge = (status: string) => {
    const s = status.toUpperCase();
    if (s === "OPEN") {
      return (
        <span className="flex items-center space-x-1 px-2.5 py-1 text-xs rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-400">
          <Clock className="w-3.5 h-3.5" />
          <span>Open</span>
        </span>
      );
    }
    return (
      <span className="flex items-center space-x-1 px-2.5 py-1 text-xs rounded-full border border-slate-500/20 bg-slate-500/10 text-slate-400">
        <CheckCircle className="w-3.5 h-3.5" />
        <span>Closed</span>
      </span>
    );
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
      <h2 className="text-2xl font-bold mb-2">Support Tickets</h2>
      <p className="text-sm text-slate-400 mb-8">
        Review current user support tickets and access transcripts logs.
      </p>

      <div className="glass-panel overflow-hidden border border-slate-800/40 rounded-xl shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800/40 bg-dark-800/40 text-xs text-slate-400 uppercase tracking-wider font-semibold">
                <th className="py-4 px-6">Ticket ID</th>
                <th className="py-4 px-6">Creator User ID</th>
                <th className="py-4 px-6">Topic / Category</th>
                <th className="py-4 px-6">Status</th>
                <th className="py-4 px-6">Claimed By</th>
                <th className="py-4 px-6">Created At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/30 text-sm">
              {tickets.map((t) => (
                <tr key={t.id} className="hover:bg-dark-800/25 transition-colors">
                  <td className="py-4 px-6 font-semibold text-indigo-400">#{t.id}</td>
                  <td className="py-4 px-6 text-slate-300">ID {t.creator_id}</td>
                  <td className="py-4 px-6 text-slate-300 font-medium">{t.topic || "General support"}</td>
                  <td className="py-4 px-6">{getStatusBadge(t.status)}</td>
                  <td className="py-4 px-6 text-slate-400">
                    {t.claimed_by ? `ID ${t.claimed_by}` : <span className="text-slate-600 text-xs italic">Unassigned</span>}
                  </td>
                  <td className="py-4 px-6 text-slate-500 font-mono text-xs">
                    {new Date(t.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}

              {tickets.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center py-20 text-slate-500">
                    No tickets opened on this server.
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
