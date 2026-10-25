"use client";

import React, { useState } from "react";
import {
  MapPin,
  Phone,
  CheckCircle,
  XCircle,
  UserCheck,
  Bell,
} from "lucide-react";
import { markAttendanceAction } from "@/app/actions/dashboard";

interface SessionItem {
  bookingId: string;
  studentName: string;
  time: string;
  location: string;
  packageName: string;
  phone: string;
  status: "present" | "absent" | "pending";
}

interface TrainerAttendanceTrackerProps {
  todaySessions: SessionItem[];
  todayDateStr: string;
}

export function TrainerAttendanceTracker({
  todaySessions,
  todayDateStr,
}: TrainerAttendanceTrackerProps) {
  const [sessions, setSessions] = useState<SessionItem[]>(todaySessions);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleMark = async (
    bookingId: string,
    status: "present" | "absent"
  ) => {
    setLoadingId(bookingId);
    setMessage(null);
    try {
      const todayIso = new Date().toISOString().split("T")[0];
      const res = await markAttendanceAction(bookingId, todayIso, status);
      if (res.success) {
        setSessions((prev) =>
          prev.map((s) => (s.bookingId === bookingId ? { ...s, status } : s))
        );
        setMessage(`Marked ${status} for ${bookingId}`);
        setTimeout(() => setMessage(null), 3000);
      }
    } catch {
      setMessage("Failed to update status");
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="rounded-3xl bg-slate-900/90 border border-slate-800 p-6 backdrop-blur space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Today&apos;s Coaching Agenda</h3>
            <p className="text-xs text-slate-400">{todayDateStr}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={async () => {
              if ("Notification" in window) {
                const res = await Notification.requestPermission();
                if (res === "granted") {
                  setMessage("Mobile PWA Push Notifications enabled!");
                  setTimeout(() => setMessage(null), 3000);
                }
              }
            }}
            className="px-3 py-1 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-500/20 transition flex items-center gap-1.5"
          >
            <Bell className="w-3.5 h-3.5 text-cyan-400" />
            <span>Enable Push Alerts</span>
          </button>

          <span className="text-xs font-bold px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 self-start sm:self-auto">
            {sessions.length} Session{sessions.length > 1 ? "s" : ""} Scheduled
          </span>
        </div>
      </div>

      {message && (
        <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-xs font-semibold text-cyan-300">
          {message}
        </div>
      )}

      {sessions.length === 0 ? (
        <div className="text-center py-10 text-xs text-slate-500">
          No training sessions scheduled for today.
        </div>
      ) : (
        <div className="space-y-3">
          {sessions.map((item) => (
            <div
              key={item.bookingId}
              className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-white">
                    {item.studentName}
                  </span>
                  <span className="text-[11px] font-semibold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded-full border border-cyan-500/20">
                    {item.time}
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-500" />
                    <span>{item.location}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <Phone className="w-3.5 h-3.5 text-slate-500" />
                    <a
                      href={`tel:${item.phone}`}
                      className="hover:text-cyan-400 underline decoration-slate-600"
                    >
                      {item.phone}
                    </a>
                  </span>
                </div>
              </div>

              {/* Attendance action buttons */}
              <div className="flex items-center gap-2 self-start md:self-auto">
                <button
                  onClick={() => handleMark(item.bookingId, "present")}
                  disabled={loadingId === item.bookingId}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 border ${
                    item.status === "present"
                      ? "bg-emerald-500 text-slate-950 border-emerald-400 shadow-lg shadow-emerald-500/20"
                      : "bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                  }`}
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>Yes, Completed (+1)</span>
                </button>

                <button
                  onClick={() => handleMark(item.bookingId, "absent")}
                  disabled={loadingId === item.bookingId}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 border ${
                    item.status === "absent"
                      ? "bg-rose-500 text-white border-rose-400 shadow-lg shadow-rose-500/20"
                      : "bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border-rose-500/30"
                  }`}
                >
                  <XCircle className="w-4 h-4" />
                  <span>No, Missed (+1 Make-up)</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
