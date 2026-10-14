"use client";

import React, { useState } from "react";
import { CalendarDayInfo } from "@/app/actions/dashboard";
import { Calendar, AlertCircle, CheckCircle2 } from "lucide-react";

interface AttendanceCalendarProps {
  monthName: string;
  calendarDays: CalendarDayInfo[];
  bookingId?: string;
  onSkipSession: (bookingId: string, dateStr: string) => Promise<{ success: boolean; message?: string; error?: string }>;
}

export function AttendanceCalendar({
  monthName,
  calendarDays,
  bookingId,
  onSkipSession,
}: AttendanceCalendarProps) {
  const [selectedDay, setSelectedDay] = useState<CalendarDayInfo | null>(null);
  const [skipLoading, setSkipLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ message: string; isError: boolean } | null>(null);

  const dayHeaders = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  const handleSkip = async () => {
    if (!selectedDay || !bookingId) return;
    setSkipLoading(true);
    setFeedback(null);
    try {
      const res = await onSkipSession(bookingId, selectedDay.dateStr);
      if (res.success) {
        setFeedback({ message: res.message || "Class skipped! 1 Make-up credit added.", isError: false });
        setTimeout(() => {
          setSelectedDay(null);
          setFeedback(null);
        }, 2500);
      } else {
        setFeedback({ message: res.error || "Could not skip session.", isError: true });
      }
    } catch {
      setFeedback({ message: "Network error", isError: true });
    } finally {
      setSkipLoading(false);
    }
  };

  return (
    <div className="rounded-3xl bg-slate-900/90 border border-slate-800 p-6 backdrop-blur">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Calendar className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Attendance Calendar</h3>
            <p className="text-xs text-slate-400">{monthName}</p>
          </div>
        </div>

        {/* Legend */}
        <div className="hidden sm:flex items-center gap-4 text-xs font-semibold">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400/50" />
            <span className="text-slate-300">Class Booked</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
            <span className="text-slate-300">Paused</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full ring-2 ring-cyan-500" />
            <span className="text-slate-300">Today</span>
          </div>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-7 gap-2 text-center">
        {dayHeaders.map((dh) => (
          <div key={dh} className="text-xs font-bold text-slate-500 uppercase tracking-wider py-2">
            {dh}
          </div>
        ))}

        {calendarDays.map((item, idx) => {
          if (!item.day) {
            return <div key={`empty-${idx}`} className="h-14 sm:h-16 rounded-xl bg-slate-950/20" />;
          }

          let bgClasses = "bg-slate-950/60 border border-slate-800/80 text-slate-300 hover:border-slate-700";
          if (item.isToday) {
            bgClasses = "bg-cyan-500/15 border-2 border-cyan-400 text-cyan-300 font-bold shadow-lg shadow-cyan-500/10";
          }
          if (item.isPaused) {
            bgClasses = "bg-amber-500/10 border border-amber-500/30 text-amber-300";
          } else if (item.isBooked) {
            bgClasses = "bg-cyan-950/50 border border-cyan-500/40 text-cyan-200 hover:bg-cyan-900/50";
          }

          return (
            <button
              key={`day-${item.day}`}
              onClick={() => item.isBooked ? setSelectedDay(item) : null}
              disabled={!item.isBooked}
              className={`h-14 sm:h-16 rounded-2xl flex flex-col items-center justify-between p-2 transition relative ${bgClasses} ${
                item.isBooked ? "cursor-pointer group" : "cursor-default"
              }`}
            >
              <span className="text-xs sm:text-sm font-semibold">{item.day}</span>
              {item.isBooked && (
                <div className="w-full">
                  <span className="block text-[10px] font-bold text-cyan-400 bg-cyan-500/20 rounded py-0.5 px-1 truncate">
                    {item.sessionTitle || "Class"}
                  </span>
                </div>
              )}
              {item.isPaused && (
                <div className="w-full">
                  <span className="block text-[9px] font-bold text-amber-400 bg-amber-500/20 rounded py-0.5 truncate">
                    Paused
                  </span>
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Session Details / Skip Modal */}
      {selectedDay && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-slate-900 border border-slate-700 rounded-3xl max-w-md w-full p-6 shadow-2xl relative">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm">
                <Calendar className="w-4 h-4" />
                <span>Class Details</span>
              </div>
              <button
                onClick={() => { setSelectedDay(null); setFeedback(null); }}
                className="text-slate-400 hover:text-white text-xs font-bold px-2 py-1 bg-slate-800 rounded-lg"
              >
                Close
              </button>
            </div>

            <div className="py-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Date</span>
                <span className="text-sm font-bold text-white">{selectedDay.dateStr}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Time Slot</span>
                <span className="text-sm font-bold text-cyan-400">{selectedDay.sessionTitle || "06:00 AM"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Status</span>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                  Scheduled Active
                </span>
              </div>

              <div className="mt-4 p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 leading-relaxed">
                <p className="font-semibold text-slate-200 mb-1">Need to reschedule?</p>
                You can skip this class up to 6 hours before start time and receive an instant make-up credit valid for 60 days.
              </div>

              {feedback && (
                <div
                  className={`p-3 rounded-xl text-xs font-semibold flex items-center gap-2 ${
                    feedback.isError
                      ? "bg-rose-500/10 text-rose-300 border border-rose-500/20"
                      : "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                  }`}
                >
                  {feedback.isError ? <AlertCircle className="w-4 h-4 shrink-0" /> : <CheckCircle2 className="w-4 h-4 shrink-0" />}
                  <span>{feedback.message}</span>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => { setSelectedDay(null); setFeedback(null); }}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white"
              >
                Dismiss
              </button>
              <button
                type="button"
                disabled={skipLoading}
                onClick={handleSkip}
                className="px-4 py-2 rounded-xl bg-rose-500 hover:bg-rose-600 disabled:opacity-50 text-white text-xs font-bold shadow-lg shadow-rose-500/20 transition"
              >
                {skipLoading ? "Processing..." : "Skip & Get Make-up Credit"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
