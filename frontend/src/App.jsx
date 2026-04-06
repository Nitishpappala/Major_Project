import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import NewsFeed from "./pages/NewsFeed";
import Channels from "./pages/Channels";
import Trends from "./pages/Trends";
import ProjectInfo from "./pages/ProjectInfo";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/feed" element={<NewsFeed />} />
          <Route path="/channels" element={<Channels />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/project" element={<ProjectInfo />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
