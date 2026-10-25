"use client";

import React from "react";
import { Ticket, Calendar, ShieldCheck, ArrowRight } from "lucide-react";
import Link from "next/link";

interface MakeUpCreditsCardProps {
  creditsCount: number;
  studentName?: string;
  packageName?: string;
}

export function MakeUpCreditsCard({
  creditsCount,
  studentName = "Swimmer",
  packageName = "Doorstep Membership",
}: MakeUpCreditsCardProps) {
  // If credit is 0, render absolutely nothing per user requirement
  if (!creditsCount || creditsCount <= 0) {
    return null;
  }

  return (
    <div className="rounded-3xl bg-gradient-to-br from-cyan-950/40 via-slate-900/90 to-slate-900 border border-cyan-500/30 p-6 backdrop-blur shadow-xl shadow-cyan-950/20 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-2xl bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
            <Ticket className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Make-up Sessions Available</h3>
            <p className="text-xs text-slate-400">Flexible rescheduling for missed classes</p>
          </div>
        </div>

        <span className="px-3 py-1 rounded-full text-xs font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/20">
          {creditsCount} Credit{creditsCount > 1 ? "s" : ""}
        </span>
      </div>

      <p className="text-xs text-slate-300 leading-relaxed">
        You have <strong className="text-white">{creditsCount} available make-up credit{creditsCount > 1 ? "s" : ""}</strong> from missed classes. You can reschedule replacement slots at your convenience.
      </p>

      <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 flex items-center justify-between gap-3">
        <div className="space-y-0.5">
          <div className="text-xs font-bold text-white flex items-center gap-2">
            <span>🏊 {studentName}</span>
            <span className="text-[10px] font-semibold text-slate-400 bg-slate-800 px-2 py-0.5 rounded-md">
              {packageName}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 flex items-center gap-1 mt-1">
            <Calendar className="w-3 h-3 text-cyan-400" />
            <span>Valid until package expiry</span>
          </p>
        </div>

        <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          Available
        </span>
      </div>

      <div className="pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>Package end date is completely unaffected.</span>
        </div>

        <Link
          href="/calendar"
          className="w-full sm:w-auto px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold transition flex items-center justify-center gap-1.5 shadow-md shadow-cyan-500/20"
        >
          <span>Reschedule Class</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
}
