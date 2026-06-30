import React, { useEffect, useState } from "react";
import { Link, useParams, useLocation, Outlet } from "react-router-dom";
import axios from "axios";
import { Guild } from "../types";
import { LayoutDashboard, Settings, Music, Shield, MessageSquare, Sparkles, Terminal, ChevronLeft, LogOut } from "lucide-react";

export default function DashboardLayout() {
  const { guildId } = useParams<{ guildId: string }>();
  const location = useLocation();
  const [activeGuild, setActiveGuild] = useState<Guild | null>(null);

  useEffect(() => {
    if (!guildId) return;
    axios.get("/api/guilds").then((res) => {
      const match = res.data.find((g: Guild) => g.id === guildId);
      if (match) setActiveGuild(match);
    });
  }, [guildId]);

  const links = [
    { to: `/guilds/${guildId}/overview`, label: "Overview", icon: LayoutDashboard },
    { to: `/guilds/${guildId}/settings`, label: "General Settings", icon: Settings },
    { to: `/guilds/${guildId}/music`, label: "Music Controller", icon: Music },
    { to: `/guilds/${guildId}/moderation`, label: "Moderation Cases", icon: Shield },
    { to: `/guilds/${guildId}/tickets`, label: "Support Tickets", icon: Shield },
    { to: `/guilds/${guildId}/welcome`, label: "Welcome Setup", icon: MessageSquare },
    { to: `/guilds/${guildId}/ai`, label: "AI Configuration", icon: Sparkles },
    { to: `/guilds/${guildId}/logs`, label: "Live logs Console", icon: Terminal }
  ];

  return (
    <div className="min-h-screen flex">
      {/* Sidebar Panel */}
      <aside className="w-64 bg-dark-800/80 border-r border-slate-800/40 backdrop-blur-md flex flex-col justify-between">
        <div className="flex flex-col">
          {/* Guild Profile Header */}
          <div className="p-6 border-b border-slate-800/30 flex items-center space-x-3">
            {activeGuild?.icon ? (
              <img src={activeGuild.icon} alt={activeGuild.name} className="w-10 h-10 rounded-xl" />
            ) : (
              <div className="w-10 h-10 rounded-xl bg-indigo-900/30 flex items-center justify-center font-bold text-indigo-400">
                {activeGuild?.name.charAt(0) || "S"}
              </div>
            )}
            <div className="flex flex-col min-w-0">
              <span className="font-semibold text-sm truncate text-slate-200">{activeGuild?.name || "Server"}</span>
              <span className="text-[10px] text-emerald-400 font-semibold tracking-wider uppercase">Online</span>
            </div>
          </div>

          {/* Sidebar Links */}
          <nav className="p-4 space-y-1">
            {links.map((link) => {
              const Icon = link.icon;
              const isActive = location.pathname === link.to;
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg text-sm transition-colors ${
                    isActive
                      ? "bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-600/10"
                      : "text-slate-400 hover:text-slate-200 hover:bg-dark-700/40"
                  }`}
                >
                  <Icon className="w-4.5 h-4.5" />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Back and Logout Actions */}
        <div className="p-4 border-t border-slate-800/30 space-y-1">
          <Link
            to="/guilds"
            className="flex items-center space-x-3 px-4 py-3 text-slate-400 hover:text-slate-200 hover:bg-dark-700/40 rounded-lg text-sm transition-colors"
          >
            <ChevronLeft className="w-4.5 h-4.5" />
            <span>Select Server</span>
          </Link>
          <button
            onClick={() => (window.location.href = "/api/auth/logout")}
            className="flex items-center space-x-3 px-4 py-3 text-slate-500 hover:text-rose-400 rounded-lg text-sm w-full transition-colors cursor-pointer"
          >
            <LogOut className="w-4.5 h-4.5" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Page Area */}
      <main className="flex-1 bg-dark-900/40 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
