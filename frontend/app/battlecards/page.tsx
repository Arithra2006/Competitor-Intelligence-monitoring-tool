"use client";

import { useEffect, useState } from "react";
import { Shield, ArrowLeft, RefreshCw, Trophy, AlertTriangle, Eye, Zap } from "lucide-react";
import Link from "next/link";

const API = "http://localhost:8000/api";

interface Competitor {
  id: number;
  name: string;
}

interface Battlecard {
  competitor_id: number;
  competitor_name: string;
  our_company: string;
  our_strengths: string[];
  our_weaknesses: string[];
  their_strengths: string[];
  their_weaknesses: string[];
  recent_moves: string[];
  how_to_win: string[];
  watch_out_for: string[];
  key_differentiators: string[];
  confidence_score: number;
  generated_at: string;
}

export default function BattlecardsPage() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [battlecard, setBattlecard] = useState<Battlecard | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

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
    fetchBattlecard(selectedId);
  }, [selectedId]);

  const fetchBattlecard = async (id: number) => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/battlecards/${id}`);
      const data = await res.json();
      setBattlecard(data.battlecard);
    } catch (e) {
      console.error("Failed to fetch battlecard:", e);
    } finally {
      setLoading(false);
    }
  };

  const generateBattlecard = async () => {
    if (!selectedId) return;
    setGenerating(true);
    try {
      const res = await fetch(`${API}/battlecards/${selectedId}`, {
        method: "POST",
      });
      const data = await res.json();
      setBattlecard(data.battlecard);
    } catch (e) {
      alert("Failed to generate battlecard");
    } finally {
      setGenerating(false);
    }
  };

  const selectedCompetitor = competitors.find((c) => c.id === selectedId);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Shield className="w-5 h-5" />
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
            <Link href="/battlecards" className="text-blue-400 font-medium">Battlecards</Link>
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
              <h2 className="text-2xl font-bold text-white">Sales Battlecards</h2>
              <p className="text-gray-400 text-sm">
                AI-generated competitive battlecards — what Crayon charges $15k/year for
              </p>
            </div>
          </div>
          <button
            onClick={generateBattlecard}
            disabled={generating || !selectedId}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition"
          >
            <RefreshCw className={`w-4 h-4 ${generating ? "animate-spin" : ""}`} />
            {generating ? "Generating..." : "Generate Battlecard"}
          </button>
        </div>

        {/* Competitor selector */}
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
            <p className="text-gray-400">Loading battlecard...</p>
          </div>
        ) : !battlecard ? (
          <div className="text-center py-20 border border-dashed border-gray-700 rounded-xl">
            <Shield className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg mb-2">No battlecard yet</p>
            <p className="text-gray-600 text-sm mb-6">
              Click "Generate Battlecard" to create one for{" "}
              {selectedCompetitor?.name}
            </p>
            <button
              onClick={generateBattlecard}
              disabled={generating}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg text-sm transition"
            >
              {generating ? "Generating..." : "Generate Now"}
            </button>
          </div>
        ) : (
          <div className="space-y-4">

            {/* Battlecard header */}
            <div className="bg-gray-900 border border-blue-500/30 rounded-xl p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-blue-400 text-xs font-medium uppercase tracking-wider mb-1">
                    Battlecard
                  </p>
                  <h3 className="text-2xl font-bold text-white mb-1">
                    Competing Against: {battlecard.competitor_name}
                  </h3>
                  <p className="text-gray-400 text-sm">
                    {battlecard.our_company} vs {battlecard.competitor_name} •
                    Last updated:{" "}
                    {new Date(battlecard.generated_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-blue-400">
                    {Math.round(battlecard.confidence_score)}%
                  </p>
                  <p className="text-gray-500 text-xs">confidence</p>
                </div>
              </div>
            </div>

            {/* Main grid */}
            <div className="grid grid-cols-2 gap-4">

              {/* Recent moves */}
              {battlecard.recent_moves.length > 0 && (
                <div className="col-span-2 bg-red-500/10 border border-red-500/20 rounded-xl p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="w-5 h-5 text-red-400" />
                    <h4 className="text-red-400 font-semibold">Their Recent Moves</h4>
                  </div>
                  <ul className="space-y-2">
                    {battlecard.recent_moves.map((move, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                        <span className="text-red-400 mt-0.5">•</span>
                        {move}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Our strengths */}
              <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Trophy className="w-5 h-5 text-green-400" />
                  <h4 className="text-green-400 font-semibold">Our Strengths vs Them</h4>
                </div>
                <ul className="space-y-2">
                  {battlecard.our_strengths.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                      <span className="text-green-400 mt-0.5">✓</span>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Their weaknesses */}
              <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-5 h-5 text-yellow-400" />
                  <h4 className="text-yellow-400 font-semibold">Their Weaknesses</h4>
                </div>
                <ul className="space-y-2">
                  {battlecard.their_weaknesses.map((w, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                      <span className="text-yellow-400 mt-0.5">•</span>
                      {w}
                    </li>
                  ))}
                </ul>
              </div>

              {/* How to win */}
              <div className="col-span-2 bg-blue-500/10 border border-blue-500/20 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Zap className="w-5 h-5 text-blue-400" />
                  <h4 className="text-blue-400 font-semibold">How to Win</h4>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {battlecard.how_to_win.map((tip, i) => (
                    <div
                      key={i}
                      className="bg-blue-500/10 rounded-lg p-3 text-sm text-gray-300 flex items-start gap-2"
                    >
                      <span className="text-blue-400 font-bold">{i + 1}.</span>
                      {tip}
                    </div>
                  ))}
                </div>
              </div>

              {/* Watch out for */}
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Eye className="w-5 h-5 text-purple-400" />
                  <h4 className="text-purple-400 font-semibold">Watch Out For</h4>
                </div>
                <ul className="space-y-2">
                  {battlecard.watch_out_for.map((w, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                      <span className="text-purple-400 mt-0.5">👀</span>
                      {w}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Key differentiators */}
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Shield className="w-5 h-5 text-cyan-400" />
                  <h4 className="text-cyan-400 font-semibold">Key Differentiators</h4>
                </div>
                <ul className="space-y-2">
                  {battlecard.key_differentiators.map((d, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                      <span className="text-cyan-400 mt-0.5">💡</span>
                      {d}
                    </li>
                  ))}
                </ul>
              </div>

            </div>
          </div>
        )}
      </main>
    </div>
  );
}