"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { getInsights } from "@/lib/api";
import { CityInsightRecord } from "@/types";
import { CITY_COORDINATES } from "@/lib/mockData";
import DemoModeBanner from "@/components/DemoModeBanner";

const HotspotMapClient = dynamic(() => import("@/components/HotspotMapClient"), {
  ssr: false,
  loading: () => (
    <div className="mt-4 flex h-[520px] items-center justify-center border border-border text-muted">
      Loading map…
    </div>
  ),
});

export default function HotspotMapPage() {
  const [insights, setInsights] = useState<CityInsightRecord[]>([]);
  const [demoMode, setDemoMode] = useState(false);

  useEffect(() => {
    getInsights().then((res) => {
      setInsights(res.data);
      setDemoMode(res.demoMode);
    });
  }, []);

  return (
    <div className="mx-auto max-w-7xl px-6 py-14">
      <h1 className="font-display text-3xl text-text">Hotspot Map</h1>
      <p className="mt-2 max-w-2xl text-muted">
        Development demand signals across Karnataka, Andhra Pradesh and Kerala.
      </p>

      <div className="mt-4">
        <DemoModeBanner visible={demoMode} />
      </div>

      <div className="mt-8">
        <HotspotMapClient insights={insights} coordinates={CITY_COORDINATES} />
      </div>
    </div>
  );
}
