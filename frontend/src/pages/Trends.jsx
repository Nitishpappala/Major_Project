import React, { useState, useEffect } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import { fetchTrends } from "../api";
import { fetchChannels, fetchCategories } from "../api";

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#1e293b] border border-[#334155] rounded-lg px-4 py-3 shadow-xl">
        <p className="text-xs text-slate-400 mb-2 font-medium">{label}</p>
        {payload.map((entry, i) => (
          <div key={i} className="flex items-center gap-2 text-xs">
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-slate-400 capitalize">{entry.dataKey}:</span>
            <span className="text-white font-mono font-medium">
              {(entry.value * 100).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
}

export default function Trends() {
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [channelFilter, setChannelFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [channels, setChannels] = useState([]);
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    setLoading(true);
    fetchTrends(channelFilter, categoryFilter)
      .then((data) => setTrendData(Array.isArray(data) ? data : []))
      .catch((err) => {
        setError(err.message);
        setTrendData([]);
      })
      .finally(() => setLoading(false));
  }, [channelFilter, categoryFilter]);

  useEffect(() => {
    // Fetch channels and categories for filter options
    Promise.all([fetchChannels(), fetchCategories()])
      .then(([channelsData, categoriesData]) => {
        setChannels(channelsData);
        setCategories(categoriesData);
      })
      .catch((err) => console.error("Error fetching filter options:", err));
  }, []);

  if (loading)
    return (
      <div className="flex justify-center items-center h-64">
        Loading trends...
      </div>
    );
  if (error)
    return (
      <div className="flex justify-center items-center h-64">
        Error: {error}
      </div>
    );
  if (trendData.length === 0)
    return (
      <div className="flex justify-center items-center h-64">
        No trends data available
      </div>
    );

  const displayData = trendData;

  // Summary calculations with safe access
  const validData = displayData.filter((d) => d.avg_positive !== undefined);
  const avgPos =
    validData.length > 0
      ? validData.reduce((s, d) => s + (d.avg_positive || 0), 0) /
        validData.length
      : 0;
  const avgNeg =
    validData.length > 0
      ? validData.reduce((s, d) => s + (d.avg_negative || 0), 0) /
        validData.length
      : 0;
  const avgNeu =
    validData.length > 0
      ? validData.reduce((s, d) => s + (d.avg_neutral || 0), 0) /
        validData.length
      : 0;

  const recentData = validData.slice(-7);
  const olderData = validData.slice(0, 7);
  const recentPos =
    recentData.length > 0
      ? recentData.reduce((s, d) => s + (d.avg_positive || 0), 0) /
        recentData.length
      : 0;
  const olderPos =
    olderData.length > 0
      ? olderData.reduce((s, d) => s + (d.avg_positive || 0), 0) /
        olderData.length
      : 0;
  const posTrend =
    olderPos > 0 ? (((recentPos - olderPos) / olderPos) * 100).toFixed(1) : 0;

  const recentNeg =
    recentData.length > 0
      ? recentData.reduce((s, d) => s + (d.avg_negative || 0), 0) /
        recentData.length
      : 0;
  const olderNeg =
    olderData.length > 0
      ? olderData.reduce((s, d) => s + (d.avg_negative || 0), 0) /
        olderData.length
      : 0;
  const negTrend =
    olderNeg > 0 ? (((recentNeg - olderNeg) / olderNeg) * 100).toFixed(1) : 0;

  return (
    <div className="space-y-6 w-full">
      {/* Filters */}
      <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="block text-xs text-slate-500 mb-1.5">
              Channel
            </label>
            <select
              value={channelFilter}
              onChange={(e) => setChannelFilter(e.target.value)}
              className="px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-slate-300 focus:outline-none focus:border-blue-500/50 appearance-none cursor-pointer min-w-[180px]"
            >
              <option value="">All Channels</option>
              {channels.map((channel) => (
                <option key={channel.channel} value={channel.channel}>
                  {channel.channel} ({channel.article_count})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1.5">
              Category
            </label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-slate-300 focus:outline-none focus:border-blue-500/50 appearance-none cursor-pointer min-w-[180px]"
            >
              <option value="">All Categories</option>
              {categories.map((category) => (
                <option key={category.category} value={category.category}>
                  {category.category} ({category.article_count})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-6">
          Sentiment Trends Over Time
        </h3>
        <ResponsiveContainer width="100%" height={380}>
          <LineChart
            data={displayData}
            margin={{ top: 5, right: 20, bottom: 5, left: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              dataKey="article_date"
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={{ stroke: "#334155" }}
              tickLine={false}
              interval="preserveStartEnd"
              tickFormatter={(value) => {
                if (value instanceof Date) {
                  return value.toLocaleDateString();
                }
                return value;
              }}
            />
            <YAxis
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
              domain={[0, "auto"]}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="top"
              align="right"
              iconType="circle"
              iconSize={8}
              formatter={(value) => (
                <span className="text-xs text-slate-400 ml-1 capitalize">
                  {value}
                </span>
              )}
            />
            <Line
              type="monotone"
              dataKey="avg_positive"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              activeDot={{
                r: 4,
                stroke: "#10b981",
                strokeWidth: 2,
                fill: "#1e293b",
              }}
            />
            <Line
              type="monotone"
              dataKey="avg_negative"
              stroke="#ef4444"
              strokeWidth={2}
              dot={false}
              activeDot={{
                r: 4,
                stroke: "#ef4444",
                strokeWidth: 2,
                fill: "#1e293b",
              }}
            />
            <Line
              type="monotone"
              dataKey="avg_neutral"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
              activeDot={{
                r: 4,
                stroke: "#f59e0b",
                strokeWidth: 2,
                fill: "#1e293b",
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-slate-500 uppercase tracking-wider font-medium">
              Avg Positive
            </span>
            <div className="p-1.5 bg-emerald-500/15 rounded-md border border-emerald-500/20">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            </div>
          </div>
          <p className="text-2xl font-bold text-emerald-400">
            {(avgPos * 100).toFixed(1)}%
          </p>
          <p
            className={`text-xs mt-1 ${Number(posTrend) >= 0 ? "text-emerald-400" : "text-red-400"}`}
          >
            {Number(posTrend) >= 0 ? "+" : ""}
            {posTrend}% vs prior week
          </p>
        </div>

        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-slate-500 uppercase tracking-wider font-medium">
              Avg Negative
            </span>
            <div className="p-1.5 bg-red-500/15 rounded-md border border-red-500/20">
              <TrendingDown className="w-3.5 h-3.5 text-red-400" />
            </div>
          </div>
          <p className="text-2xl font-bold text-red-400">
            {(avgNeg * 100).toFixed(1)}%
          </p>
          <p
            className={`text-xs mt-1 ${Number(negTrend) <= 0 ? "text-emerald-400" : "text-red-400"}`}
          >
            {Number(negTrend) >= 0 ? "+" : ""}
            {negTrend}% vs prior week
          </p>
        </div>

        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-slate-500 uppercase tracking-wider font-medium">
              Avg Neutral
            </span>
            <div className="p-1.5 bg-amber-500/15 rounded-md border border-amber-500/20">
              <Minus className="w-3.5 h-3.5 text-amber-400" />
            </div>
          </div>
          <p className="text-2xl font-bold text-amber-400">
            {(avgNeu * 100).toFixed(1)}%
          </p>
          <p className="text-xs mt-1 text-slate-500">
            {displayData.length} data points
          </p>
        </div>
      </div>
    </div>
  );
}
