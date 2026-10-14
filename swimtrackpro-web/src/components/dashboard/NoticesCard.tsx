"use client";

import React from "react";
import { Bell } from "lucide-react";

interface NoticesCardProps {
  notices: {
    id: number;
    authorName: string;
    message: string;
    createdAt: string;
  }[];
}

export function NoticesCard({ notices }: NoticesCardProps) {
  if (!notices || notices.length === 0) return null;

  return (
    <div className="rounded-3xl bg-slate-900/90 border border-slate-800 p-6 backdrop-blur">
      <div className="flex items-center gap-2.5 mb-4">
        <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
          <Bell className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-base font-bold text-white">Academy Announcements</h3>
          <p className="text-xs text-slate-400">Updates from coaches & admin</p>
        </div>
      </div>

      <div className="space-y-3">
        {notices.map((n) => (
          <div
            key={n.id}
            className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex items-start gap-3"
          >
            <div className="w-2 h-2 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
            <div>
              <p className="text-xs text-slate-200 leading-relaxed">{n.message}</p>
              <div className="flex items-center gap-2 mt-1.5 text-[10px] text-slate-500 font-medium">
                <span>By {n.authorName}</span>
                <span>•</span>
                <span>{n.createdAt.split("T")[0]}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
