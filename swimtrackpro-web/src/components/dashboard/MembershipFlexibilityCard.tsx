"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  PauseCircle,
  PlayCircle,
  AlertTriangle,
  CheckCircle2,
  Clock,
} from "lucide-react";
import { pauseBookingAction, resumeBookingAction } from "@/app/actions/dashboard";

interface MembershipFlexibilityCardProps {
  packageData: {
    bookingId: string;
    packageName: string;
    trainerName: string;
    startDate: string;
    endDate: string;
    timeSlot: string;
    location: string;
    status: string;
    pauseStatus: string;
    autoResumeDate?: string;
    allocatedPauseDays: number;
    usedPauseDays: number;
    availablePauseDays: number;
    isPausable: boolean;
    totalClasses: number;
    completedClasses: number;
    remainingClasses: number;
    skipsAllowed: number;
    skipsUsed: number;
    skipsRemaining: number;
  };
}

export function MembershipFlexibilityCard({ packageData }: MembershipFlexibilityCardProps) {
  const [showPauseModal, setShowPauseModal] = useState(false);
  const [pauseDays, setPauseDays] = useState(7);
  const [reason, setReason] = useState("Travel / Vacation");
  const [otherReason, setOtherReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<{ message: string; isError: boolean } | null>(null);

  const isPaused = packageData.pauseStatus === "PAUSED";
  const progressPercent = Math.min(
    100,
    Math.round((packageData.completedClasses / Math.max(1, packageData.totalClasses)) * 100)
  );

  const handlePauseSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setActionFeedback(null);
    try {
      const fd = new FormData();
      fd.append("bookingId", packageData.bookingId);
      fd.append("pauseDays", pauseDays.toString());
      fd.append("reason", reason);
      if (otherReason) fd.append("otherReason", otherReason);

      const res = await pauseBookingAction(fd);
      if (res.success) {
        setActionFeedback({ message: res.message || "Membership paused.", isError: false });
        setTimeout(() => {
          setShowPauseModal(false);
          setActionFeedback(null);
        }, 2000);
      } else {
        setActionFeedback({ message: res.error || "Pause failed.", isError: true });
      }
    } catch {
      setActionFeedback({ message: "Network error", isError: true });
    } finally {
      setLoading(false);
    }
  };

  const handleResumeNow = async () => {
    setLoading(true);
    setActionFeedback(null);
    try {
      const res = await resumeBookingAction(packageData.bookingId);
      if (res.success) {
        setActionFeedback({ message: res.message || "Membership resumed!", isError: false });
        setTimeout(() => setActionFeedback(null), 3000);
      } else {
        setActionFeedback({ message: res.error || "Resume failed.", isError: true });
      }
    } catch {
      setActionFeedback({ message: "Network error", isError: true });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-3xl bg-slate-900/90 border border-slate-800 p-6 backdrop-blur flex flex-col justify-between relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 blur-3xl pointer-events-none rounded-full" />

      <div>
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 mb-2">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>{isPaused ? "MEMBERSHIP PAUSED" : "ACTIVE MEMBERSHIP"}</span>
            </div>
            <h3 className="text-xl font-black text-white tracking-tight">
              {packageData.packageName}
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Coach: <span className="text-slate-200 font-medium">{packageData.trainerName}</span> • {packageData.timeSlot}
            </p>
          </div>

          <div className="text-right">
            <span className="text-xs text-slate-400 block">Valid Until</span>
            <span className="text-sm font-bold text-slate-100">{packageData.endDate || "--"}</span>
          </div>
        </div>

        {/* Attendance Progress */}
        <div className="space-y-1.5 my-5">
          <div className="flex justify-between text-xs font-semibold">
            <span className="text-slate-400">
              Completed <strong className="text-cyan-400">{packageData.completedClasses}</strong> of {packageData.totalClasses} classes
            </span>
            <span className="text-cyan-400">{progressPercent}%</span>
          </div>
          <div className="w-full h-2.5 rounded-full bg-slate-950 border border-slate-800 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Action feedback message */}
        {actionFeedback && (
          <div
            className={`p-3 rounded-2xl text-xs font-semibold mb-4 flex items-center gap-2 ${
              actionFeedback.isError
                ? "bg-rose-500/10 text-rose-300 border border-rose-500/20"
                : "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
            }`}
          >
            {actionFeedback.isError ? (
              <AlertTriangle className="w-4 h-4 shrink-0" />
            ) : (
              <CheckCircle2 className="w-4 h-4 shrink-0" />
            )}
            <span>{actionFeedback.message}</span>
          </div>
        )}

        {/* If Paused Alert State */}
        {isPaused ? (
          <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 mb-4">
            <div className="flex items-center gap-2 text-amber-300 font-bold text-xs mb-1">
              <Clock className="w-4 h-4" />
              <span>Membership currently paused</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed mb-3">
              Your remaining classes are on hold. Auto-resumes on{" "}
              <strong className="text-white">{packageData.autoResumeDate || "scheduled date"}</strong>.
            </p>
            <button
              onClick={handleResumeNow}
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 transition flex items-center justify-center gap-2"
            >
              <PlayCircle className="w-4 h-4" />
              <span>{loading ? "Resuming..." : "Resume Membership Early"}</span>
            </button>
          </div>
        ) : (
          /* Flexibility stats row */
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800">
              <span className="text-[11px] font-semibold text-slate-400 block mb-0.5">
                Pause Balance
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-lg font-black text-white">
                  {packageData.isPausable ? packageData.availablePauseDays : "0"}
                </span>
                <span className="text-[11px] text-slate-400">
                  {packageData.isPausable ? `/ ${packageData.allocatedPauseDays} days` : "(N/A)"}
                </span>
              </div>
              <p className="text-[10px] text-slate-500 mt-1">
                {packageData.isPausable ? "Zero fee carry-forward" : "3 skips included instead"}
              </p>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800">
              <span className="text-[11px] font-semibold text-slate-400 block mb-0.5">
                Make-up Skips
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-lg font-black text-cyan-400">
                  {packageData.skipsRemaining}
                </span>
                <span className="text-[11px] text-slate-400">
                  / {packageData.skipsAllowed} available
                </span>
              </div>
              <p className="text-[10px] text-slate-500 mt-1">60-day validity credit</p>
            </div>
          </div>
        )}
      </div>

      {/* Buttons Footer */}
      {!isPaused && (
        <div className="pt-2">
          {packageData.isPausable ? (
            <button
              onClick={() => setShowPauseModal(true)}
              disabled={packageData.availablePauseDays <= 0}
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 text-xs font-bold transition border border-slate-700 flex items-center justify-center gap-2"
            >
              <PauseCircle className="w-4 h-4 text-cyan-400" />
              <span>Pause Membership ({packageData.availablePauseDays}d remaining)</span>
            </button>
          ) : (
            <div className="text-center p-2 rounded-xl bg-slate-950/40 border border-slate-800/80 text-[11px] text-slate-400">
              Monthly packages include 3 skip credits with make-up rescheduling.
            </div>
          )}
        </div>
      )}

      {/* Pause Modal */}
      {showPauseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <form
            onSubmit={handlePauseSubmit}
            className="bg-slate-900 border border-slate-700 rounded-3xl max-w-md w-full p-6 shadow-2xl relative"
          >
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm">
                <PauseCircle className="w-4 h-4" />
                <span>Pause Membership</span>
              </div>
              <button
                type="button"
                onClick={() => setShowPauseModal(false)}
                className="text-slate-400 hover:text-white text-xs font-bold px-2 py-1 bg-slate-800 rounded-lg"
              >
                Cancel
              </button>
            </div>

            <div className="py-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Select Pause Duration (Days)
                </label>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min={1}
                    max={packageData.availablePauseDays}
                    value={pauseDays}
                    onChange={(e) => setPauseDays(parseInt(e.target.value, 10))}
                    className="flex-1 accent-cyan-400"
                  />
                  <span className="w-16 text-center py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-cyan-400 font-bold text-sm">
                    {pauseDays} d
                  </span>
                </div>
                <span className="text-[11px] text-slate-400 mt-1 block">
                  Remaining balance after pause: {packageData.availablePauseDays - pauseDays} days
                </span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Reason for Pause
                </label>
                <select
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400"
                >
                  <option value="Travel / Vacation">Travel / Vacation</option>
                  <option value="Medical / Health / Injury">Medical / Health / Injury</option>
                  <option value="Work / Exam Schedule">Work / Exam Schedule</option>
                  <option value="Personal Reasons">Personal Reasons</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              {reason === "Other" && (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Specify Reason
                  </label>
                  <input
                    type="text"
                    required
                    value={otherReason}
                    onChange={(e) => setOtherReason(e.target.value)}
                    placeholder="Brief description..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400"
                  />
                </div>
              )}

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
                <span className="text-slate-300 font-semibold block mb-0.5">
                  How Pause Works:
                </span>
                All remaining classes are automatically shifted forward by {pauseDays} days. No classes or money are forfeited!
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowPauseModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white"
              >
                Keep Active
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition"
              >
                {loading ? "Confirming..." : `Pause for ${pauseDays} Days`}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
