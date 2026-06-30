import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { PlaybackState } from "../types";
import { Play, Pause, SkipForward, Square, Search, Music as MusicIcon, Trash2 } from "lucide-react";

export default function Music() {
  const { guildId } = useParams<{ guildId: string }>();
  const [playback, setPlayback] = useState<PlaybackState | null>(null);
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchPlaybackState = () => {
    if (!guildId) return;
    axios
      .get(`/api/guilds/${guildId}/music/state`)
      .then((res) => {
        setPlayback(res.data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchPlaybackState();
    const interval = setInterval(fetchPlaybackState, 3000);
    return () => clearInterval(interval);
  }, [guildId]);

  const handleControl = (action: "pause" | "resume" | "skip" | "stop") => {
    if (!guildId) return;
    axios.post(`/api/guilds/${guildId}/music/${action}`).then(() => fetchPlaybackState());
  };

  const handlePlaySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!guildId || !query) return;
    setSearching(true);

    axios
      .post(`/api/guilds/${guildId}/music/play`, { query })
      .then(() => {
        setQuery("");
        setSearching(false);
        fetchPlaybackState();
      })
      .catch((err) => {
        setSearching(false);
        alert(err.response?.data?.detail || "Failed to search/play song.");
      });
  };

  const handleRemoveTrack = (uuid: string) => {
    if (!guildId) return;
    axios
      .post(`/api/guilds/${guildId}/music/remove`, { target: uuid })
      .then(() => fetchPlaybackState());
  };

  const formatDuration = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const isPlaying = playback?.state === "PLAYING";

  return (
    <div className="p-8 max-w-4xl grid grid-cols-1 md:grid-cols-3 gap-8">
      {/* Search & Controller section */}
      <div className="md:col-span-2 space-y-6">
        <h2 className="text-2xl font-bold mb-4">Music Controller</h2>

        {/* Current Song Panel */}
        <div className="glass-panel p-6 flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-6">
          {playback?.current?.track.thumbnail ? (
            <img
              src={playback.current.track.thumbnail}
              alt={playback.current.track.title}
              className="w-32 h-32 rounded-xl object-cover shadow-lg shadow-black/40"
            />
          ) : (
            <div className="w-32 h-32 rounded-xl bg-indigo-950/20 flex items-center justify-center text-indigo-400">
              <MusicIcon className="w-12 h-12" />
            </div>
          )}

          <div className="flex-1 text-center sm:text-left">
            <span className="text-xs text-indigo-400 font-semibold tracking-wider uppercase">
              {playback?.state || "IDLE"}
            </span>
            <h3 className="text-xl font-bold text-slate-100 mt-1 line-clamp-2">
              {playback?.current?.track.title || "No track currently playing"}
            </h3>
            {playback?.current && (
              <div className="text-xs text-slate-400 mt-2">
                Requested by: <span className="text-slate-300">ID {playback.current.added_by}</span>
              </div>
            )}

            {/* Playback Controls */}
            <div className="flex items-center justify-center sm:justify-start space-x-4 mt-6">
              {isPlaying ? (
                <button
                  onClick={() => handleControl("pause")}
                  className="p-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full transition-colors cursor-pointer"
                >
                  <Pause className="w-5 h-5" />
                </button>
              ) : (
                <button
                  onClick={() => handleControl("resume")}
                  className="p-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full transition-colors cursor-pointer"
                >
                  <Play className="w-5 h-5" />
                </button>
              )}

              <button
                onClick={() => handleControl("skip")}
                className="p-3 bg-dark-700 hover:bg-dark-600 border border-slate-800 text-slate-200 rounded-full transition-colors cursor-pointer"
              >
                <SkipForward className="w-5 h-5" />
              </button>

              <button
                onClick={() => handleControl("stop")}
                className="p-3 bg-dark-700 hover:bg-dark-600 border border-slate-800 text-slate-200 rounded-full transition-colors cursor-pointer"
              >
                <Square className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Play search query form */}
        <form onSubmit={handlePlaySubmit} className="flex items-center space-x-3">
          <div className="flex-1 relative">
            <Search className="w-5 h-5 text-slate-500 absolute left-4 top-3.5" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search track title or paste YouTube/Spotify url..."
              className="w-full pl-12 pr-4 py-3.5 bg-dark-900 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:border-indigo-500 placeholder-slate-500 text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={searching}
            className="px-6 py-3.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-semibold rounded-xl transition-colors cursor-pointer text-sm"
          >
            {searching ? "Searching..." : "Play"}
          </button>
        </form>
      </div>

      {/* Queue list section */}
      <div className="glass-panel p-6 flex flex-col h-[400px] md:h-auto">
        <h3 className="text-lg font-bold mb-4">Playback Queue</h3>
        <div className="flex-1 overflow-y-auto space-y-3 pr-2">
          {playback?.queue.map((item, idx) => (
            <div
              key={item.uuid}
              className="flex justify-between items-center p-3 bg-dark-900/50 hover:bg-dark-900 rounded-lg border border-slate-800/20 group"
            >
              <div className="flex-1 min-w-0 pr-3">
                <div className="text-xs text-slate-500 font-semibold mb-0.5">#{idx + 1}</div>
                <div className="text-sm font-medium text-slate-300 truncate">{item.track.title}</div>
                <div className="text-xs text-slate-500">{formatDuration(item.track.duration)}</div>
              </div>
              <button
                onClick={() => handleRemoveTrack(item.uuid)}
                className="text-slate-500 hover:text-rose-400 p-1 opacity-0 group-hover:opacity-100 transition-all cursor-pointer"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}

          {(!playback || playback.queue.length === 0) && (
            <div className="text-center py-20 text-xs text-slate-500">Queue is empty.</div>
          )}
        </div>
      </div>
    </div>
  );
}
