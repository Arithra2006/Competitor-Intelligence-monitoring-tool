"use client";

import { useEffect, useState } from "react";
import { Activity, ArrowLeft } from "lucide-react";
import Link from "next/link";

const API = "http://localhost:8000/api";

interface Competitor {
  id: number;
  name: string;
}

interface LogEntry {
  id: number;
  phase: string;
  message: string;
  level: string;
  created_at: string;
}

const PHASE_ICONS: Record<string, string> = {
  collector: "🌐",
  detector: "🧠",
  classifier: "🔬",
  scorer: "📊",
  reporter: "📰",
  delivery: "📬",
};

const LEVEL_COLORS: Record<string, string> = {
  info: "text-gray-300",
  warning: "text-yellow-400",
  error: "text-red-400",
};

export default function ActivityPage() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API}/competitors`)
      .then((r) => r.json())
      .then((d) => {
        setCompetitors(d.competitors);
        if (d.competitors.length > 0) setSelectedId(d.competitors[0].id);
      });
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    fetch(`${API}/logs/${selectedId}`)
      .then((r) => r.json())
      .then((d) => setLogs(d.logs || []))
      .finally(() => setLoading(false));
  }, [selectedId]);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Competitor Intelligence</h1>
              <p className="text-xs text-gray-400">Autonomous monitoring pipeline</p>
            </div>
          </div>
          <nav className="flex items-center gap-6 text-sm">
            <Link href="/" className="text-gray-400 hover:text-white transition">Dashboard</Link>
            <Link href="/competitors" className="text-gray-400 hover:text-white transition">Competitors</Link>
            <Link href="/reports" className="text-gray-400 hover:text-white transition">Reports</Link>
            <Link href="/trends" className="text-gray-400 hover:text-white transition">Trends</Link>
            <Link href="/battlecards" className="text-gray-400 hover:text-white transition">Battlecards</Link>
            <Link href="/timeline" className="text-gray-400 hover:text-white transition">Timeline</Link>
            <Link href="/activity" className="text-blue-400 font-medium">Activity</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center gap-3 mb-8">
          <Link href="/" className="text-gray-400 hover:text-white transition">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h2 className="text-2xl font-bold text-white">Pipeline Activity</h2>
            <p className="text-gray-400 text-sm">Live log of what the pipeline is doing</p>
          </div>
        </div>

        <div className="flex gap-3 mb-6 flex-wrap">
          {competitors.map((comp) => (
            <button
              key={comp.id}
              onClick={() => setSelectedId(comp.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                selectedId === comp.id
                  ? "bg-blue-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:text-white"
              }`}
            >
              {comp.name}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center py-20">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-400">Loading activity...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-20 border border-dashed border-gray-700 rounded-xl">
            <Activity className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg mb-2">No activity yet</p>
            <p className="text-gray-600 text-sm">Run the pipeline to see live logs here</p>
          </div>
        ) : (
          <div className="space-y-2">
            {logs.map((log) => (
              <div
                key={log.id}
                className="bg-gray-900 border border-gray-800 rounded-lg p-3 flex items-start gap-3"
              >
                <span className="text-lg">{PHASE_ICONS[log.phase] || "📋"}</span>
                <div className="flex-1">
                  <p className={`text-sm ${LEVEL_COLORS[log.level] || "text-gray-300"}`}>
                    {log.message}
                  </p>
                  <p className="text-xs text-gray-600 mt-0.5">
                    {new Date(log.created_at).toLocaleString()} — {log.phase}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}