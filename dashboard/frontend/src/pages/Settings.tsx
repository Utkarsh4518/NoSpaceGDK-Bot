import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { GuildSettings } from "../types";
import { Save, AlertCircle } from "lucide-react";

export default function Settings() {
  const { guildId } = useParams<{ guildId: string }>();
  const [settings, setSettings] = useState<GuildSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!guildId) return;
    axios
      .get(`/api/guilds/${guildId}/settings`)
      .then((res) => {
        setSettings(res.data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [guildId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!guildId || !settings) return;
    setSaving(true);
    setSuccess(false);

    axios
      .post(`/api/guilds/${guildId}/settings`, settings)
      .then(() => {
        setSaving(false);
        setSuccess(true);
        setTimeout(() => setSuccess(false), 3000);
      })
      .catch(() => setSaving(false));
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!settings) return;
    const { name, value } = e.target;
    setSettings({
      ...settings,
      [name]: name.includes("limit") || name.includes("seconds") ? parseInt(value) || 0 : value
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
    <div className="p-8 max-w-2xl">
      <h2 className="text-2xl font-bold mb-2">Guild Settings</h2>
      <p className="text-sm text-slate-400 mb-8">
        Manage timeouts, warnings ceilings, roles mapping, and channel targets.
      </p>

      {success && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl mb-6 flex items-center space-x-2 text-sm">
          <span>Settings saved successfully!</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-2 gap-6">
          <div className="flex flex-col">
            <label className="text-xs text-slate-400 font-semibold mb-2">Default Timeout (seconds)</label>
            <input
              type="number"
              name="default_timeout_seconds"
              value={settings?.default_timeout_seconds || 3600}
              onChange={handleInputChange}
              className="px-4 py-3 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex flex-col">
            <label className="text-xs text-slate-400 font-semibold mb-2">Warning Limit Max</label>
            <input
              type="number"
              name="default_warning_limit"
              value={settings?.default_warning_limit || 3}
              onChange={handleInputChange}
              className="px-4 py-3 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="flex flex-col">
          <label className="text-xs text-slate-400 font-semibold mb-2">Audit Logs Target Channel ID</label>
          <input
            type="text"
            name="audit_channel_id"
            value={settings?.audit_channel_id || ""}
            onChange={handleInputChange}
            placeholder="e.g. 123456789012345678"
            className="px-4 py-3 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex flex-col">
          <label className="text-xs text-slate-400 font-semibold mb-2">Moderator Roles Names (comma separated)</label>
          <input
            type="text"
            name="moderator_roles"
            value={settings?.moderator_roles || ""}
            onChange={handleInputChange}
            placeholder="e.g. Admin, Moderator, Staff"
            className="px-4 py-3 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex flex-col">
          <label className="text-xs text-slate-400 font-semibold mb-2">Protected Roles Names (comma separated)</label>
          <input
            type="text"
            name="protected_roles"
            value={settings?.protected_roles || ""}
            onChange={handleInputChange}
            placeholder="e.g. VIP, Owner, Helper"
            className="px-4 py-3 bg-dark-900 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <button
          type="submit"
          disabled={saving}
          className="flex items-center justify-center space-x-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-semibold rounded-lg transition-colors cursor-pointer w-full sm:w-auto"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? "Saving Changes..." : "Save Settings"}</span>
        </button>
      </form>
    </div>
  );
}
