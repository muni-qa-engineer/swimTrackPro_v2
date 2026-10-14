import React from "react";
import { Navbar } from "@/components/common/Navbar";
import { TrainerAttendanceTracker } from "@/components/trainer/TrainerAttendanceTracker";
import { getTrainerDashboardData } from "@/app/actions/dashboard";
import {
  Star,
  Users,
  ShieldCheck,
} from "lucide-react";

export const dynamic = "force-dynamic";

export default async function TrainerPortalPage() {
  const data = await getTrainerDashboardData();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Trainer Banner */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/40 border border-slate-800 p-6 sm:p-8">
          <div className="absolute top-0 right-0 w-80 h-80 bg-cyan-500/10 blur-3xl pointer-events-none rounded-full" />

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-slate-950 font-black text-2xl shadow-xl shadow-cyan-500/20">
                {data.trainerName.split(" ")[1]?.charAt(0) || "T"}
              </div>
              <div>
                <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 mb-1">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Certified Coach Portal</span>
                </div>
                <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
                  {data.trainerName}
                </h1>
                <p className="text-xs text-slate-400">
                  Doorstep Coaching Specialist • Bangalore Region
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 font-bold text-xs">
                <Star className="w-4 h-4 fill-amber-400" />
                <span>5.0 Rating (48 reviews)</span>
              </div>
            </div>
          </div>

          {/* KPI row */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4 mt-8 pt-6 border-t border-slate-800/80">
            <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800/80">
              <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                Assigned Students
              </span>
              <p className="text-lg font-black text-white">{data.totalStudents}</p>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800/80">
              <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                Active Training Batches
              </span>
              <p className="text-lg font-black text-cyan-400">
                {data.totalActiveBatches} Batches
              </p>
            </div>

            <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800/80 col-span-2 sm:col-span-1">
              <span className="text-[11px] font-semibold text-slate-400 block mb-1">
                Today&apos;s Date
              </span>
              <p className="text-sm font-bold text-slate-200">{data.todayDateStr}</p>
            </div>
          </div>
        </div>

        {/* Live Attendance Tracker */}
        <TrainerAttendanceTracker
          todaySessions={data.todaySessions}
          todayDateStr={data.todayDateStr}
        />

        {/* Assigned Swimmer Roster */}
        <div className="rounded-3xl bg-slate-900/90 border border-slate-800 p-6 backdrop-blur space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                <Users className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Swimmer Roster</h3>
                <p className="text-xs text-slate-400">
                  Sorted latest active first • All assigned trainees
                </p>
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 uppercase font-bold text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4 rounded-l-xl">Swimmer</th>
                  <th className="py-3 px-4">Membership Plan</th>
                  <th className="py-3 px-4">Days</th>
                  <th className="py-3 px-4">Slot</th>
                  <th className="py-3 px-4">Contact</th>
                  <th className="py-3 px-4 rounded-r-xl">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {data.swimmerRoster.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition">
                    <td className="py-3.5 px-4 font-bold text-white">
                      {item.studentName}
                    </td>
                    <td className="py-3.5 px-4">{item.packageName}</td>
                    <td className="py-3.5 px-4 text-cyan-400">{item.selectedDays}</td>
                    <td className="py-3.5 px-4">{item.time}</td>
                    <td className="py-3.5 px-4 text-slate-400">{item.phone}</td>
                    <td className="py-3.5 px-4">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
