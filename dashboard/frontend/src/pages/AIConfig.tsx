import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { AIConfig } from "../types";
import { Save, Cpu, ToggleLeft, ToggleRight } from "lucide-react";

export default function AIConfigPage() {
  const { guildId } = useParams<{ guildId: string }>();
  const [config, setConfig] = useState<AIConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!guildId) return;
    axios
      .get(`/api/guilds/${guildId}/ai`)
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

    // Filter list of disabled tool names
    const disabled_tools = config.tools.filter((t) => !t.enabled).map((t) => t.name);

    axios
      .post(`/api/guilds/${guildId}/ai`, {
        provider: config.current_provider,
        model: config.current_model,
        system_prompt: config.system_prompt,
        disabled_tools: disabled_tools
      })
      .then(() => {
        setSaving(false);
        setSuccess(true);
        setTimeout(() => setSuccess(false), 3000);
      })
      .catch(() => setSaving(false));
  };

  const handleToolToggle = (index: number) => {
    if (!config) return;
    const updatedTools = [...config.tools];
    updatedTools[index].enabled = !updatedTools[index].enabled;
    setConfig({ ...config, tools: updatedTools });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl grid grid-cols-1 md:grid-cols-3 gap-8">
      {/* Top Description */}
      <div className="md:col-span-3">
        <h2 className="text-2xl font-bold mb-2">AI Assistant Settings</h2>
        <p className="text-sm text-slate-400">
          Configure model providers, tweak system prompt templates, and control agent tool execution permissions.
        </p>

        {success && (
          <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl mt-6 text-sm">
            AI Configurations saved successfully! No bot restart required.
          </div>
        )}
      </div>

      {/* Main Parameters Panel */}
      <form onSubmit={handleSubmit} className="md:col-span-2 space-y-6">
        <div className="glass-panel p-6 space-y-5">
          <h3 className="text-lg font-bold flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-indigo-400" />
            <span>LLM Backend Config</span>
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col">
              <label className="text-xs text-slate-400 font-semibold mb-2">Active AI Provider</label>
              <select
                value={config?.current_provider || ""}
                onChange={(e) => setConfig({ ...config!, current_provider: e.target.value })}
                className="px-4 py-3 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 text-sm"
              >
                {config?.providers.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col">
              <label className="text-xs text-slate-400 font-semibold mb-2">Model Name</label>
              <input
                type="text"
                value={config?.current_model || ""}
                onChange={(e) => setConfig({ ...config!, current_model: e.target.value })}
                placeholder="e.g. gemini-1.5-flash"
                className="px-4 py-3 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 text-sm"
              />
            </div>
          </div>

          <div className="flex flex-col">
            <label className="text-xs text-slate-400 font-semibold mb-2">System Instructions Prompt</label>
            <textarea
              value={config?.system_prompt || ""}
              onChange={(e) => setConfig({ ...config!, system_prompt: e.target.value })}
              rows={6}
              className="px-4 py-3 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500 text-sm"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="flex items-center justify-center space-x-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-semibold rounded-lg transition-colors cursor-pointer"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? "Saving Configuration..." : "Save Config"}</span>
        </button>
      </form>

      {/* Tool Manager sidebar */}
      <div className="glass-panel p-6 flex flex-col h-[500px]">
        <h3 className="text-lg font-bold mb-2">Agent Tools</h3>
        <p className="text-xs text-slate-400 mb-4">Toggle function calling permissions.</p>

        <div className="flex-1 overflow-y-auto space-y-4 pr-1">
          {config?.tools.map((t, idx) => (
            <div key={t.name} className="flex justify-between items-start p-3 bg-dark-900/50 rounded-lg border border-slate-800/25">
              <div className="flex-1 min-w-0 pr-3">
                <div className="text-sm font-semibold text-slate-200 truncate">{t.name}</div>
                <div className="text-xs text-slate-500 line-clamp-2 mt-0.5">{t.description}</div>
              </div>
              <button
                type="button"
                onClick={() => handleToolToggle(idx)}
                className="text-slate-400 hover:text-white transition-colors cursor-pointer"
              >
                {t.enabled ? (
                  <ToggleRight className="w-7 h-7 text-emerald-400" />
                ) : (
                  <ToggleLeft className="w-7 h-7 text-slate-600" />
                )}
              </button>
            </div>
          ))}

          {(!config || config.tools.length === 0) && (
            <div className="text-center py-20 text-xs text-slate-500">No agent tools registered.</div>
          )}
        </div>
      </div>
    </div>
  );
}
