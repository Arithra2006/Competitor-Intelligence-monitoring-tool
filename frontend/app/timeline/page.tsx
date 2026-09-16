"use client";

import { useEffect, useState } from "react";
import { Clock, ArrowLeft, CheckCircle, AlertCircle, Activity } from "lucide-react";
import Link from "next/link";

const API = "http://localhost:8000/api";

interface Competitor {
  id: number;
  name: string;
}

interface TimelineEvent {
  type: string;
  date: string;
  datetime: string;
  title: string;
  confidence: number;
  priority: string;
  sources: string[];
  evidence: {
    source: string;
    reliability: number;
    detail: string;
    reasoning: string;
  }[];
  signal_id: number | null;
  feedback: string | null;
}

const PRIORITY_COLORS = {
  HIGH:   { border: "border-red-500/50",    bg: "bg-red-500/10",    dot: "bg-red-500",    text: "text-red-400",    emoji: "🔴" },
  MEDIUM: { border: "border-yellow-500/50", bg: "bg-yellow-500/10", dot: "bg-yellow-500", text: "text-yellow-400", emoji: "🟡" },
  LOW:    { border: "border-green-500/50",  bg: "bg-green-500/10",  dot: "bg-green-500",  text: "text-green-400",  emoji: "🟢" },
  NONE:   { border: "border-gray-700",      bg: "bg-gray-900",      dot: "bg-gray-600",   text: "text-gray-500",   emoji: "✅" },
};

const SOURCE_ICONS: Record<string, string> = {
  website: "🌐",
  careers: "💼",
  github:  "🐙",
  news:    "📰",
  reddit:  "🔴",
};

export default function TimelinePage() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [competitorName, setCompetitorName] = useState("");
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

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
    fetch(`${API}/timeline/${selectedId}`)
      .then((r) => r.json())
      .then((d) => {
        setEvents(d.events || []);
        setCompetitorName(d.competitor || "");
      })
      .finally(() => setLoading(false));
  }, [selectedId]);

  // Group events by date
  const groupedEvents: Record<string, TimelineEvent[]> = {};
  events.forEach((e) => {
    if (!groupedEvents[e.date]) groupedEvents[e.date] = [];
    groupedEvents[e.date].push(e);
  });

  const signalCount = events.filter((e) => e.type === "signal").length;
  const highCount   = events.filter((e) => e.priority === "HIGH").length;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Clock className="w-5 h-5" />
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
            <Link href="/timeline" className="text-blue-400 font-medium">Timeline</Link>
            <Link href="/timeline" className="text-gray-400 hover:text-white transition">Timeline</Link>
            <Link href="/activity" className="text-gray-400 hover:text-white transition">Activity</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* Page header */}
        <div className="flex items-center gap-3 mb-8">
          <Link href="/" className="text-gray-400 hover:text-white transition">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h2 className="text-2xl font-bold text-white">Change History Timeline</h2>
            <p className="text-gray-400 text-sm">
              Every change detected — in chronological order
            </p>
          </div>
        </div>

        {/* Competitor selector */}
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

        {/* Stats */}
        {!loading && events.length > 0 && (
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-gray-400 text-sm mb-1">Total Events</p>
              <p className="text-2xl font-bold text-white">{events.length}</p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-gray-400 text-sm mb-1">Signals Detected</p>
              <p className="text-2xl font-bold text-white">{signalCount}</p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-gray-400 text-sm mb-1">High Priority</p>
              <p className="text-2xl font-bold text-red-400">{highCount}</p>
            </div>
          </div>
        )}

        {loading ? (
          <div className="text-center py-20">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-400">Loading timeline...</p>
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-20 border border-dashed border-gray-700 rounded-xl">
            <Clock className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg mb-2">No history yet</p>
            <p className="text-gray-600 text-sm">
              Run the pipeline to start building the timeline
            </p>
          </div>
        ) : (
          <div className="relative">
            {/* Vertical line */}
            <div className="absolute left-6 top-0 bottom-0 w-px bg-gray-800" />

            <div className="space-y-0">
              {Object.entries(groupedEvents).map(([date, dayEvents]) => (
                <div key={date} className="mb-6">
                  {/* Date label */}
                  <div className="flex items-center gap-4 mb-3">
                    <div className="w-12 flex justify-center">
                      <div className="w-3 h-3 rounded-full bg-gray-600 border-2 border-gray-950" />
                    </div>
                    <p className="text-gray-500 text-sm font-medium">
                      {new Date(date).toLocaleDateString("en-US", {
                        weekday: "long",
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      })}
                    </p>
                  </div>

                  {/* Events for this date */}
                  {dayEvents.map((event, idx) => {
                    const colors = PRIORITY_COLORS[event.priority as keyof typeof PRIORITY_COLORS] || PRIORITY_COLORS.NONE;
                    const isExpanded = expanded === event.signal_id;

                    return (
                      <div key={idx} className="flex gap-4 mb-3 ml-0">
                        {/* Dot */}
                        <div className="w-12 flex justify-center flex-shrink-0 pt-4">
                          <div className={`w-3 h-3 rounded-full ${colors.dot} border-2 border-gray-950`} />
                        </div>

                        {/* Event card */}
                        <div className={`flex-1 border ${colors.border} ${colors.bg} rounded-xl overflow-hidden`}>
                          <button
                            onClick={() =>
                              event.type === "signal"
                                ? setExpanded(isExpanded ? null : event.signal_id)
                                : null
                            }
                            className="w-full text-left p-4"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex items-center gap-2">
                                <span>{colors.emoji}</span>
                                <div>
                                  <p className={`font-semibold ${event.type === "signal" ? "text-white" : "text-gray-500"}`}>
                                    {event.title}
                                  </p>
                                  <div className="flex items-center gap-3 mt-1">
                                    {event.sources.map((s) => (
                                      <span key={s} className="text-xs text-gray-500">
                                        {SOURCE_ICONS[s] || "📊"} {s}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              </div>

                              <div className="text-right flex-shrink-0 ml-4">
                                {event.confidence > 0 && (
                                  <p className={`text-sm font-bold ${colors.text}`}>
                                    {Math.round(event.confidence)}%
                                  </p>
                                )}
                                {event.type === "signal" && (
                                  <p className="text-xs text-gray-600 mt-0.5">
                                    {isExpanded ? "▲ hide" : "▼ details"}
                                  </p>
                                )}
                              </div>
                            </div>
                          </button>

                          {/* Expanded evidence */}
                          {isExpanded && event.evidence.length > 0 && (
                            <div className="border-t border-gray-800 p-4 space-y-3">
                              <p className="text-xs text-gray-500 uppercase tracking-wider font-medium">
                                Evidence
                              </p>
                              {event.evidence.map((e, i) => (
                                <div
                                  key={i}
                                  className="bg-gray-800 rounded-lg p-3 flex items-start gap-3"
                                >
                                  <span className="text-lg">
                                    {SOURCE_ICONS[e.source] || "📊"}
                                  </span>
                                  <div>
                                    <div className="flex items-center gap-2 mb-1">
                                      <p className="text-white text-sm font-medium capitalize">
                                        {e.source}
                                      </p>
                                      <span className="text-xs text-gray-500">
                                        reliability: {e.reliability}
                                      </span>
                                    </div>
                                    {e.detail && (
                                      <p className="text-gray-300 text-sm">{e.detail}</p>
                                    )}
                                    {e.reasoning && (
                                      <p className="text-gray-500 text-xs mt-1 italic">
                                        {e.reasoning}
                                      </p>
                                    )}
                                  </div>
                                </div>
                              ))}

                              {/* Feedback status */}
                              {event.feedback && (
                                <div className="flex items-center gap-2 mt-2">
                                  <span className="text-xs text-gray-500">Your rating:</span>
                                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                                    event.feedback === "useful"
                                      ? "bg-green-500/20 text-green-400"
                                      : "bg-red-500/20 text-red-400"
                                  }`}>
                                    {event.feedback === "useful" ? "👍 Useful" : "👎 Irrelevant"}
                                  </span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}