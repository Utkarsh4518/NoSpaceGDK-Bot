import React, { useEffect, useState } from "react";
import axios from "axios";
import { Guild } from "../types";
import { LogOut, ArrowRight, Shield } from "lucide-react";

export default function GuildSelect() {
  const [guilds, setGuilds] = useState<Guild[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get("/api/guilds")
      .then((res) => {
        setGuilds(res.data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleGuildClick = (guild: Guild) => {
    if (guild.bot_present) {
      window.location.href = `/guilds/${guild.id}/overview`;
    } else {
      // Invite Bot
      window.open(
        `https://discord.com/api/oauth2/authorize?client_id=${import.meta.env.VITE_DISCORD_CLIENT_ID || ""}&permissions=8&scope=bot%20applications.commands&guild_id=${guild.id}`,
        "_blank"
      );
    }
  };

  const handleLogout = () => {
    window.location.href = "/api/auth/logout";
  };

  return (
    <div className="min-h-screen py-16 px-6 max-w-4xl mx-auto flex flex-col">
      {/* Top Header */}
      <div className="flex justify-between items-center mb-12">
        <div className="flex items-center space-x-3">
          <Shield className="w-7 h-7 text-indigo-500" />
          <span className="text-xl font-bold tracking-wider">NoSpaceFGK</span>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center space-x-2 text-sm text-slate-400 hover:text-white transition-colors cursor-pointer"
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </button>
      </div>

      <h2 className="text-3xl font-extrabold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400">
        Select a Server
      </h2>
      <p className="text-sm text-slate-400 mb-8">
        Configure AI assistant parameters and moderation settings.
      </p>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <span className="text-sm text-slate-400">Fetching servers list...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {guilds.map((g) => (
            <div
              key={g.id}
              onClick={() => handleGuildClick(g)}
              className="flex justify-between items-center p-5 glass-panel hover:bg-dark-800/90 transition-all duration-300 transform hover:scale-[1.01] cursor-pointer group"
            >
              <div className="flex items-center space-x-4">
                {g.icon ? (
                  <img src={g.icon} alt={g.name} className="w-12 h-12 rounded-xl object-cover" />
                ) : (
                  <div className="w-12 h-12 rounded-xl bg-indigo-900/30 flex items-center justify-center font-bold text-indigo-400">
                    {g.name.charAt(0)}
                  </div>
                )}
                <div className="flex flex-col">
                  <span className="font-semibold text-slate-200 group-hover:text-white transition-colors">
                    {g.name}
                  </span>
                  <span className="text-xs text-slate-500">
                    {g.permissions}
                  </span>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {g.bot_present ? (
                  <div className="flex items-center space-x-2 text-emerald-400 font-medium text-xs bg-emerald-500/10 px-3 py-1.5 rounded-lg">
                    <span>Manage</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </div>
                ) : (
                  <span className="text-xs text-indigo-400 bg-indigo-500/10 hover:bg-indigo-500/20 px-3 py-1.5 rounded-lg transition-colors">
                    Invite Bot
                  </span>
                )}
              </div>
            </div>
          ))}

          {guilds.length === 0 && (
            <div className="col-span-2 text-center py-20 text-slate-500">
              No manageable servers found. Make sure you are an administrator.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
