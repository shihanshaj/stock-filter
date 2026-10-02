"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Settings, Category } from "@/lib/types";

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getSettings().then(setSettings).catch(() => {
      setSettings({
        screenerUrl: "",
        cacheDuration: 24,
        categories: [Category.AVERAGE_DISCOUNTED, Category.AVERAGE_ATTRACTIVE, Category.HIGH_ATTRACTIVE, Category.HIGH_HIGH_VALUATION]
      });
    });
  }, []);

  const handleSave = async () => {
    if (!settings) return;
    try {
      setSaving(true);
      await api.updateSettings(settings);
      alert("Settings saved!");
    } catch (e) {
      alert("Failed to save");
    } finally {
      setSaving(false);
    }
  };

  if (!settings) return <div className="text-center py-10">Loading settings...</div>;

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>
      
      <div className="space-y-6 bg-card border rounded-lg p-6 shadow-sm">
        <div>
          <label className="block text-sm font-medium mb-2">Chartink Screener URL</label>
          <input 
            type="url" 
            value={settings.screenerUrl} 
            onChange={e => setSettings({...settings, screenerUrl: e.target.value})}
            className="w-full px-3 py-2 border rounded-md dark:bg-slate-900"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-2">Cache Duration (hours)</label>
          <input 
            type="number" 
            value={settings.cacheDuration} 
            onChange={e => setSettings({...settings, cacheDuration: Number(e.target.value)})}
            className="w-full px-3 py-2 border rounded-md dark:bg-slate-900"
          />
        </div>
        
        <button 
          onClick={handleSave} 
          disabled={saving}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-md transition-colors"
        >
          {saving ? "Saving..." : "Save Settings"}
        </button>
      </div>
    </div>
  );
}
