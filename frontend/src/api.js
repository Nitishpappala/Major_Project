const BASE_URL = "http://localhost:8001/api";

async function request(endpoint, params = {}) {
  const url = new URL(`${BASE_URL}${endpoint}`);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.append(key, value);
    }
  });

  try {
    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

export function fetchDashboard(date) {
  return request("/dashboard", { date });
}

export function fetchDashboardDates() {
  return request("/dashboard/dates");
}

export function fetchArticles(params = {}) {
  return request("/articles", params);
}

export function fetchChannels() {
  return request("/channels").then((data) => {
    console.log("Raw channels response:", data);
    if (data && typeof data === "object") {
      return Array.isArray(data.channels)
        ? data.channels
        : Array.isArray(data)
          ? data
          : [];
    }
    return [];
  });
}

export function fetchCompareChannels(channels, category) {
  return request("/compare", { channels: channels.join(","), category }).then(
    (data) => data.comparison || {},
  );
}

export function fetchCategories() {
  return request("/categories").then((data) => {
    console.log("Raw categories response:", data);
    if (data && typeof data === "object") {
      return Array.isArray(data.categories)
        ? data.categories
        : Array.isArray(data)
          ? data
          : [];
    }
    return [];
  });
}

export function fetchProjectInfo() {
  return request("/project-info").then((data) => {
    console.log("Raw project info response:", data);
    return data || {};
  });
}

export function fetchLineage() {
  return request("/lineage").then((data) => {
    console.log("Raw lineage response:", data);
    return data || {};
  });
}

export function fetchTrends(channel, category) {
  return request("/trends", { channel, category }).then((data) => {
    console.log("Raw trends response:", data);
    if (data && typeof data === "object") {
      return Array.isArray(data.trends)
        ? data.trends
        : Array.isArray(data)
          ? data
          : [];
    }
    return [];
  });
}
