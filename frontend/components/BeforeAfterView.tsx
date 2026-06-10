"use client";

import { useState } from "react";
import { ArrowRight, Eye } from "lucide-react";

interface BeforeAfterProps {
  before: {
    text: string;
    crawled_at: string;
    change_type?: string;
  };
  after: {
    text: string;
    crawled_at: string;
    change_type?: string;
  };
  source: string;
  changeType: string;
  confidence: number;
}

const SOURCE_ICONS: Record<string, string> = {
  website: "🌐",
  careers: "💼",
  github: "🐙",
  news: "📰",
  reddit: "🔴",
};

export default function BeforeAfterView({
  before,
  after,
  source,
  changeType,
  confidence,
}: BeforeAfterProps) {
  const [view, setView] = useState<"split" | "before" | "after">("split");

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <span className="text-xl">{SOURCE_ICONS[source] || "📊"}</span>
          <div>
            <p className="text-white font-medium capitalize">{source} — {changeType}</p>
            <p className="text-gray-500 text-xs">
              Confidence: {Math.round(confidence)}%
            </p>
          </div>
        </div>

        {/* View toggle */}
        <div className="flex bg-gray-800 rounded-lg p-1 gap-1">
          {(["split", "before", "after"] as const).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`px-3 py-1 rounded text-xs font-medium transition capitalize ${
                view === v
                  ? "bg-blue-600 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div
        className={`grid ${
          view === "split" ? "grid-cols-2" : "grid-cols-1"
        } divide-x divide-gray-800`}
      >
        {/* Before */}
        {(view === "split" || view === "before") && (
          <div className="p-5">
            <div className="flex items-center gap-2 mb-3">
              <span className="w-2 h-2 bg-red-500 rounded-full" />
              <p className="text-xs text-gray-400 font-medium">BEFORE</p>
              <p className="text-xs text-gray-600 ml-auto">
                {new Date(before.crawled_at).toLocaleDateString()}
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 max-h-64 overflow-auto">
              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap font-mono">
                {before.text || "No previous snapshot available"}
              </p>
            </div>
          </div>
        )}

        {/* After */}
        {(view === "split" || view === "after") && (
          <div className="p-5">
            <div className="flex items-center gap-2 mb-3">
              <span className="w-2 h-2 bg-green-500 rounded-full" />
              <p className="text-xs text-gray-400 font-medium">AFTER</p>
              <p className="text-xs text-gray-600 ml-auto">
                {new Date(after.crawled_at).toLocaleDateString()}
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 max-h-64 overflow-auto">
              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap font-mono">
                {after.text || "No new snapshot available"}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Change indicator */}
      {view === "split" && (
        <div className="px-5 py-3 border-t border-gray-800 bg-gray-800/50 flex items-center gap-2">
          <Eye className="w-4 h-4 text-blue-400" />
          <p className="text-xs text-gray-400">
            Semantic similarity analysis detected a{" "}
            <span className="text-blue-400 font-medium">{changeType}</span>{" "}
            with {Math.round(confidence)}% confidence
          </p>
        </div>
      )}
    </div>
  );
}