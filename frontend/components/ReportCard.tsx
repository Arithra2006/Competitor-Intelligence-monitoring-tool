"use client";

import { useState } from "react";
import { FileText, ChevronDown, ChevronUp, Calendar } from "lucide-react";

interface Report {
  id: number;
  competitor_id: number;
  report_text: string;
  generated_at: string;
}

interface ReportCardProps {
  report: Report;
  competitorName: string;
}

export default function ReportCard({ report, competitorName }: ReportCardProps) {
  const [expanded, setExpanded] = useState(false);

  const date = new Date(report.generated_at);
  const formattedDate = date.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const formattedTime = date.toLocaleTimeString();

  // Extract priority counts from report text
  const highCount = (report.report_text.match(/🔴/g) || []).length;
  const mediumCount = (report.report_text.match(/🟡/g) || []).length;
  const lowCount = (report.report_text.match(/🟢/g) || []).length;
  const hasSignals = highCount + mediumCount + lowCount > 0;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden hover:border-gray-700 transition">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-5 hover:bg-gray-800/50 transition text-left"
      >
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-blue-600/20 rounded-lg flex items-center justify-center">
            <FileText className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <p className="text-white font-semibold">
              Intelligence Brief — {competitorName}
            </p>
            <div className="flex items-center gap-2 mt-1">
              <Calendar className="w-3.5 h-3.5 text-gray-500" />
              <p className="text-gray-500 text-sm">{formattedDate}</p>
              <span className="text-gray-700">·</span>
              <p className="text-gray-600 text-sm">{formattedTime}</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Signal summary badges */}
          {hasSignals ? (
            <div className="flex items-center gap-2">
              {highCount > 0 && (
                <span className="flex items-center gap-1 text-xs bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-1 rounded-full">
                  🔴 {highCount}
                </span>
              )}
              {mediumCount > 0 && (
                <span className="flex items-center gap-1 text-xs bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 px-2 py-1 rounded-full">
                  🟡 {mediumCount}
                </span>
              )}
              {lowCount > 0 && (
                <span className="flex items-center gap-1 text-xs bg-green-500/10 text-green-400 border border-green-500/20 px-2 py-1 rounded-full">
                  🟢 {lowCount}
                </span>
              )}
            </div>
          ) : (
            <span className="text-xs text-gray-500 bg-gray-800 px-3 py-1 rounded-full">
              No signals
            </span>
          )}

          {expanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </button>

      {/* Expanded report content */}
      {expanded && (
        <div className="border-t border-gray-800">
          {/* Quick stats */}
          {hasSignals && (
            <div className="flex gap-4 px-5 py-3 bg-gray-800/50 border-b border-gray-800">
              <div className="text-center">
                <p className="text-red-400 font-bold text-lg">{highCount}</p>
                <p className="text-gray-500 text-xs">High</p>
              </div>
              <div className="text-center">
                <p className="text-yellow-400 font-bold text-lg">{mediumCount}</p>
                <p className="text-gray-500 text-xs">Medium</p>
              </div>
              <div className="text-center">
                <p className="text-green-400 font-bold text-lg">{lowCount}</p>
                <p className="text-gray-500 text-xs">Watch</p>
              </div>
            </div>
          )}

          {/* Report text */}
          <div className="p-5">
            <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono leading-relaxed bg-gray-800 rounded-lg p-4 overflow-auto max-h-[500px]">
              {report.report_text}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}