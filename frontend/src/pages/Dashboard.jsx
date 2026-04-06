import React, { useState, useEffect } from "react";
import {
  FileText,
  ThumbsUp,
  ThumbsDown,
  AlertTriangle,
  ExternalLink,
  Calendar,
  Minus,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  CartesianGrid,
  LineChart,
  Line,
} from "recharts";
import StatCard from "../components/StatCard";
import SentimentBadge from "../components/SentimentBadge";
import { fetchDashboard, fetchDashboardDates } from "../api";

const DONUT_COLORS = ["#10b981", "#ef4444", "#f59e0b"];

function CustomTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-2 shadow-xl">
        <p className="text-sm text-white font-medium">
          {payload[0].name || payload[0].payload.name}
        </p>
        <p className="text-xs text-slate-400">{payload[0].value}</p>
      </div>
    );
  }
  return null;
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [availableDates, setAvailableDates] = useState([]);
  const [selectedDate, setSelectedDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetchDashboard(selectedDate)
      .then(setData)
      .catch((err) => {
        setError(err.message);
        setData(null);
      })
      .finally(() => setLoading(false));
  }, [selectedDate]);

  useEffect(() => {
    fetchDashboardDates()
      .then((dates) => {
        setAvailableDates(Array.isArray(dates) ? dates : []);
      })
      .catch(() => {
        setAvailableDates([]);
      });
  }, []);

  if (loading)
    return (
      <div className="flex justify-center items-center h-64">
        <div>Loading dashboard data...</div>
      </div>
    );
  if (error || !data)
    return (
      <div className="flex justify-center items-center h-64">
        <div>Error: {error || "Failed to load data"}</div>
      </div>
    );

  const stats = data.stats;
  const sentimentDist = data.sentimentDistribution;
  const categories = data.categories;
  const channels = data.channels;
  const sentimentTrends = data.sentimentTrends || [];
  const categorySentiment = data.categorySentiment || [];
  const channelSentiment = data.channelSentiment || [];
  const ministrySentiment = data.ministrySentiment || [];
  const dailyVolume = data.dailyVolume || [];
  const dailySentimentCounts = data.dailySentimentCounts || [];
  const sentimentPolarity = data.sentimentPolarity || [];

  return (
    <div className="space-y-6 w-full">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-[#0f172a]/80 backdrop-blur-xl border-b border-[#334155]">
        <div className="flex items-center justify-between px-8 py-4">
          <h2 className="text-xl font-semibold text-white">Dashboard</h2>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-[#1e293b] rounded-lg border border-[#334155]">
                <FileText className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-slate-400">Total Articles:</span>
                <span className="text-white font-semibold">
                  {stats.totalArticles.toLocaleString()}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-[#1e293b] rounded-lg border border-[#334155] text-xs">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-300">
                {selectedDate || "All dates"}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
            Dashboard overview
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Select a date to view metrics for that day, or leave blank to show
            all dates combined.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex flex-col text-xs text-slate-400">
            <label
              htmlFor="dashboard-date"
              className="mb-1 uppercase tracking-wider"
            >
              Date filter
            </label>
            <select
              id="dashboard-date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="min-w-[200px] px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-slate-300 focus:outline-none focus:border-blue-500/50"
            >
              <option value="">All dates</option>
              {availableDates.map((date) => (
                <option key={date} value={date}>
                  {date}
                </option>
              ))}
            </select>
          </div>
          {selectedDate && (
            <button
              onClick={() => setSelectedDate("")}
              className="h-fit px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-xs text-slate-300 hover:bg-slate-700 transition-colors"
            >
              Clear date
            </button>
          )}
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <StatCard
          icon={ThumbsUp}
          value={`${stats.positivePercent}%`}
          label="Positive Sentiment"
          accent="green"
        />
        <StatCard
          icon={ThumbsDown}
          value={`${stats.negativePercent}%`}
          label="Negative Sentiment"
          accent="red"
        />
        <StatCard
          icon={Minus}
          value={`${stats.neutralPercent}%`}
          label="Neutral Sentiment"
          accent="amber"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment Donut */}
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
            Sentiment Distribution
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={sentimentDist}
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={110}
                paddingAngle={3}
                dataKey="value"
                strokeWidth={0}
              >
                {sentimentDist.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={DONUT_COLORS[index % DONUT_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="bottom"
                iconType="circle"
                iconSize={8}
                formatter={(value) => (
                  <span className="text-xs text-slate-400 ml-1">{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Category Distribution */}
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
            Category Distribution
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={categories} layout="vertical" margin={{ left: 20 }}>
              <XAxis
                type="number"
                tick={{ fill: "#64748b", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fill: "#94a3b8", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
                width={80}
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{ fill: "rgba(59,130,246,0.05)" }}
              />
              <Bar
                dataKey="count"
                fill="#3b82f6"
                radius={[0, 4, 4, 0]}
                barSize={18}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Additional Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Ministry Sentiment Analysis */}
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
            Ministry Sentiment Analysis
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={ministrySentiment.slice(0, 5)} layout="vertical">
              <XAxis type="number" tick={{ fill: "#64748b", fontSize: 11 }} />
              <YAxis
                dataKey="ministry"
                type="category"
                tick={{ fill: "#94a3b8", fontSize: 10 }}
                width={100}
              />
              <Tooltip />
              <Legend />
              <Bar dataKey="positive" fill="#10b981" />
              <Bar dataKey="negative" fill="#ef4444" />
              <Bar dataKey="neutral" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Daily Article Volume */}
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
            Daily Article Volume
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={dailyVolume}>
              <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} />
              <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Sentiment Trends Over Time */}
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6 lg:col-span-2">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
            Sentiment Trends Over Time
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={sentimentTrends}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} />
              <YAxis tick={{ fill: "#64748b", fontSize: 11 }} domain={[0, 1]} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line
                type="monotone"
                dataKey="positive"
                stroke="#10b981"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="negative"
                stroke="#ef4444"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="neutral"
                stroke="#f59e0b"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Category Sentiment Breakdown */}
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
            Category Sentiment Breakdown
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={categorySentiment}>
              <XAxis
                dataKey="category"
                tick={{ fill: "#64748b", fontSize: 10 }}
              />
              <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="positive" stackId="a" fill="#10b981" />
              <Bar dataKey="negative" stackId="a" fill="#ef4444" />
              <Bar dataKey="neutral" stackId="a" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Daily Sentiment Counts */}
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
            Daily Sentiment Article Counts
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={dailySentimentCounts}>
              <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} />
              <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="positive" stackId="a" fill="#10b981" />
              <Bar dataKey="negative" stackId="a" fill="#ef4444" />
              <Bar dataKey="neutral" stackId="a" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Sentiment Polarity Trend */}
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6 lg:col-span-2">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
            Sentiment Polarity Trend
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={sentimentPolarity}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} />
              <YAxis
                tick={{ fill: "#64748b", fontSize: 11 }}
                domain={[-1, 1]}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="polarity"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={{ fill: "#8b5cf6", strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Channel Sentiment Comparison */}
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6 lg:col-span-2">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
            Channel Sentiment Comparison
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={channelSentiment.slice(0, 5)}>
              <XAxis
                dataKey="channel"
                tick={{ fill: "#64748b", fontSize: 10 }}
              />
              <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="positive" fill="#10b981" />
              <Bar dataKey="negative" fill="#ef4444" />
              <Bar dataKey="neutral" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Channel Performance with Sentiment */}
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6 lg:col-span-2">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
            Channel Performance with Sentiment
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#334155]">
                  <th className="text-left py-3 px-2 text-slate-500 font-medium text-xs uppercase tracking-wider">
                    Channel
                  </th>
                  <th className="text-right py-3 px-2 text-slate-500 font-medium text-xs uppercase tracking-wider">
                    Articles
                  </th>
                  <th className="text-right py-3 px-2 text-slate-500 font-medium text-xs uppercase tracking-wider">
                    Positive
                  </th>
                  <th className="text-right py-3 px-2 text-slate-500 font-medium text-xs uppercase tracking-wider">
                    Negative
                  </th>
                  <th className="text-right py-3 px-2 text-slate-500 font-medium text-xs uppercase tracking-wider">
                    Neutral
                  </th>
                </tr>
              </thead>
              <tbody>
                {channelSentiment.slice(0, 10).map((ch, i) => (
                  <tr
                    key={i}
                    className="border-b border-[#334155]/50 hover:bg-[#293548] transition-colors"
                  >
                    <td className="py-3 px-2 text-slate-200 font-medium">
                      {ch.channel}
                    </td>
                    <td className="py-3 px-2 text-right text-slate-400">
                      {ch.positive + ch.negative + ch.neutral}
                    </td>
                    <td className="py-3 px-2 text-right text-emerald-400">
                      {ch.positive}
                    </td>
                    <td className="py-3 px-2 text-right text-red-400">
                      {ch.negative}
                    </td>
                    <td className="py-3 px-2 text-right text-amber-400">
                      {ch.neutral}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
