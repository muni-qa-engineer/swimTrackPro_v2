import React from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Sparkles,
  ArrowRight,
  MapPin,
  PauseCircle,
} from "lucide-react";

import { Navbar } from "@/components/common/Navbar";

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      {/* Hero Section */}
      <main className="flex-1">
        <section className="relative overflow-hidden py-16 sm:py-24 px-4 sm:px-6 lg:px-8 text-center max-w-5xl mx-auto">
          {/* Subtle gradient glow behind hero */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-cyan-500/10 blur-[120px] pointer-events-none rounded-full" />

          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-bold mb-6">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Modern Next.js 15 Full-Stack Platform</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-black text-white tracking-tight leading-tight">
            Doorstep Swimming Academy. <br />
            <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-emerald-400 bg-clip-text text-transparent">
              Elevate Every Stroke.
            </span>
          </h1>

          <p className="mt-5 text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Personalized swim training at your apartment, society, or clubhouse pool. Certified coaches, flexible schedules, and real-time student attendance tracking.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row gap-3.5 justify-center items-center">
            <Link
              href="/booking"
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-cyan-400 hover:from-cyan-400 hover:to-cyan-300 text-slate-950 font-bold transition shadow-xl shadow-cyan-500/25 flex items-center justify-center gap-2 text-base"
            >
              <span>Book Doorstep Session</span>
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>

          {/* Value Props Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-16 text-left">
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center mb-3">
                <MapPin className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-white">Doorstep Convenience</h3>
              <p className="text-xs text-slate-400 mt-1">
                Coaches travel directly to your society pool. GPS detection auto-fills your location.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-3">
                <PauseCircle className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-white">Pause & Flexibility</h3>
              <p className="text-xs text-slate-400 mt-1">
                Freeze packages during exams or travel without wasting days. Automatic calendar extension.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center mb-3">
                <Sparkles className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-white">Group Batch Scaling</h3>
              <p className="text-xs text-slate-400 mt-1">
                Train with up to 5 friends or siblings and unlock dynamic discounts up to 36% OFF.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center mb-3">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-white">Verified Coaches</h3>
              <p className="text-xs text-slate-400 mt-1">
                Background-checked, certified swimming coaches with verified ratings and reviews.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-8 text-center text-xs text-slate-500">
        <p>© {new Date().getFullYear()} SwimTrackPro. Next-generation swimming academy management.</p>
      </footer>
    </div>
  );
}
