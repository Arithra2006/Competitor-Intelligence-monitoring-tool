"use client";

import { useEffect, useState } from "react";
import { TrendingUp, ArrowLeft } from "lucide-react";
import Link from "next/link";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import FeedbackButtons from "@/components/FeedbackButtons";

const API = "http://localhost:8000/api";

interface Competitor {
  id: number;
  name: string;
}

interface Signal {
  id: number;
  signal_type: string;
  confidence: number;
  detected_at: string;
  feedback: string | null;
}

interface Snapshot {
  id: number;
  source: string;
  crawled_at: string;
  change_type: string | null;
}

export default function TrendsPage() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API}/competitors`)
      .then((r) => r.json())
      .then((d) => {
        setCompetitors(d.competitors);
        if (d.competitors.length > 0) {
          setSelectedId(d.competitors[0].id);
        }
      });
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    Promise.all([
      fetch(`${API}/signals/${selectedId}`).then((r) => r.json()),
      fetch(`${API}/snapshots/${selectedId}`).then((r) => r.json()),
    ])
      .then(([signalData, snapshotData]) => {
        setSignals(signalData.signals || []);
        setSnapshots(snapshotData.snapshots || []);
      })
      .finally(() => setLoading(false));
  }, [selectedId]);

  const confidenceTrend = signals
    .slice()
    .reverse()
    .map((s) => ({
      confidence: Math.round(s.confidence),
      type: s.signal_type,
      date: new Date(s.detected_at).toLocaleDateString(),
    }));

  const sourceCount: Record<string, number> = {};
  snapshots.forEach((s) => {
    sourceCount[s.source] = (sourceCount[s.source] || 0) + 1;
  });
  const sourceData = Object.entries(sourceCount).map(([source, count]) => ({
    source,
    crawls: count,
  }));

  const typeCount: Record<string, number> = {};
  signals.forEach((s) => {
    typeCount[s.signal_type] = (typeCount[s.signal_type] || 0) + 1;
  });
  const typeData = Object.entries(typeCount).map(([type, count]) => ({
    type: type.length > 20 ? type.slice(0, 20) + "..." : type,
    count,
  }));

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-5 h-5" />
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
            <Link href="/trends" className="text-blue-400 font-medium">Trends</Link>
            <Link href="/battlecards" className="text-gray-400 hover:text-white transition">Battlecards</Link>
            <Link href="/timeline" className="text-gray-400 hover:text-white transition">Timeline</Link>
            <Link href="/activity" className="text-gray-400 hover:text-white transition">Activity</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center gap-3 mb-8">
          <Link href="/" className="text-gray-400 hover:text-white transition">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h2 className="text-2xl font-bold text-white">Trend Analysis</h2>
            <p className="text-gray-400 text-sm">Signal confidence and activity over time</p>
          </div>
        </div>

        <div className="flex gap-3 mb-8 flex-wrap">
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
            <p className="text-gray-400">Loading trend data...</p>
          </div>
        ) : (
          <div className="space-y-6">

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <p className="text-gray-400 text-sm mb-1">Total Signals</p>
                <p className="text-3xl font-bold text-white">{signals.length}</p>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <p className="text-gray-400 text-sm mb-1">Avg Confidence</p>
                <p className="text-3xl font-bold text-white">
                  {signals.length > 0
                    ? Math.round(signals.reduce((a, b) => a + b.confidence, 0) / signals.length)
                    : 0}%
                </p>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <p className="text-gray-400 text-sm mb-1">Total Crawls</p>
                <p className="text-3xl font-bold text-white">{snapshots.length}</p>
              </div>
            </div>

            {/* Confidence trend */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <h3 className="text-lg font-bold text-white mb-6">Signal Confidence Over Time</h3>
              {confidenceTrend.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500">No signals detected yet</p>
                  <p className="text-gray-600 text-sm">Run the pipeline to generate signals</p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={confidenceTrend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="date" stroke="#6B7280" tick={{ fill: "#9CA3AF", fontSize: 12 }} />
                    <YAxis domain={[0, 100]} stroke="#6B7280" tick={{ fill: "#9CA3AF", fontSize: 12 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#1F2937", border: "1px solid #374151", borderRadius: "8px", color: "#F9FAFB" }}
                      formatter={(value) => [`${value}%`, "Confidence"]}
                    />
                    <Line type="monotone" dataKey="confidence" stroke="#3B82F6" strokeWidth={2} dot={{ fill: "#3B82F6", r: 4 }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Source activity */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <h3 className="text-lg font-bold text-white mb-6">Crawls by Source</h3>
              {sourceData.length === 0 ? (
                <div className="text-center py-12"><p className="text-gray-500">No crawl data yet</p></div>
              ) : (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={sourceData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="source" stroke="#6B7280" tick={{ fill: "#9CA3AF", fontSize: 12 }} />
                    <YAxis stroke="#6B7280" tick={{ fill: "#9CA3AF", fontSize: 12 }} />
                    <Tooltip contentStyle={{ backgroundColor: "#1F2937", border: "1px solid #374151", borderRadius: "8px", color: "#F9FAFB" }} />
                    <Bar dataKey="crawls" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Signal type distribution */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <h3 className="text-lg font-bold text-white mb-6">Signal Type Distribution</h3>
              {typeData.length === 0 ? (
                <div className="text-center py-12"><p className="text-gray-500">No signals yet</p></div>
              ) : (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={typeData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis type="number" stroke="#6B7280" tick={{ fill: "#9CA3AF", fontSize: 12 }} />
                    <YAxis type="category" dataKey="type" stroke="#6B7280" tick={{ fill: "#9CA3AF", fontSize: 11 }} width={140} />
                    <Tooltip contentStyle={{ backgroundColor: "#1F2937", border: "1px solid #374151", borderRadius: "8px", color: "#F9FAFB" }} />
                    <Bar dataKey="count" fill="#10B981" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Recent signals with feedback buttons */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-white">Recent Signals</h3>
                <p className="text-xs text-gray-500">Rate signals to improve future detection</p>
              </div>
              {signals.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No signals yet</p>
              ) : (
                <div className="overflow-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-gray-400 border-b border-gray-800">
                        <th className="text-left py-2 pr-4">Signal Type</th>
                        <th className="text-left py-2 pr-4">Confidence</th>
                        <th className="text-left py-2 pr-4">Detected</th>
                        <th className="text-left py-2">Was this useful?</th>
                      </tr>
                    </thead>
                    <tbody>
                      {signals.slice(0, 10).map((signal) => (
                        <tr key={signal.id} className="border-b border-gray-800 hover:bg-gray-800/50 transition">
                          <td className="py-4 pr-4 text-white">{signal.signal_type}</td>
                          <td className="py-4 pr-4">
                            <span className={`font-semibold ${
                              signal.confidence >= 80 ? "text-green-400"
                              : signal.confidence >= 60 ? "text-yellow-400"
                              : "text-red-400"
                            }`}>
                              {Math.round(signal.confidence)}%
                            </span>
                          </td>
                          <td className="py-4 pr-4 text-gray-400">
                            {new Date(signal.detected_at).toLocaleDateString()}
                          </td>
                          <td className="py-4">
                            <FeedbackButtons
                              signalId={signal.id}
                              initialFeedback={signal.feedback}
                              onFeedbackSubmit={(fb) => {
                                setSignals((prev) =>
                                  prev.map((s) =>
                                    s.id === signal.id ? { ...s, feedback: fb } : s
                                  )
                                );
                              }}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

          </div>
        )}
      </main>
    </div>
  );
}