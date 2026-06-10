"use client";

import { useEffect, useState } from "react";
import { Activity, TrendingUp, AlertCircle, Building2, FileText, RefreshCw } from "lucide-react";
import Link from "next/link";

const API = "http://localhost:8000/api";

interface CompetitorSummary {
  competitor: {
    id: number;
    name: string;
    website_url: string;
    frequency: string;
  };
  total_signals: number;
  high_priority: number;
  medium_priority: number;
  low_priority: number;
  total_reports: number;
  latest_report: { report_text: string; generated_at: string } | null;
}

interface DashboardData {
  summary: CompetitorSummary[];
  total_competitors: number;
  generated_at: string;
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<number | null>(null);

  const fetchDashboard = async () => {
    try {
      const res = await fetch(`${API}/dashboard`);
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error("Failed to fetch dashboard:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const runPipeline = async (competitorId: number, name: string) => {
    setRunning(competitorId);
    try {
      await fetch(`${API}/run/${competitorId}`, { method: "POST" });
      alert(`✅ Pipeline started for ${name}! Check back in a few minutes.`);
    } catch (e) {
      alert("❌ Failed to start pipeline");
    } finally {
      setRunning(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400 text-lg">Loading intelligence dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
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
            <Link href="/" className="text-blue-400 font-medium">Dashboard</Link>
            <Link href="/competitors" className="text-gray-400 hover:text-white transition">Competitors</Link>
            <Link href="/reports" className="text-gray-400 hover:text-white transition">Reports</Link>
            <Link href="/trends" className="text-gray-400 hover:text-white transition">Trends</Link>
            <Link href="/battlecards" className="text-gray-400 hover:text-white transition">Battlecards</Link>
            <Link href="/timeline" className="text-gray-400 hover:text-white transition">Timeline</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Row */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <StatCard
            icon={<Building2 className="w-5 h-5 text-blue-400" />}
            label="Competitors Tracked"
            value={data?.total_competitors ?? 0}
            color="blue"
          />
          <StatCard
            icon={<AlertCircle className="w-5 h-5 text-red-400" />}
            label="High Priority Signals"
            value={data?.summary.reduce((a, b) => a + b.high_priority, 0) ?? 0}
            color="red"
          />
          <StatCard
            icon={<TrendingUp className="w-5 h-5 text-yellow-400" />}
            label="Total Signals"
            value={data?.summary.reduce((a, b) => a + b.total_signals, 0) ?? 0}
            color="yellow"
          />
          <StatCard
            icon={<FileText className="w-5 h-5 text-green-400" />}
            label="Reports Generated"
            value={data?.summary.reduce((a, b) => a + b.total_reports, 0) ?? 0}
            color="green"
          />
        </div>

        {/* Competitor Cards */}
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">Tracked Competitors</h2>
          <Link
            href="/competitors"
            className="text-sm text-blue-400 hover:text-blue-300 transition"
          >
            + Add Competitor
          </Link>
        </div>

        {!data?.summary.length ? (
          <div className="text-center py-20 border border-dashed border-gray-700 rounded-xl">
            <Building2 className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg mb-2">No competitors tracked yet</p>
            <p className="text-gray-600 text-sm mb-6">Add your first competitor to start monitoring</p>
            <Link
              href="/competitors"
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg text-sm transition"
            >
              Add Competitor
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {data.summary.map((item) => (
              <CompetitorCard
                key={item.competitor.id}
                item={item}
                onRun={() => runPipeline(item.competitor.id, item.competitor.name)}
                isRunning={running === item.competitor.id}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}


// ─────────────────────────────────────────
// COMPONENTS
// ─────────────────────────────────────────

function StatCard({
  icon, label, value, color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
}) {
  const borders: Record<string, string> = {
    blue: "border-blue-500/20",
    red: "border-red-500/20",
    yellow: "border-yellow-500/20",
    green: "border-green-500/20",
  };

  return (
    <div className={`bg-gray-900 border ${borders[color]} rounded-xl p-5`}>
      <div className="flex items-center gap-2 mb-3">{icon}<span className="text-gray-400 text-sm">{label}</span></div>
      <p className="text-3xl font-bold text-white">{value}</p>
    </div>
  );
}


function CompetitorCard({
  item, onRun, isRunning,
}: {
  item: CompetitorSummary;
  onRun: () => void;
  isRunning: boolean;
}) {
  const { competitor, total_signals, high_priority, medium_priority, low_priority, total_reports, latest_report } = item;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-white mb-1">{competitor.name}</h3>
          <a
            href={competitor.website_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-gray-500 hover:text-blue-400 transition"
          >
            {competitor.website_url}
          </a>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href={`/reports?id=${competitor.id}`}
            className="text-sm bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1.5 rounded-lg transition"
          >
            View Reports
          </Link>
          <button
            onClick={onRun}
            disabled={isRunning}
            className="flex items-center gap-1.5 text-sm bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRunning ? "animate-spin" : ""}`} />
            {isRunning ? "Running..." : "Run Now"}
          </button>
        </div>
      </div>

      {/* Signal counts */}
      <div className="flex items-center gap-4 mb-4">
        <SignalBadge emoji="🔴" count={high_priority} label="High" />
        <SignalBadge emoji="🟡" count={medium_priority} label="Medium" />
        <SignalBadge emoji="🟢" count={low_priority} label="Low" />
        <span className="text-gray-600 text-sm ml-auto">{total_reports} reports generated</span>
      </div>

      {/* Latest report preview */}
      {latest_report && (
        <div className="bg-gray-800 rounded-lg p-3 mt-3">
          <p className="text-xs text-gray-500 mb-1">
            Latest report — {new Date(latest_report.generated_at).toLocaleDateString()}
          </p>
          <p className="text-sm text-gray-300 line-clamp-2">
            {latest_report.report_text.slice(0, 200)}...
          </p>
        </div>
      )}
    </div>
  );
}


function SignalBadge({ emoji, count, label }: { emoji: string; count: number; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span>{emoji}</span>
      <span className="text-white font-semibold">{count}</span>
      <span className="text-gray-500 text-sm">{label}</span>
    </div>
  );
}