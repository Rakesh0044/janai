"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import KpiCard from "@/components/KpiCard";
import DemoModeBanner from "@/components/DemoModeBanner";
import { getDashboardSummary } from "@/lib/api";
import { DashboardSummary } from "@/types";

const BAND_COLORS: Record<string, string> = {
  LOW: "#4A9291",
  MODERATE: "#C98A2C",
  HIGH: "#C24D3D",
};

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [demoMode, setDemoMode] = useState(false);

  useEffect(() => {
    getDashboardSummary().then((res) => {
      setSummary(res.data);
      setDemoMode(res.demoMode);
    });
  }, []);

  if (!summary) {
    return (
      <div className="mx-auto max-w-7xl px-6 py-14">
        <p className="text-muted">Loading dashboard…</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-14">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-text">Development Intelligence Dashboard</h1>
          <p className="mt-2 text-muted">A live view of citizen demand across covered cities.</p>
        </div>
      </div>

      <div className="mt-4">
        <DemoModeBanner visible={demoMode} />
      </div>

      <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-4">
        <KpiCard label="Citizen Requests" value={summary.total_requests.toLocaleString()} />
        <KpiCard label="Active Hotspots" value={summary.active_hotspots} />
        <KpiCard label="High Priority Insights" value={summary.high_priority_insights} />
        <KpiCard label="Cities Covered" value={summary.cities_covered} />
      </div>

      <div className="mt-10 grid gap-4 lg:grid-cols-3">
        <div className="border border-border bg-surface p-6 lg:col-span-2">
          <h2 className="font-medium text-text">Requests by Category</h2>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={summary.category_distribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="#28374F" vertical={false} />
                <XAxis dataKey="category" stroke="#8C99AC" fontSize={12} />
                <YAxis stroke="#8C99AC" fontSize={12} />
                <Tooltip
                  contentStyle={{ background: "#152238", border: "1px solid #28374F", color: "#E9EEF3" }}
                />
                <Bar dataKey="count" fill="#4A9291" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="border border-border bg-surface p-6">
          <h2 className="font-medium text-text">Hotspot Distribution</h2>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={summary.hotspot_distribution}
                  dataKey="count"
                  nameKey="band"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={2}
                >
                  {summary.hotspot_distribution.map((entry) => (
                    <Cell key={entry.band} fill={BAND_COLORS[entry.band]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "#152238", border: "1px solid #28374F", color: "#E9EEF3" }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="mt-2 flex justify-center gap-4 text-xs text-muted">
            {summary.hotspot_distribution.map((entry) => (
              <li key={entry.band} className="flex items-center gap-1.5">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ background: BAND_COLORS[entry.band] }}
                />
                {entry.band} ({entry.count})
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-4 border border-border bg-surface p-6">
        <h2 className="font-medium text-text">Requests by State</h2>
        <div className="mt-4 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={summary.state_distribution} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#28374F" horizontal={false} />
              <XAxis type="number" stroke="#8C99AC" fontSize={12} />
              <YAxis type="category" dataKey="state" stroke="#8C99AC" fontSize={12} width={110} />
              <Tooltip
                contentStyle={{ background: "#152238", border: "1px solid #28374F", color: "#E9EEF3" }}
              />
              <Bar dataKey="count" fill="#C98A2C" radius={[0, 2, 2, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
