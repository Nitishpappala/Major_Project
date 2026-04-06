import React, { useState, useEffect } from "react";
import {
  BarChart3,
  Database,
  Zap,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Clock,
  FileJson,
} from "lucide-react";
import { fetchProjectInfo, fetchChannels, fetchLineage } from "../api";

const PipelineStage = ({
  stage_name,
  stage_number,
  status,
  icon: Icon,
  description,
  data_count,
  output,
}) => {
  const statusColor =
    status === "completed"
      ? "bg-emerald-500/20 border-emerald-500/50 text-emerald-400"
      : status === "running"
        ? "bg-blue-500/20 border-blue-500/50 text-blue-400"
        : "bg-slate-500/20 border-slate-500/50 text-slate-400";

  const statusIcon =
    status === "completed" ? (
      <CheckCircle className="w-4 h-4" />
    ) : status === "running" ? (
      <Zap className="w-4 h-4 animate-pulse" />
    ) : (
      <Clock className="w-4 h-4" />
    );

  const getIcon = () => {
    switch (stage_number) {
      case 1:
        return <Database className="w-5 h-5 text-slate-400" />;
      case 2:
        return <FileJson className="w-5 h-5 text-slate-400" />;
      case 3:
        return <Zap className="w-5 h-5 text-slate-400" />;
      case 4:
        return <TrendingUp className="w-5 h-5 text-slate-400" />;
      default:
        return <BarChart3 className="w-5 h-5 text-slate-400" />;
    }
  };

  return (
    <div className="bg-[#1e293b] border border-[#334155] rounded-lg p-4 w-full">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 flex-1">
          <div className="p-2 bg-slate-500/15 rounded-lg border border-slate-500/20">
            {getIcon()}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold text-slate-400 bg-slate-500/20 px-2 py-0.5 rounded">
                Stage {stage_number}
              </span>
              <h3 className="text-sm font-semibold text-slate-200">
                {stage_name}
              </h3>
            </div>
            <p className="text-xs text-slate-500">{description}</p>
            {output && (
              <p className="text-xs text-slate-600 mt-1">Output: {output}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          {data_count !== undefined && (
            <div className="text-right">
              <p className="text-xs text-slate-500">Records</p>
              <p className="text-lg font-bold text-emerald-400">
                {data_count > 999
                  ? (data_count / 1000).toFixed(1) + "K"
                  : data_count}
              </p>
            </div>
          )}
          <div
            className={`px-2.5 py-1 rounded-full border text-xs font-medium flex items-center gap-1.5 whitespace-nowrap ${statusColor}`}
          >
            {statusIcon}
            <span className="capitalize">{status}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function ProjectInfo() {
  const [stats, setStats] = useState({
    totalArticles: 0,
    channels: 0,
    categories: 0,
    dateRange: { start: "", end: "" },
  });
  const [channelsList, setChannelsList] = useState([]);
  const [lineageStages, setLineageStages] = useState([]);

  useEffect(() => {
    // Fetch project statistics, channels, and lineage
    Promise.all([fetchProjectInfo(), fetchChannels(), fetchLineage()])
      .then(([projectData, channelsData, lineageData]) => {
        setStats({
          totalArticles: projectData.total_articles || 0,
          channels: projectData.channels_count || 0,
          categories: projectData.categories_count || 0,
          dateRange: {
            start: projectData.date_range?.start || "N/A",
            end: projectData.date_range?.end || "N/A",
          },
        });
        setChannelsList(channelsData || []);
        setLineageStages(lineageData.lineage_stages || []);
      })
      .catch((err) => console.error("Error fetching stats:", err));
  }, []);

  return (
    <div className="space-y-6 w-full">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#1e293b] to-[#0f172a] border border-[#334155] rounded-xl p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white mb-2">
              Project Lineage & Data Pipeline
            </h1>
            <p className="text-slate-400 text-sm max-w-2xl">
              A comprehensive data pipeline that collects, processes, and
              analyzes news sentiment across multiple Indian news channels using
              Databricks and advanced NLP techniques.
            </p>
          </div>
          <div className="p-3 bg-blue-500/15 rounded-lg border border-blue-500/20">
            <BarChart3 className="w-6 h-6 text-blue-400" />
          </div>
        </div>
      </div>

      {/* Key Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#1e293b] border border-[#334155] rounded-lg p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
            Total Articles
          </p>
          <p className="text-2xl font-bold text-emerald-400">
            {stats.totalArticles.toLocaleString()}
          </p>
        </div>
        <div className="bg-[#1e293b] border border-[#334155] rounded-lg p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
            News Channels
          </p>
          <p className="text-2xl font-bold text-blue-400">{stats.channels}</p>
        </div>
        <div className="bg-[#1e293b] border border-[#334155] rounded-lg p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
            Categories
          </p>
          <p className="text-2xl font-bold text-amber-400">
            {stats.categories}
          </p>
        </div>
        <div className="bg-[#1e293b] border border-[#334155] rounded-lg p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
            Last Updated
          </p>
          <p className="text-sm font-semibold text-slate-300">
            {new Date().toLocaleDateString()}
          </p>
        </div>
      </div>

      {/* Data Pipeline */}
      <div>
        <h2 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <Database className="w-5 h-5" />
          Data Lineage & Pipeline Stages
        </h2>
        <div className="flex flex-col items-center gap-4 max-w-3xl mx-auto">
          {lineageStages && lineageStages.length > 0 ? (
            lineageStages.map((item, idx) => (
              <React.Fragment key={idx}>
                <div className="w-full">
                  <PipelineStage {...item} />
                </div>
                {idx < lineageStages.length - 1 && (
                  <div className="flex items-center justify-center py-2">
                    <div className="w-1 h-12 bg-gradient-to-b from-slate-500/50 to-slate-500/10 rounded-full"></div>
                  </div>
                )}
              </React.Fragment>
            ))
          ) : (
            <div className="text-slate-400 text-sm">
              Loading lineage data...
            </div>
          )}
        </div>
      </div>

      {/* Project Architecture */}
      <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
        <h2 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Technology Stack & Architecture
        </h2>
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-medium text-slate-300 mb-2">
              Data Sources ({channelsList.length} channels)
            </h3>
            <div className="flex flex-wrap gap-2">
              {channelsList && channelsList.length > 0 ? (
                channelsList.map((ch) => (
                  <span
                    key={ch.channel}
                    className="px-3 py-1 bg-blue-500/15 border border-blue-500/30 rounded-full text-xs text-blue-300"
                  >
                    {ch.channel}
                  </span>
                ))
              ) : (
                <span className="text-xs text-slate-500">
                  Loading channels...
                </span>
              )}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-slate-300 mb-2">
              Processing Tools
            </h3>
            <div className="flex flex-wrap gap-2">
              {["Databricks", "Delta Lake", "Python", "FastAPI"].map((tool) => (
                <span
                  key={tool}
                  className="px-3 py-1 bg-emerald-500/15 border border-emerald-500/30 rounded-full text-xs text-emerald-300"
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-slate-300 mb-2">
              AI/ML Models
            </h3>
            <div className="space-y-2">
              <div>
                <p className="text-xs text-slate-400 mb-1">
                  Classification Models:
                </p>
                <div className="flex flex-wrap gap-2">
                  {["AutoKeras", "DistilBERT"].map((model) => (
                    <span
                      key={model}
                      className="px-3 py-1 bg-purple-500/15 border border-purple-500/30 rounded-full text-xs text-purple-300"
                    >
                      {model}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs text-slate-400 mb-1">
                  Sentiment Analysis Models:
                </p>
                <div className="flex flex-wrap gap-2">
                  {["RoBERTa    ", "TextBlob Analysis"].map((model) => (
                    <span
                      key={model}
                      className="px-3 py-1 bg-indigo-500/15 border border-indigo-500/30 rounded-full text-xs text-indigo-300"
                    >
                      {model}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-slate-300 mb-2">
              Frontend Stack
            </h3>
            <div className="flex flex-wrap gap-2">
              {["React", "Vite", "Tailwind CSS", "Recharts"].map((tech) => (
                <span
                  key={tech}
                  className="px-3 py-1 bg-orange-500/15 border border-orange-500/30 rounded-full text-xs text-orange-300"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Pipeline Flow Diagram */}
      <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-6">
        <h2 className="text-lg font-semibold text-slate-200 mb-4">
          Data Flow Visualization
        </h2>
        <div className="bg-[#0f172a] rounded-lg p-8 overflow-x-auto">
          <div className="flex items-center justify-center gap-4 min-w-max">
            {/* Step 1 */}
            <div className="flex flex-col items-center">
              <div className="w-24 h-24 bg-blue-500/20 border-2 border-blue-500/50 rounded-lg flex items-center justify-center mb-2">
                <div className="text-center">
                  <Database className="w-6 h-6 text-blue-400 mx-auto mb-1" />
                  <p className="text-xs text-blue-300 font-medium">
                    Collection
                  </p>
                </div>
              </div>
            </div>

            {/* Arrow */}
            <div className="text-slate-500 text-2xl">→</div>

            {/* Step 2 */}
            <div className="flex flex-col items-center">
              <div className="w-24 h-24 bg-emerald-500/20 border-2 border-emerald-500/50 rounded-lg flex items-center justify-center mb-2">
                <div className="text-center">
                  <FileJson className="w-6 h-6 text-emerald-400 mx-auto mb-1" />
                  <p className="text-xs text-emerald-300 font-medium">Bronze</p>
                </div>
              </div>
            </div>

            {/* Arrow */}
            <div className="text-slate-500 text-2xl">→</div>

            {/* Step 3 */}
            <div className="flex flex-col items-center">
              <div className="w-24 h-24 bg-amber-500/20 border-2 border-amber-500/50 rounded-lg flex items-center justify-center mb-2">
                <div className="text-center">
                  <Zap className="w-6 h-6 text-amber-400 mx-auto mb-1" />
                  <p className="text-xs text-amber-300 font-medium">Silver</p>
                </div>
              </div>
            </div>

            {/* Arrow */}
            <div className="text-slate-500 text-2xl">→</div>

            {/* Step 4 */}
            <div className="flex flex-col items-center">
              <div className="w-24 h-24 bg-purple-500/20 border-2 border-purple-500/50 rounded-lg flex items-center justify-center mb-2">
                <div className="text-center">
                  <TrendingUp className="w-6 h-6 text-purple-400 mx-auto mb-1" />
                  <p className="text-xs text-purple-300 font-medium">Gold</p>
                </div>
              </div>
            </div>

            {/* Arrow */}
            <div className="text-slate-500 text-2xl">→</div>

            {/* Step 5 */}
            <div className="flex flex-col items-center">
              <div className="w-24 h-24 bg-pink-500/20 border-2 border-pink-500/50 rounded-lg flex items-center justify-center mb-2">
                <div className="text-center">
                  <BarChart3 className="w-6 h-6 text-pink-400 mx-auto mb-1" />
                  <p className="text-xs text-pink-300 font-medium">Dashboard</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Key Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-[#1e293b] border border-[#334155] rounded-lg p-4">
          <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            Key Features
          </h3>
          <ul className="space-y-2 text-sm text-slate-400">
            <li className="flex items-start gap-2">
              <span className="text-emerald-400 mt-1">•</span>
              <span>Real-time sentiment analysis across multiple channels</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-400 mt-1">•</span>
              <span>Automated news categorization and tagging</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-400 mt-1">•</span>
              <span>Advanced trend analysis and insights</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-400 mt-1">•</span>
              <span>Multi-source data aggregation and deduplication</span>
            </li>
          </ul>
        </div>

        <div className="bg-[#1e293b] border border-[#334155] rounded-lg p-4">
          <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-blue-400" />
            How It Works
          </h3>
          <ul className="space-y-2 text-sm text-slate-400">
            <li className="flex items-start gap-2">
              <span className="text-blue-400 mt-1">1.</span>
              <span>Articles are continuously scraped from news sources</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-400 mt-1">2.</span>
              <span>Data is processed through the multi-layer pipeline</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-400 mt-1">3.</span>
              <span>Sentiment and categories are assigned using ML models</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-400 mt-1">4.</span>
              <span>Results are displayed in interactive dashboards</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Metadata */}
      <div className="bg-[#1e293b] border border-[#334155] rounded-lg p-4 text-xs text-slate-500">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span>Data Last Updated: {new Date().toLocaleString()}</span>
            <span>•</span>
            <span>Version: 1.0.0</span>
            <span>•</span>
            <span>
              Status: <span className="text-emerald-400">Active</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
