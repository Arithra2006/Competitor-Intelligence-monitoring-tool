"use client";

interface Evidence {
  source: string;
  reliability: number;
  detail: string;
  reasoning: string;
  confidence?: number;
}

interface EvidenceCardProps {
  evidence: Evidence[];
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

const RELIABILITY_LABEL: Record<string, string> = {
  "0.9": "Very High",
  "0.8": "High",
  "0.7": "Good",
  "0.5": "Medium",
};

export default function EvidenceCard({
  evidence,
  changeType,
  confidence,
}: EvidenceCardProps) {
  const confidenceColor =
    confidence >= 80
      ? "text-green-400 border-green-500/30 bg-green-500/10"
      : confidence >= 60
      ? "text-yellow-400 border-yellow-500/30 bg-yellow-500/10"
      : "text-red-400 border-red-500/30 bg-red-500/10";

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-semibold">{changeType}</h3>
        <span
          className={`text-sm font-bold px-3 py-1 rounded-full border ${confidenceColor}`}
        >
          {Math.round(confidence)}% confidence
        </span>
      </div>

      {/* Confidence formula breakdown */}
      <div className="bg-gray-800 rounded-lg p-3 mb-4">
        <p className="text-xs text-gray-500 mb-2 font-mono">
          confidence = 0.4×agreement + 0.4×reliability + 0.2×strength
        </p>
        <div className="flex gap-4">
          <div className="text-center">
            <p className="text-blue-400 font-bold text-lg">
              {evidence.length}
            </p>
            <p className="text-gray-500 text-xs">sources</p>
          </div>
          <div className="text-center">
            <p className="text-purple-400 font-bold text-lg">
              {evidence.length > 0
                ? (
                    evidence.reduce((a, b) => a + b.reliability, 0) /
                    evidence.length
                  ).toFixed(2)
                : "0.00"}
            </p>
            <p className="text-gray-500 text-xs">avg reliability</p>
          </div>
          <div className="text-center">
            <p className="text-green-400 font-bold text-lg">
              {Math.round(confidence)}%
            </p>
            <p className="text-gray-500 text-xs">final score</p>
          </div>
        </div>
      </div>

      {/* Evidence items */}
      <div className="space-y-3">
        <p className="text-xs text-gray-500 uppercase tracking-wider">
          Evidence
        </p>
        {evidence.map((e, i) => (
          <div
            key={i}
            className="flex items-start gap-3 bg-gray-800 rounded-lg p-3"
          >
            <span className="text-xl mt-0.5">
              {SOURCE_ICONS[e.source] || "📊"}
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <span className="text-white text-sm font-medium capitalize">
                  {e.source}
                </span>
                <span className="text-xs text-gray-500">
                  reliability:{" "}
                  <span className="text-blue-400 font-semibold">
                    {e.reliability}
                  </span>
                </span>
              </div>
              {e.detail && (
                <p className="text-gray-300 text-sm mb-1">{e.detail}</p>
              )}
              {e.reasoning && (
                <p className="text-gray-500 text-xs italic">{e.reasoning}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}