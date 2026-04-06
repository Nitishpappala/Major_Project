import React from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Newspaper,
  Radio,
  TrendingUp,
  Calendar,
  FileText,
  AlertTriangle,
  GitBranch,
} from "lucide-react";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/project", label: "Lineage", icon: GitBranch },
  { to: "/feed", label: "News Feed", icon: Newspaper },
  { to: "/channels", label: "Channels", icon: Radio },
  { to: "/trends", label: "Trends", icon: TrendingUp },
];

const pageTitles = {
  "/": "Dashboard",
  "/feed": "News Feed",
  "/channels": "Channels",
  "/trends": "Trends",
  "/project": "Lineage",
};

export default function Layout() {
  const location = useLocation();
  const pageTitle = pageTitles[location.pathname] || "Dashboard";
  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="flex min-h-screen w-screen">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 bottom-0 w-[250px] bg-[#1e293b] border-r border-[#334155] flex flex-col z-50">
        {/* Brand */}
        <div className="px-6 py-5 border-b border-[#334155]">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/15 rounded-lg border border-blue-500/20">
              <Newspaper className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">
                NewsIntel
              </h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-widest">
                Sentiment Analytics
              </p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? "bg-blue-500/10 text-blue-400 border-l-2 border-blue-500 ml-0 pl-[10px]"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#293548] border-l-2 border-transparent ml-0 pl-[10px]"
                }`
              }
            >
              <Icon className="w-[18px] h-[18px]" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[#334155]">
          <p className="text-[10px] text-slate-600 uppercase tracking-wider">
            Powered by Databricks
          </p>
        </div>
      </aside>

      {/* Main area */}
      <div className="ml-[250px] flex-1 flex flex-col min-h-screen w-full">
        {/* Content */}
        <main className="flex-1 overflow-auto px-8 py-6 min-h-screen min-w-0 w-full">
          <div className="min-w-0 w-full min-h-full">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
