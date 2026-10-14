"use client";

import React from "react";
import { WifiOff, RotateCcw, Home } from "lucide-react";
import Link from "next/link";

export default function OfflinePage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6 text-center">
      <div className="w-16 h-16 rounded-3xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-6 shadow-xl shadow-cyan-500/10">
        <WifiOff className="w-8 h-8" />
      </div>

      <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight mb-2">
        You are currently offline
      </h1>
      <p className="text-sm text-slate-400 max-w-sm mb-8 leading-relaxed">
        SwimTrackPro is ready to work offline. Please check your network connection or tap retry once reconnected.
      </p>

      <div className="flex flex-col sm:flex-row items-center gap-3 w-full max-w-xs">
        <button
          onClick={() => window.location.reload()}
          className="w-full py-3 rounded-2xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-500/20 transition flex items-center justify-center gap-2"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Retry Connection</span>
        </button>

        <Link
          href="/"
          className="w-full py-3 rounded-2xl bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 font-bold text-sm transition flex items-center justify-center gap-2"
        >
          <Home className="w-4 h-4" />
          <span>Home</span>
        </Link>
      </div>
    </div>
  );
}
