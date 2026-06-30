import React from "react";
import { Shield, Sparkles, Music, Terminal } from "lucide-react";

export default function Landing() {
  const handleLogin = () => {
    window.location.href = "/api/auth/login";
  };

  return (
    <div className="min-h-screen flex flex-col justify-between items-center px-6 py-12 relative overflow-hidden">
      {/* Background glow animations */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl -z-10 animate-pulse"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl -z-10 animate-pulse delay-700"></div>

      {/* Header */}
      <div className="flex items-center space-x-3 mt-8">
        <div className="p-3 bg-gradient-to-tr from-indigo-500 to-violet-600 rounded-xl shadow-lg shadow-indigo-500/30">
          <Shield className="w-8 h-8 text-white" />
        </div>
        <span className="text-2xl font-bold tracking-wider bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
          NoSpaceFGK
        </span>
      </div>

      {/* Main Content */}
      <div className="max-w-2xl text-center flex flex-col items-center">
        <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight mb-6 bg-gradient-to-r from-white via-indigo-200 to-slate-400 bg-clip-text text-transparent">
          Control Your Discord Guild Remotely
        </h1>
        <p className="text-lg text-slate-400 max-w-lg mb-10 leading-relaxed">
          Manage dynamic AI behaviors, configure premium voice audio matching systems, enforce automod bans, and view system stats in real-time.
        </p>

        {/* Action Button */}
        <button
          onClick={handleLogin}
          className="flex items-center space-x-3 px-8 py-4 bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-semibold rounded-xl hover:from-indigo-500 hover:to-violet-500 transition-all duration-300 transform hover:scale-[1.03] shadow-xl shadow-indigo-600/20 cursor-pointer"
        >
          <Sparkles className="w-5 h-5" />
          <span>Login with Discord</span>
        </button>

        {/* Feature Grid */}
        <div className="grid grid-cols-3 gap-6 mt-16 max-w-xl w-full">
          <div className="flex flex-col items-center p-5 glass-panel">
            <Music className="w-6 h-6 text-indigo-400 mb-2" />
            <span className="text-sm font-semibold text-slate-300">Spotify Queue</span>
          </div>
          <div className="flex flex-col items-center p-5 glass-panel">
            <Shield className="w-6 h-6 text-emerald-400 mb-2" />
            <span className="text-sm font-semibold text-slate-300">Moderation</span>
          </div>
          <div className="flex flex-col items-center p-5 glass-panel">
            <Terminal className="w-6 h-6 text-violet-400 mb-2" />
            <span className="text-sm font-semibold text-slate-300">Live logs</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <span className="text-xs text-slate-600 mt-8">
        NoSpaceFGK Bot Dashboard &copy; 2026. Made with love.
      </span>
    </div>
  );
}
