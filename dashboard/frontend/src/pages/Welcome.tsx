import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { WelcomeSettings } from "../types";
import { Save, Sparkles, MessageSquare } from "lucide-react";

export default function Welcome() {
  const { guildId } = useParams<{ guildId: string }>();
  const [config, setConfig] = useState<WelcomeSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!guildId) return;
    axios
      .get(`/api/guilds/${guildId}/welcome`)
      .then((res) => {
        setConfig(res.data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [guildId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!guildId || !config) return;
    setSaving(true);
    setSuccess(false);

    axios
      .post(`/api/guilds/${guildId}/welcome`, config)
      .then(() => {
        setSaving(false);
        setSuccess(true);
        setTimeout(() => setSuccess(false), 3000);
      })
      .catch(() => setSaving(false));
  };

  const handleInputChange = (section: "welcome" | "goodbye", name: string, value: any) => {
    if (!config) return;
    setConfig({
      ...config,
      [section]: {
        ...config[section],
        [name]: value
      }
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-8">
      <div className="md:col-span-2">
        <h2 className="text-2xl font-bold mb-2">Welcome & Goodbye Setup</h2>
        <p className="text-sm text-slate-400 mb-6">
          Customize announcements when members join or leave your guild.
        </p>

        {success && (
          <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl mb-6 text-sm">
            Welcome configurations saved successfully!
          </div>
        )}
      </div>

      {/* Welcome Setup */}
      <div className="glass-panel p-6 space-y-5">
        <h3 className="text-lg font-bold flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-indigo-400" />
          <span>Member Join Announcements</span>
        </h3>

        <div className="flex items-center justify-between">
          <label className="text-sm text-slate-300 font-semibold">Enable Welcome Messages</label>
          <input
            type="checkbox"
            checked={config?.welcome.enabled || false}
            onChange={(e) => handleInputChange("welcome", "enabled", e.target.checked)}
            className="w-5 h-5 accent-indigo-600 rounded"
          />
        </div>

        <div className="flex items-center justify-between">
          <label className="text-sm text-slate-300 font-semibold">Enable DM Messages</label>
          <input
            type="checkbox"
            checked={config?.welcome.dm_enabled || false}
            onChange={(e) => handleInputChange("welcome", "dm_enabled", e.target.checked)}
            className="w-5 h-5 accent-indigo-600 rounded"
          />
        </div>

        <div className="flex flex-col">
          <label className="text-xs text-slate-400 font-semibold mb-2">Announcement Channel ID</label>
          <input
            type="text"
            value={config?.welcome.channel_id || ""}
            onChange={(e) => handleInputChange("welcome", "channel_id", e.target.value)}
            placeholder="e.g. 123456789012345678"
            className="px-4 py-3 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 text-sm"
          />
        </div>

        <div className="flex flex-col">
          <label className="text-xs text-slate-400 font-semibold mb-2">Message Text</label>
          <textarea
            value={config?.welcome.message_text || ""}
            onChange={(e) => handleInputChange("welcome", "message_text", e.target.value)}
            placeholder="Welcome {user} to {server}!"
            rows={3}
            className="px-4 py-3 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 text-sm"
          />
        </div>

        <div className="flex flex-col">
          <label className="text-xs text-slate-400 font-semibold mb-2">Custom Embed JSON (Optional)</label>
          <textarea
            value={config?.welcome.embed_json || ""}
            onChange={(e) => handleInputChange("welcome", "embed_json", e.target.value)}
            placeholder='{"title": "Welcome!"}'
            rows={3}
            className="px-4 py-3 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 font-mono text-xs"
          />
        </div>
      </div>

      {/* Goodbye Setup */}
      <div className="glass-panel p-6 space-y-5">
        <h3 className="text-lg font-bold flex items-center space-x-2">
          <MessageSquare className="w-5 h-5 text-rose-400" />
          <span>Member Leave Announcements</span>
        </h3>

        <div className="flex items-center justify-between">
          <label className="text-sm text-slate-300 font-semibold">Enable Goodbye Messages</label>
          <input
            type="checkbox"
            checked={config?.goodbye.enabled || false}
            onChange={(e) => handleInputChange("goodbye", "enabled", e.target.checked)}
            className="w-5 h-5 accent-indigo-600 rounded"
          />
        </div>

        <div className="flex flex-col">
          <label className="text-xs text-slate-400 font-semibold mb-2">Announcement Channel ID</label>
          <input
            type="text"
            value={config?.goodbye.channel_id || ""}
            onChange={(e) => handleInputChange("goodbye", "channel_id", e.target.value)}
            placeholder="e.g. 123456789012345678"
            className="px-4 py-3 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 text-sm"
          />
        </div>

        <div className="flex flex-col">
          <label className="text-xs text-slate-400 font-semibold mb-2">Message Text</label>
          <textarea
            value={config?.goodbye.message_text || ""}
            onChange={(e) => handleInputChange("goodbye", "message_text", e.target.value)}
            placeholder="{username} left the server."
            rows={3}
            className="px-4 py-3 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 text-sm"
          />
        </div>

        <div className="flex flex-col">
          <label className="text-xs text-slate-400 font-semibold mb-2">Custom Embed JSON (Optional)</label>
          <textarea
            value={config?.goodbye.embed_json || ""}
            onChange={(e) => handleInputChange("goodbye", "embed_json", e.target.value)}
            placeholder='{"title": "Goodbye!"}'
            rows={3}
            className="px-4 py-3 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 font-mono text-xs"
          />
        </div>
      </div>

      <div className="md:col-span-2">
        <button
          onClick={handleSubmit}
          disabled={saving}
          className="flex items-center justify-center space-x-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-semibold rounded-lg transition-colors cursor-pointer w-full sm:w-auto"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? "Saving Configurations..." : "Save Config"}</span>
        </button>
      </div>
    </div>
  );
}
