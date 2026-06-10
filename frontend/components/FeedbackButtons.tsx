"use client";

import { useState } from "react";
import { ThumbsUp, ThumbsDown, Check } from "lucide-react";

const API = "http://localhost:8000/api";

interface FeedbackButtonsProps {
  signalId: number;
  initialFeedback?: string | null;
  onFeedbackSubmit?: (feedback: string) => void;
}

export default function FeedbackButtons({
  signalId,
  initialFeedback = null,
  onFeedbackSubmit,
}: FeedbackButtonsProps) {
  const [feedback, setFeedback] = useState<string | null>(initialFeedback);
  const [loading, setLoading] = useState(false);

  const submitFeedback = async (value: "useful" | "irrelevant") => {
    if (feedback === value) return;
    setLoading(true);
    try {
      await fetch(`${API}/signals/${signalId}/feedback`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback: value }),
      });
      setFeedback(value);
      onFeedbackSubmit?.(value);
    } catch (e) {
      console.error("Failed to submit feedback:", e);
    } finally {
      setLoading(false);
    }
  };

  if (feedback) {
    return (
      <div className="flex items-center gap-2">
        <div
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ${
            feedback === "useful"
              ? "bg-green-500/20 text-green-400 border border-green-500/30"
              : "bg-red-500/20 text-red-400 border border-red-500/30"
          }`}
        >
          <Check className="w-3.5 h-3.5" />
          {feedback === "useful" ? "Marked useful" : "Marked irrelevant"}
        </div>
        <button
          onClick={() => setFeedback(null)}
          className="text-xs text-gray-600 hover:text-gray-400 transition"
        >
          Change
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 mr-1">Was this useful?</span>
      <button
        onClick={() => submitFeedback("useful")}
        disabled={loading}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20 hover:bg-green-500/20 transition disabled:opacity-50"
      >
        <ThumbsUp className="w-3.5 h-3.5" />
        Useful
      </button>
      <button
        onClick={() => submitFeedback("irrelevant")}
        disabled={loading}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition disabled:opacity-50"
      >
        <ThumbsDown className="w-3.5 h-3.5" />
        Irrelevant
      </button>
    </div>
  );
}