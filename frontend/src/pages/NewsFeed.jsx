import React, { useState, useEffect, useMemo } from "react";
import {
  Search,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  X,
  ExternalLink,
  ArrowUpDown,
} from "lucide-react";
import SentimentBadge from "../components/SentimentBadge";
import { fetchArticles, fetchDashboardDates } from "../api";

const ITEMS_PER_PAGE = 15;

export default function NewsFeed() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedRow, setExpandedRow] = useState(null);
  const [page, setPage] = useState(1);
  const [sortField, setSortField] = useState("article_date");
  const [sortDir, setSortDir] = useState("desc");

  // Filters
  const [channelFilter, setChannelFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [sentimentFilter, setSentimentFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDate, setSelectedDate] = useState("");
  const [availableDates, setAvailableDates] = useState([]);

  useEffect(() => {
    fetchArticles({
      per_page: 100,
      date: selectedDate,
      channel: channelFilter,
      category: categoryFilter,
      sentiment: sentimentFilter,
      search: searchQuery,
    })
      .then((data) =>
        setArticles(Array.isArray(data) ? data : data?.articles || []),
      )
      .catch(() => setArticles([]))
      .finally(() => setLoading(false));
  }, [
    selectedDate,
    channelFilter,
    categoryFilter,
    sentimentFilter,
    searchQuery,
  ]);

  useEffect(() => {
    fetchDashboardDates()
      .then((dates) => {
        setAvailableDates(Array.isArray(dates) ? dates : []);
      })
      .catch(() => {
        setAvailableDates([]);
      });
  }, []);

  const uniqueChannels = [...new Set(articles.map((a) => a.channel))];
  const uniqueCategories = [...new Set(articles.map((a) => a.category))];
  const sentimentOptions = ["positive", "negative", "neutral"];

  const filtered = useMemo(() => {
    let result = [...articles];

    result.sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];
      if (typeof valA === "string") valA = valA.toLowerCase();
      if (typeof valB === "string") valB = valB.toLowerCase();
      if (valA < valB) return sortDir === "asc" ? -1 : 1;
      if (valA > valB) return sortDir === "asc" ? 1 : -1;
      return 0;
    });

    return result;
  }, [articles, sortField, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE));
  const paginated = filtered.slice(
    (page - 1) * ITEMS_PER_PAGE,
    page * ITEMS_PER_PAGE,
  );

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("asc");
    }
    setPage(1);
  };

  const clearFilters = () => {
    setChannelFilter("");
    setCategoryFilter("");
    setSentimentFilter("");
    setSearchQuery("");
    setSelectedDate("");
    setPage(1);
  };

  const hasFilters =
    channelFilter ||
    categoryFilter ||
    sentimentFilter ||
    searchQuery ||
    selectedDate;

  const SortHeader = ({ field, children }) => (
    <th
      className="text-left py-3 px-3 text-slate-500 font-medium text-xs uppercase tracking-wider cursor-pointer hover:text-slate-300 transition-colors select-none"
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center gap-1">
        {children}
        <ArrowUpDown
          className={`w-3 h-3 ${sortField === field ? "text-blue-400" : "text-slate-600"}`}
        />
      </div>
    </th>
  );

  return (
    <div className="space-y-4 w-full">
      {/* Filter Bar */}
      <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search articles..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all"
            />
          </div>

          <select
            value={channelFilter}
            onChange={(e) => {
              setChannelFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-slate-300 focus:outline-none focus:border-blue-500/50 appearance-none cursor-pointer min-w-[150px]"
          >
            <option value="">All Channels</option>
            {uniqueChannels.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-slate-300 focus:outline-none focus:border-blue-500/50 appearance-none cursor-pointer min-w-[140px]"
          >
            <option value="">All Categories</option>
            {uniqueCategories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          <select
            value={sentimentFilter}
            onChange={(e) => {
              setSentimentFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-slate-300 focus:outline-none focus:border-blue-500/50 appearance-none cursor-pointer min-w-[140px]"
          >
            <option value="">All Sentiments</option>
            {sentimentOptions.map((s) => (
              <option key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>

          <select
            value={selectedDate}
            onChange={(e) => {
              setSelectedDate(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 bg-[#0f172a] border border-[#334155] rounded-lg text-sm text-slate-300 focus:outline-none focus:border-blue-500/50 appearance-none cursor-pointer min-w-[140px]"
          >
            <option value="">All dates</option>
            {availableDates.map((date) => (
              <option key={date} value={date}>
                {date}
              </option>
            ))}
          </select>

          {hasFilters && (
            <button
              onClick={clearFilters}
              className="flex items-center gap-1.5 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg text-xs text-red-400 hover:bg-red-500/20 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
              Clear
            </button>
          )}

          <div className="ml-auto text-xs text-slate-500">
            {filtered.length} article{filtered.length !== 1 ? "s" : ""}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1e293b] border border-[#334155] rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#334155] bg-[#1a2536]">
                <SortHeader field="heading">Heading</SortHeader>
                <SortHeader field="channel">Channel</SortHeader>
                <SortHeader field="category">Category</SortHeader>
                <SortHeader field="sentiment_label">Sentiment</SortHeader>
                <SortHeader field="positive_score">Pos%</SortHeader>
                <SortHeader field="negative_score">Neg%</SortHeader>
                <th className="py-3 px-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Neu%
                </th>
                <SortHeader field="article_date">Date</SortHeader>
              </tr>
            </thead>
            <tbody>
              {paginated.map((article) => (
                <React.Fragment key={article.id}>
                  <tr
                    className={`border-b border-[#334155]/50 cursor-pointer transition-colors ${
                      expandedRow === article.id
                        ? "bg-[#293548]"
                        : "hover:bg-[#293548]/50"
                    }`}
                    onClick={() =>
                      setExpandedRow(
                        expandedRow === article.id ? null : article.id,
                      )
                    }
                  >
                    <td className="py-3 px-3 text-slate-200 font-medium max-w-[300px]">
                      <div className="flex items-center gap-2">
                        {expandedRow === article.id ? (
                          <ChevronUp className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        )}
                        <span className="truncate">{article.heading}</span>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-slate-400 whitespace-nowrap">
                      {article.channel}
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-xs rounded-md border border-blue-500/20">
                        {article.category}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <SentimentBadge sentiment={article.sentiment_label} />
                    </td>
                    <td className="py-3 px-3 text-emerald-400 font-mono text-xs">
                      {(article.positive_score * 100).toFixed(1)}
                    </td>
                    <td className="py-3 px-3 text-red-400 font-mono text-xs">
                      {(article.negative_score * 100).toFixed(1)}
                    </td>
                    <td className="py-3 px-3 text-amber-400 font-mono text-xs">
                      {(
                        (1 - article.positive_score - article.negative_score) *
                        100
                      ).toFixed(1)}
                    </td>
                    <td className="py-3 px-3 text-slate-500 whitespace-nowrap text-xs">
                      {article.article_date}
                    </td>
                  </tr>

                  {/* Expanded content */}
                  {expandedRow === article.id && (
                    <tr className="bg-[#293548]">
                      <td colSpan={8} className="px-6 py-4">
                        <div className="pl-6 space-y-3">
                          <p className="text-sm text-slate-300 leading-relaxed">
                            {article.body_cleaned || "No body text available."}
                          </p>
                          {article.url && (
                            <a
                              href={article.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                              View original article
                            </a>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
              {paginated.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
                    No articles found matching your filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-[#334155] bg-[#1a2536]">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#0f172a] border border-[#334155] rounded-lg text-xs text-slate-400 hover:text-white hover:border-[#475569] disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            Previous
          </button>

          <span className="text-xs text-slate-500">
            Page <span className="text-slate-300 font-medium">{page}</span> of{" "}
            <span className="text-slate-300 font-medium">{totalPages}</span>
          </span>

          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#0f172a] border border-[#334155] rounded-lg text-xs text-slate-400 hover:text-white hover:border-[#475569] disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            Next
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
