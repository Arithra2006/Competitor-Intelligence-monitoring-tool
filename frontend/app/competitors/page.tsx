"use client";

import { useEffect, useState } from "react";
import { Building2, Trash2, Plus, ArrowLeft, RefreshCw } from "lucide-react";
import Link from "next/link";

const API = "http://localhost:8000/api";

interface Competitor {
  id: number;
  name: string;
  website_url: string;
  careers_url: string | null;
  github_org: string | null;
  reddit_keyword: string | null;
  frequency: string;
  created_at: string;
}

export default function CompetitorsPage() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [running, setRunning] = useState<number | null>(null);
  const [form, setForm] = useState({
    name: "",
    website_url: "",
    careers_url: "",
    github_org: "",
    reddit_keyword: "",
    frequency: "weekly",
  });

  const fetchCompetitors = async () => {
    try {
      const res = await fetch(`${API}/competitors`);
      const json = await res.json();
      setCompetitors(json.competitors);
    } catch (e) {
      console.error("Failed to fetch competitors:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompetitors();
  }, []);

  const handleSubmit = async () => {
    if (!form.name || !form.website_url) {
      alert("Name and website URL are required");
      return;
    }
    try {
      const res = await fetch(`${API}/competitors`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name,
          website_url: form.website_url,
          careers_url: form.careers_url || null,
          github_org: form.github_org || null,
          reddit_keyword: form.reddit_keyword || null,
          frequency: form.frequency,
        }),
      });
      if (res.ok) {
        setForm({
          name: "",
          website_url: "",
          careers_url: "",
          github_org: "",
          reddit_keyword: "",
          frequency: "weekly",
        });
        setShowForm(false);
        fetchCompetitors();
      }
    } catch (e) {
      alert("Failed to add competitor");
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Remove ${name} from tracking?`)) return;
    setDeleting(id);
    try {
      await fetch(`${API}/competitors/${id}`, { method: "DELETE" });
      fetchCompetitors();
    } catch (e) {
      alert("Failed to delete competitor");
    } finally {
      setDeleting(null);
    }
  };

  const handleRun = async (id: number, name: string) => {
    setRunning(id);
    try {
      await fetch(`${API}/run/${id}`, { method: "POST" });
      alert(`✅ Pipeline started for ${name}! Takes a few minutes to complete.`);
    } catch (e) {
      alert("Failed to start pipeline");
    } finally {
      setRunning(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Competitor Intelligence</h1>
              <p className="text-xs text-gray-400">Autonomous monitoring pipeline</p>
            </div>
          </div>
          <nav className="flex items-center gap-6 text-sm">
            <Link href="/" className="text-gray-400 hover:text-white transition">Dashboard</Link>
            <Link href="/competitors" className="text-blue-400 font-medium">Competitors</Link>
            <Link href="/reports" className="text-gray-400 hover:text-white transition">Reports</Link>
            <Link href="/trends" className="text-gray-400 hover:text-white transition">Trends</Link>
            <Link href="/battlecards" className="text-gray-400 hover:text-white transition">Battlecards</Link>
            <Link href="/timeline" className="text-gray-400 hover:text-white transition">Timeline</Link>
            <Link href="/activity" className="text-gray-400 hover:text-white transition">Activity</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Page header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-gray-400 hover:text-white transition">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h2 className="text-2xl font-bold text-white">Competitors</h2>
              <p className="text-gray-400 text-sm">Manage your tracked competitors</p>
            </div>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition"
          >
            <Plus className="w-4 h-4" />
            Add Competitor
          </button>
        </div>

        {/* Add competitor form */}
        {showForm && (
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 mb-6">
            <h3 className="text-lg font-bold mb-4">Add New Competitor</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-400 mb-1 block">
                  Company Name *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Linear"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 mb-1 block">
                  Website URL *
                </label>
                <input
                  type="text"
                  placeholder="https://linear.app"
                  value={form.website_url}
                  onChange={(e) => setForm({ ...form, website_url: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 mb-1 block">
                  Careers Page URL
                </label>
                <input
                  type="text"
                  placeholder="https://linear.app/careers"
                  value={form.careers_url}
                  onChange={(e) => setForm({ ...form, careers_url: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 mb-1 block">
                  GitHub Org
                </label>
                <input
                  type="text"
                  placeholder="e.g. linear"
                  value={form.github_org}
                  onChange={(e) => setForm({ ...form, github_org: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 mb-1 block">
                  Reddit Keyword
                </label>
                <input
                  type="text"
                  placeholder="e.g. Linear app"
                  value={form.reddit_keyword}
                  onChange={(e) => setForm({ ...form, reddit_keyword: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 mb-1 block">
                  Frequency
                </label>
                <select
                  value={form.frequency}
                  onChange={(e) => setForm({ ...form, frequency: e.target.value })}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
            </div>
            <div className="flex gap-3 mt-4">
              <button
                onClick={handleSubmit}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg text-sm transition"
              >
                Add Competitor
              </button>
              <button
                onClick={() => setShowForm(false)}
                className="bg-gray-700 hover:bg-gray-600 text-white px-6 py-2 rounded-lg text-sm transition"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Competitors list */}
        {loading ? (
          <div className="text-center py-20">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-400">Loading competitors...</p>
          </div>
        ) : competitors.length === 0 ? (
          <div className="text-center py-20 border border-dashed border-gray-700 rounded-xl">
            <Building2 className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg mb-2">No competitors tracked yet</p>
            <p className="text-gray-600 text-sm">Click "Add Competitor" to start monitoring</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {competitors.map((comp) => (
              <div
                key={comp.id}
                className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-white mb-1">{comp.name}</h3>
                    <div className="flex flex-col gap-1 text-sm text-gray-500">
                      <span>🌐 {comp.website_url}</span>
                      {comp.careers_url && <span>💼 {comp.careers_url}</span>}
                      {comp.github_org && <span>🐙 github.com/{comp.github_org}</span>}
                      {comp.reddit_keyword && <span>🔴 Reddit: {comp.reddit_keyword}</span>}
                    </div>
                    <div className="mt-2">
                      <span className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded-full">
                        {comp.frequency} monitoring
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleRun(comp.id, comp.name)}
                      disabled={running === comp.id}
                      className="flex items-center gap-1.5 text-sm bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg transition"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${running === comp.id ? "animate-spin" : ""}`} />
                      {running === comp.id ? "Running..." : "Run Now"}
                    </button>
                    <button
                      onClick={() => handleDelete(comp.id, comp.name)}
                      disabled={deleting === comp.id}
                      className="flex items-center gap-1.5 text-sm bg-red-600/20 hover:bg-red-600/40 text-red-400 px-3 py-1.5 rounded-lg transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      {deleting === comp.id ? "Removing..." : "Remove"}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}