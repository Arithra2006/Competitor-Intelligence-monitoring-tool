"use client";

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
  ReferenceLine,
} from "recharts";

// ─────────────────────────────────────────
// CONFIDENCE TREND CHART
// ─────────────────────────────────────────

interface ConfidenceDataPoint {
  date: string;
  confidence: number;
  type: string;
}

interface ConfidenceTrendChartProps {
  data: ConfidenceDataPoint[];
  title?: string;
}

export function ConfidenceTrendChart({
  data,
  title = "Signal Confidence Over Time",
}: ConfidenceTrendChartProps) {
  if (data.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-bold text-white mb-4">{title}</h3>
        <div className="text-center py-12">
          <p className="text-gray-500">No data available yet</p>
          <p className="text-gray-600 text-sm">Run the pipeline to generate signals</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h3 className="text-lg font-bold text-white mb-6">{title}</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="date"
            stroke="#6B7280"
            tick={{ fill: "#9CA3AF", fontSize: 11 }}
          />
          <YAxis
            domain={[0, 100]}
            stroke="#6B7280"
            tick={{ fill: "#9CA3AF", fontSize: 11 }}
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1F2937",
              border: "1px solid #374151",
              borderRadius: "8px",
              color: "#F9FAFB",
              fontSize: "13px",
            }}
            formatter={(value) => [`${value}%`, "Confidence"]}
            labelFormatter={(label) => `Date: ${label}`}
          />
          {/* Threshold line at 50% */}
          <ReferenceLine
            y={50}
            stroke="#EF4444"
            strokeDasharray="4 4"
            label={{
              value: "Min threshold",
              fill: "#EF4444",
              fontSize: 10,
              position: "insideTopRight",
            }}
          />
          {/* High confidence line at 80% */}
          <ReferenceLine
            y={80}
            stroke="#10B981"
            strokeDasharray="4 4"
            label={{
              value: "High confidence",
              fill: "#10B981",
              fontSize: 10,
              position: "insideTopRight",
            }}
          />
          <Line
            type="monotone"
            dataKey="confidence"
            stroke="#3B82F6"
            strokeWidth={2.5}
            dot={{ fill: "#3B82F6", r: 5, strokeWidth: 2, stroke: "#1D4ED8" }}
            activeDot={{ r: 7, fill: "#60A5FA" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}


// ─────────────────────────────────────────
// SOURCE ACTIVITY BAR CHART
// ─────────────────────────────────────────

interface SourceDataPoint {
  source: string;
  crawls: number;
}

interface SourceActivityChartProps {
  data: SourceDataPoint[];
  title?: string;
}

export function SourceActivityChart({
  data,
  title = "Crawls by Source",
}: SourceActivityChartProps) {
  const SOURCE_COLORS: Record<string, string> = {
    website: "#3B82F6",
    careers: "#8B5CF6",
    github:  "#10B981",
    news:    "#F59E0B",
    reddit:  "#EF4444",
  };

  if (data.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-bold text-white mb-4">{title}</h3>
        <div className="text-center py-12">
          <p className="text-gray-500">No crawl data yet</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h3 className="text-lg font-bold text-white mb-6">{title}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="source"
            stroke="#6B7280"
            tick={{ fill: "#9CA3AF", fontSize: 12 }}
          />
          <YAxis
            stroke="#6B7280"
            tick={{ fill: "#9CA3AF", fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1F2937",
              border: "1px solid #374151",
              borderRadius: "8px",
              color: "#F9FAFB",
              fontSize: "13px",
            }}
            formatter={(value) => [value, "Crawls"]}
          />
          <Bar
            dataKey="crawls"
            radius={[6, 6, 0, 0]}
            fill="#3B82F6"
          />
        </BarChart>
      </ResponsiveContainer>

      {/* Source legend */}
      <div className="flex flex-wrap gap-3 mt-4">
        {data.map((d) => (
          <div key={d.source} className="flex items-center gap-1.5">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: SOURCE_COLORS[d.source] || "#6B7280" }}
            />
            <span className="text-gray-400 text-xs capitalize">{d.source}</span>
            <span className="text-white text-xs font-semibold">{d.crawls}</span>
          </div>
        ))}
      </div>
    </div>
  );
}


// ─────────────────────────────────────────
// SIGNAL TYPE DISTRIBUTION CHART
// ─────────────────────────────────────────

interface TypeDataPoint {
  type: string;
  count: number;
}

interface SignalTypeChartProps {
  data: TypeDataPoint[];
  title?: string;
}

export function SignalTypeChart({
  data,
  title = "Signal Type Distribution",
}: SignalTypeChartProps) {
  if (data.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-bold text-white mb-4">{title}</h3>
        <div className="text-center py-12">
          <p className="text-gray-500">No signals yet</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h3 className="text-lg font-bold text-white mb-6">{title}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            type="number"
            stroke="#6B7280"
            tick={{ fill: "#9CA3AF", fontSize: 12 }}
          />
          <YAxis
            type="category"
            dataKey="type"
            stroke="#6B7280"
            tick={{ fill: "#9CA3AF", fontSize: 11 }}
            width={150}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1F2937",
              border: "1px solid #374151",
              borderRadius: "8px",
              color: "#F9FAFB",
              fontSize: "13px",
            }}
            formatter={(value) => [value, "Signals"]}
          />
          <Bar
            dataKey="count"
            fill="#10B981"
            radius={[0, 6, 6, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}