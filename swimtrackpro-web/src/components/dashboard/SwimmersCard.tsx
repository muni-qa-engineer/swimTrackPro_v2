"use client";

import React from "react";
import { Users, Award, Plus } from "lucide-react";
import Link from "next/link";
import { SwimmerInfo } from "@/app/actions/dashboard";

interface SwimmersCardProps {
  swimmers: SwimmerInfo[];
}

export function SwimmersCard({ swimmers }: SwimmersCardProps) {
  const getBadgeColor = (level: string) => {
    switch (level.toLowerCase()) {
      case "advanced":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "intermediate":
        return "bg-cyan-500/10 text-cyan-400 border-cyan-500/20";
      default:
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
    }
  };

  return (
    <div className="rounded-3xl bg-slate-900/90 border border-slate-800 p-6 backdrop-blur">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Users className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Registered Swimmers</h3>
            <p className="text-xs text-slate-400">{swimmers.length} Member{swimmers.length > 1 ? "s" : ""}</p>
          </div>
        </div>

        <Link
          href="/booking"
          className="text-xs font-bold text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add Swimmer</span>
        </Link>
      </div>

      <div className="space-y-3">
        {swimmers.map((s, idx) => (
          <div
            key={s.id || idx}
            className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-cyan-600/10">
                {s.name.charAt(0).toUpperCase()}
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">{s.name}</h4>
                <span className="text-[11px] text-slate-400 flex items-center gap-1">
                  <Award className="w-3 h-3 text-cyan-400" />
                  <span>Doorstep Student</span>
                </span>
              </div>
            </div>

            <span
              className={`px-2.5 py-1 rounded-full text-[11px] font-bold border ${getBadgeColor(
                s.skillLevel
              )}`}
            >
              {s.skillLevel}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
