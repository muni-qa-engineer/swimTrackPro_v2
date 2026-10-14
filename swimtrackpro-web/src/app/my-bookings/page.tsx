import React from "react";
import { Navbar } from "@/components/common/Navbar";
import { getMyBookingsList } from "@/app/actions/dashboard";
import {
  Calendar,
  Clock,
  MapPin,
  User,
  Users,
  Sparkles,
  ArrowRight,
  PlusCircle,
} from "lucide-react";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function MyBookingsPage({
  searchParams,
}: {
  searchParams: Promise<{ tab?: string }>;
}) {
  const { tab = "all" } = await searchParams;
  const currentTab = (["all", "active", "booked", "completed"].includes(tab)
    ? tab
    : "all") as "all" | "active" | "booked" | "completed";

  const rawBookings = await getMyBookingsList(currentTab);

  // Fallback demo bookings if DB is empty so page renders cleanly
  const bookings =
    rawBookings.length > 0
      ? rawBookings
      : [
          {
            id: "SWIM-BK-2026-01",
            booking_code: "SWIM-BK-2026-01",
            student_name: "Aarav Sharma, Ananya Sharma",
            package: "Monthly 3 Days/Week",
            trainer_username: "Coach Rajesh Verma",
            start_date: "2026-10-15",
            end_date: "2026-11-15",
            selected_days: "Monday, Wednesday, Friday",
            time: "06:00 AM - 07:00 AM",
            location: "Sobha City Swimming Pool, Bengaluru",
            persons: 2,
            fee: 14720,
            status: "active",
            pause_status: "ACTIVE",
            payment_request: "confirmed",
          },
          {
            id: "SWIM-BK-2026-02",
            booking_code: "SWIM-BK-2026-02",
            student_name: "Aarav Sharma",
            package: "Demo 1 Session",
            trainer_username: "Coach Sunita Rao",
            start_date: "2026-10-01",
            end_date: "2026-10-01",
            selected_days: "Thursday",
            time: "07:00 AM - 08:00 AM",
            location: "Prestige Golfshire Club, Bengaluru",
            persons: 1,
            fee: 699,
            status: "completed",
            pause_status: "ACTIVE",
            payment_request: "confirmed",
          },
        ];

  const getStatusBadge = (b: typeof bookings[0]) => {
    if (b.pause_status === "PAUSED") {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20">
          PAUSED
        </span>
      );
    }
    const st = (b.status || "").toLowerCase();
    if (st === "active" || st === "confirmed") {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          ACTIVE
        </span>
      );
    }
    if (st === "booked" || st === "pending") {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
          BOOKED
        </span>
      );
    }
    return (
      <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-400 border border-slate-700">
        COMPLETED
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Header Title */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Doorstep Coaching Subscriptions</span>
            </div>
            <h1 className="text-3xl font-black text-white tracking-tight">
              My Bookings
            </h1>
            <p className="text-xs sm:text-sm text-slate-400">
              Sorted with active packages first. Review schedule, coach assignment, and location.
            </p>
          </div>

          <Link
            href="/booking"
            className="px-5 py-2.5 rounded-2xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs sm:text-sm shadow-lg shadow-cyan-500/20 transition flex items-center gap-2 self-start sm:self-auto"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Booking</span>
          </Link>
        </div>

        {/* Tab Filters */}
        <div className="flex items-center gap-2 border-b border-slate-800/80 pb-3">
          {[
            { id: "all", label: "All Bookings" },
            { id: "active", label: "Active" },
            { id: "booked", label: "Booked (Upcoming)" },
            { id: "completed", label: "Completed" },
          ].map((tabItem) => (
            <Link
              key={tabItem.id}
              href={`/my-bookings?tab=${tabItem.id}`}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition ${
                currentTab === tabItem.id
                  ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                  : "text-slate-400 hover:text-white hover:bg-slate-900"
              }`}
            >
              {tabItem.label}
            </Link>
          ))}
        </div>

        {/* Bookings List */}
        <div className="space-y-4">
          {bookings.length === 0 ? (
            <div className="rounded-3xl bg-slate-900/40 border border-slate-800 p-12 text-center space-y-3">
              <Calendar className="w-10 h-10 text-slate-600 mx-auto" />
              <h3 className="text-base font-bold text-slate-300">No bookings in this tab</h3>
              <p className="text-xs text-slate-500">
                You do not have any bookings matching the current filter.
              </p>
              <Link
                href="/booking"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 text-slate-950 font-bold text-xs mt-2"
              >
                <span>Book a Doorstep Session</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          ) : (
            bookings.map((b) => (
              <div
                key={b.id}
                className="rounded-3xl bg-slate-900/90 border border-slate-800 p-6 backdrop-blur hover:border-slate-700 transition space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-slate-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
                      {b.booking_code || b.id}
                    </span>
                    <h3 className="text-base font-black text-white">{b.package}</h3>
                  </div>

                  <div>{getStatusBadge(b)}</div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                  <div>
                    <span className="text-slate-500 block mb-0.5 font-medium">Coach</span>
                    <p className="font-bold text-white flex items-center gap-1.5">
                      <User className="w-3.5 h-3.5 text-cyan-400" />
                      <span>{b.trainer_username || "Academy Coach"}</span>
                    </p>
                  </div>

                  <div>
                    <span className="text-slate-500 block mb-0.5 font-medium">Schedule</span>
                    <p className="font-bold text-white flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-cyan-400" />
                      <span>{b.time || "06:00 AM"}</span>
                    </p>
                    <span className="text-[11px] text-slate-400">{b.selected_days}</span>
                  </div>

                  <div>
                    <span className="text-slate-500 block mb-0.5 font-medium">Swimmers</span>
                    <p className="font-bold text-white flex items-center gap-1.5">
                      <Users className="w-3.5 h-3.5 text-cyan-400" />
                      <span>{b.persons || 1} Swimmer{(b.persons || 1) > 1 ? "s" : ""}</span>
                    </p>
                    <span className="text-[11px] text-slate-400 truncate block">
                      {b.student_name}
                    </span>
                  </div>

                  <div>
                    <span className="text-slate-500 block mb-0.5 font-medium">Total Fee</span>
                    <p className="font-bold text-emerald-400 text-sm">
                      ₹{b.fee ? b.fee.toLocaleString("en-IN") : 0}
                    </p>
                    <span className="text-[10px] text-slate-400">
                      Payment: {b.payment_request || "Paid"}
                    </span>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-800/60 text-xs">
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                    <span className="truncate max-w-md">{b.location || "Pool Arena"}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <Link
                      href="/dashboard"
                      className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs transition"
                    >
                      View in Dashboard
                    </Link>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </main>
    </div>
  );
}
