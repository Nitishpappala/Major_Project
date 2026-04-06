import React, { useState, useEffect } from "react";
import { Radio } from "lucide-react";
import { fetchChannels } from "../api";

function SentimentBar({ positive, negative, neutral, total }) {
  const pPct = ((positive / total) * 100).toFixed(0);
  const nPct = ((negative / total) * 100).toFixed(0);
  const neuPct = ((neutral / total) * 100).toFixed(0);

  return (
    <div className="space-y-1.5">
      <div className="flex h-2 rounded-full overflow-hidden bg-[#0f172a]">
        <div
          className="bg-emerald-500 transition-all"
          style={{ width: `${pPct}%` }}
        />
        <div
          className="bg-red-500 transition-all"
          style={{ width: `${nPct}%` }}
        />
        <div
          className="bg-amber-500 transition-all"
          style={{ width: `${neuPct}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-slate-500">
        <span className="text-emerald-400">{pPct}% pos</span>
        <span className="text-red-400">{nPct}% neg</span>
        <span className="text-amber-400">{neuPct}% neu</span>
      </div>
    </div>
  );
}

export default function Channels() {
  const [channels, setChannels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log("Channels component mounted");
    setLoading(true);
    fetchChannels()
      .then((data) => {
        console.log("Channels data received:", data);
        const channelsArray = Array.isArray(data) ? data : [];
        console.log("Setting channels:", channelsArray);
        setChannels(channelsArray);
      })
      .catch((err) => {
        console.error("Failed to fetch channels:", err);
        setError(err.message || "Unknown error");
        setChannels([]);
      })
      .finally(() => {
        console.log("Channels fetch complete");
        setLoading(false);
      });
  }, []);

  if (loading)
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="text-blue-400 mb-2">Loading channels...</div>
          <div className="text-xs text-slate-500">Fetching from API...</div>
        </div>
      </div>
    );
  if (error)
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="text-red-400 mb-2">Error loading channels</div>
          <div className="text-xs text-slate-500">{error}</div>
        </div>
      </div>
    );
  if (channels.length === 0)
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="text-amber-400 mb-2">No channels data</div>
          <div className="text-xs text-slate-500">Check API connection</div>
        </div>
      </div>
    );

  return (
    <div className="space-y-6 w-full">
      {/* Channel Grid */}
      <div>
        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
          All Channels
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {channels.map((ch, i) => (
            <div
              key={i}
              className="bg-[#1e293b] border border-[#334155] rounded-xl p-5 hover:border-[#475569] hover:shadow-lg hover:shadow-black/20 transition-all duration-200"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="text-sm font-semibold text-white">
                    {ch.channel || ch.name || "Unknown"}
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {ch.article_count || 0} articles
                  </p>
                </div>
                <div className="p-2 bg-blue-500/10 rounded-lg border border-blue-500/20">
                  <Radio className="w-4 h-4 text-blue-400" />
                </div>
              </div>

              <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-slate-500">Avg Sentiment</span>
                  {ch.avg_positive !== undefined &&
                    ch.avg_positive !== null && (
                      <span
                        className={`text-sm font-bold font-mono ${
                          ch.avg_positive >= 0.6
                            ? "text-emerald-400"
                            : ch.avg_positive >= 0.4
                              ? "text-amber-400"
                              : "text-red-400"
                        }`}
                      >
                        {(ch.avg_positive * 100).toFixed(1)}%
                      </span>
                    )}
                </div>
                {ch.avg_positive !== undefined && ch.avg_positive !== null && (
                  <div className="h-1.5 bg-[#0f172a] rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${Math.min(ch.avg_positive * 100, 100)}%`,
                        backgroundColor:
                          ch.avg_positive >= 0.6
                            ? "#10b981"
                            : ch.avg_positive >= 0.4
                              ? "#f59e0b"
                              : "#ef4444",
                      }}
                    />
                  </div>
                )}
              </div>

              {ch.avg_positive !== undefined && ch.article_count && (
                <SentimentBar
                  positive={(ch.avg_positive || 0) * ch.article_count}
                  negative={(ch.avg_negative || 0) * ch.article_count}
                  neutral={(ch.avg_neutral || 0) * ch.article_count}
                  total={ch.article_count}
                />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
