import React from "react";
import { Navbar } from "@/components/common/Navbar";
import { AttendanceCalendar } from "@/components/dashboard/AttendanceCalendar";
import { MembershipFlexibilityCard } from "@/components/dashboard/MembershipFlexibilityCard";
import { SwimmersCard } from "@/components/dashboard/SwimmersCard";
import { NoticesCard } from "@/components/dashboard/NoticesCard";
import {
  getGuestDashboardData,
  skipSessionAction,
} from "@/app/actions/dashboard";
import {
  Sparkles,
  Clock,
  Ticket,
  ChevronRight,
  MapPin,
} from "lucide-react";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const data = await getGuestDashboardData();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Welcome Hero Banner */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 border border-slate-800 p-6 sm:p-8">
          <div className="absolute top-0 right-0 w-80 h-80 bg-cyan-500/10 blur-3xl pointer-events-none rounded-full" />

          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Doorstep Swimming Portal</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
                Welcome back, {data.ownerName}! 👋
              </h1>
              <p className="text-xs sm:text-sm text-slate-400">
                Track your active training batches, request pause periods, and reschedule make-up classes.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href="/booking"
                className="px-5 py-2.5 rounded-2xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs sm:text-sm shadow-lg shadow-cyan-500/20 transition flex items-center gap-2"
              >
                <span>Book Another Batch</span>
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* Quick Metrics Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mt-8 pt-6 border-t border-slate-800/80">
            <div className="p-3 sm:p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80">
              <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                Active Plan
              </span>
              <p className="text-sm sm:text-base font-bold text-white truncate">
                {data.activePackage?.packageName || "No Active Plan"}
              </p>
            </div>

            <div className="p-3 sm:p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80">
              <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                Classes Left
              </span>
              <p className="text-sm sm:text-base font-bold text-cyan-400">
                {data.activePackage?.remainingClasses ?? 0} classes
              </p>
            </div>

            <div className="p-3 sm:p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80">
              <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                Make-up Credits
              </span>
              <div className="flex items-center gap-1.5">
                <Ticket className="w-4 h-4 text-emerald-400" />
                <p className="text-sm sm:text-base font-bold text-emerald-400">
                  {data.makeupCreditsCount} Credits
                </p>
              </div>
            </div>

            <div className="p-3 sm:p-4 rounded-2xl bg-slate-950/60 border border-slate-800/80">
              <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                Swimmers
              </span>
              <p className="text-sm sm:text-base font-bold text-white">
                {data.totalSwimmers} Enrolled
              </p>
            </div>
          </div>
        </div>

        {/* Dashboard Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column (5 Cols) */}
          <div className="lg:col-span-5 space-y-6">
            {data.activePackage && (
              <MembershipFlexibilityCard packageData={data.activePackage} />
            )}
            <SwimmersCard swimmers={data.swimmers} />
            <NoticesCard notices={data.notices} />
          </div>

          {/* Right Column (7 Cols) */}
          <div className="lg:col-span-7 space-y-6">
            <AttendanceCalendar
              monthName={data.calendarMonthName}
              calendarDays={data.calendarDays}
              bookingId={data.activePackage?.bookingId}
              onSkipSession={skipSessionAction}
            />

            {/* Upcoming Next Sessions Card */}
            <div className="rounded-3xl bg-slate-900/90 border border-slate-800 p-6 backdrop-blur">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                    <Clock className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Upcoming Classes</h3>
                    <p className="text-xs text-slate-400">Next scheduled doorstep sessions</p>
                  </div>
                </div>
              </div>

              {data.upcomingSessions.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-500">
                  No upcoming classes scheduled.
                </div>
              ) : (
                <div className="space-y-3">
                  {data.upcomingSessions.map((s, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-white">{s.studentName}</span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                            {s.time}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 flex items-center gap-1.5">
                          <MapPin className="w-3.5 h-3.5 text-slate-500" />
                          <span>{s.location}</span>
                        </p>
                      </div>

                      <div className="text-right sm:text-right">
                        <span className="text-xs font-bold text-cyan-300 block">{s.date}</span>
                        <span className="text-[11px] text-slate-400">{s.trainerName}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
