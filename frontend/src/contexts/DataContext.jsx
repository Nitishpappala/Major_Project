import React, { createContext, useContext, useState, useEffect } from "react";
import {
  fetchDashboard,
  fetchArticles,
  fetchChannels,
  fetchAlerts,
  fetchTrends,
} from "../api";

const DataContext = createContext();

export const useData = () => useContext(DataContext);

export const DataProvider = ({ children }) => {
  const [data, setData] = useState({
    dashboard: null,
    articles: [],
    channels: [],
    alerts: [],
    trends: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [
          dashboardData,
          articlesData,
          channelsData,
          alertsData,
          trendsData,
        ] = await Promise.all([
          fetchDashboard(),
          fetchArticles({ per_page: 1000 }), // fetch more articles
          fetchChannels(),
          fetchAlerts(),
          fetchTrends(),
        ]);
        setData({
          dashboard: dashboardData,
          articles: Array.isArray(articlesData)
            ? articlesData
            : articlesData?.articles || [],
          channels: Array.isArray(channelsData)
            ? channelsData
            : channelsData?.channels || [],
          alerts: Array.isArray(alertsData)
            ? alertsData
            : alertsData?.alerts || [],
          trends: Array.isArray(trendsData)
            ? trendsData
            : trendsData?.trends || [],
        });
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  return (
    <DataContext.Provider value={{ data, loading, error }}>
      {children}
    </DataContext.Provider>
  );
};
