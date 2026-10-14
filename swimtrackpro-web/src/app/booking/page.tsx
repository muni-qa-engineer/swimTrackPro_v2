import React from "react";
import { getActiveCoaches } from "@/app/actions/booking";
import { BookingWizard } from "@/components/booking/BookingWizard";
import { Waves } from "lucide-react";

export const metadata = {
  title: "Book Swimming Sessions | SwimTrackPro",
  description: "Book customized doorstep swimming sessions with top-tier verified coaches.",
};

export const dynamic = "force-dynamic";

export default async function BookingPage() {
  const coaches = await getActiveCoaches();

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header Section */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-bold mb-3">
            <Waves className="w-4 h-4" />
            <span>Doorstep Academy Coaching</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
            Book Swimming Session
          </h1>
          <p className="text-sm text-slate-400 mt-2 max-w-lg mx-auto">
            Choose your personal coach, training days, and doorstep pool with instant price calculations.
          </p>
        </div>

        {/* Wizard Form Component */}
        <BookingWizard coaches={coaches} />
      </div>
    </main>
  );
}
