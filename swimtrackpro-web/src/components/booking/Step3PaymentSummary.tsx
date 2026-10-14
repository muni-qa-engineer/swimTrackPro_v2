"use client";

import React, { useState } from "react";
import { CoachInfo, createBooking } from "@/app/actions/booking";
import { getPackageQuote } from "@/lib/pricingEngine";
import {
  CheckCircle2,
  Calendar,
  Clock,
  MapPin,
  User,
  ShieldCheck,
  Loader2,
  AlertCircle,
  Award,
} from "lucide-react";
import Link from "next/link";

interface Step3Props {
  coach: CoachInfo | undefined;
  packageKey: string;
  startDate: string;
  selectedDays: string[];
  timeSlot: string;
  location: string;
  latitude: string;
  longitude: string;
  swimmerName: string;
  skillLevel: string;
  swimmerCount: number;
  contactPhone: string;
  contactEmail: string;
  onBack: () => void;
}

export function Step3PaymentSummary({
  coach,
  packageKey,
  startDate,
  selectedDays,
  timeSlot,
  location,
  latitude,
  longitude,
  swimmerName,
  skillLevel,
  swimmerCount,
  contactPhone,
  contactEmail,
  onBack,
}: Step3Props) {
  const [submitting, setSubmitting] = useState(false);
  const [bookingResult, setBookingResult] = useState<{
    success: boolean;
    bookingId?: string;
    bookingCode?: string;
    totalFee?: number;
    error?: string;
  } | null>(null);

  const quote = getPackageQuote(packageKey, swimmerCount, {
    weeklyDays: selectedDays.length,
  });

  const handleConfirmBooking = async () => {
    if (!coach) return;
    setSubmitting(true);
    try {
      const res = await createBooking({
        trainerUsername: coach.username,
        packageKey,
        startDate,
        selectedDays,
        time: timeSlot,
        location,
        latitude,
        longitude,
        swimmerName,
        skillLevel,
        swimmerCount,
        contactPhone,
        contactEmail,
      });
      setBookingResult(res);
    } catch (e) {
      setBookingResult({
        success: false,
        error: e instanceof Error ? e.message : "Something went wrong. Please try again.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (bookingResult?.success) {
    return (
      <div className="bg-slate-900/80 border border-emerald-500/30 rounded-3xl p-6 sm:p-10 text-center max-w-xl mx-auto backdrop-blur shadow-2xl animate-in zoom-in-95 duration-300">
        <div className="w-16 h-16 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-5 border border-emerald-500/30">
          <CheckCircle2 className="w-10 h-10" />
        </div>

        <h3 className="text-2xl font-black text-white mb-2">Booking Confirmed!</h3>
        <p className="text-sm text-slate-300 mb-6">
          Your swim slot with <strong>{coach?.name}</strong> has been registered successfully.
        </p>

        <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-left space-y-2 mb-6">
          <div className="flex justify-between items-center text-xs text-slate-400">
            <span>Booking Code:</span>
            <span className="font-mono font-bold text-cyan-400 text-sm">
              {bookingResult.bookingCode}
            </span>
          </div>
          <div className="flex justify-between items-center text-xs text-slate-400">
            <span>Total Payable:</span>
            <span className="font-bold text-white text-base">
              ₹{bookingResult.totalFee?.toLocaleString("en-IN")}
            </span>
          </div>
          <div className="flex justify-between items-center text-xs text-slate-400">
            <span>Start Date:</span>
            <span className="text-slate-200">{startDate}</span>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/"
            className="px-6 py-3 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold rounded-xl text-sm transition"
          >
            Go to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {bookingResult?.error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400" />
          <span>{bookingResult.error}</span>
        </div>
      )}

      {/* Booking Summary Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 sm:p-6 backdrop-blur space-y-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-cyan-400 block">
              Booking Overview
            </span>
            <h3 className="text-lg font-bold text-white">{quote.packageName}</h3>
          </div>
          <span className="px-3 py-1 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-full text-xs font-bold">
            {swimmerCount} Swimmer{swimmerCount > 1 ? "s" : ""}
          </span>
        </div>

        {/* Breakdown Items */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="flex items-start gap-3 p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
            <User className="w-4 h-4 text-cyan-400 mt-0.5" />
            <div>
              <span className="text-slate-400 block">Coach Assigned</span>
              <span className="font-bold text-white">{coach?.name || "Unassigned"}</span>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
            <Award className="w-4 h-4 text-cyan-400 mt-0.5" />
            <div>
              <span className="text-slate-400 block">Swimmer</span>
              <span className="font-bold text-white">
                {swimmerName} ({skillLevel})
              </span>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
            <Calendar className="w-4 h-4 text-cyan-400 mt-0.5" />
            <div>
              <span className="text-slate-400 block">Schedule & Days</span>
              <span className="font-bold text-white">
                {startDate} • {selectedDays.join(", ")}
              </span>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
            <Clock className="w-4 h-4 text-cyan-400 mt-0.5" />
            <div>
              <span className="text-slate-400 block">Slot Time</span>
              <span className="font-bold text-white">{timeSlot}</span>
            </div>
          </div>

          <div className="sm:col-span-2 flex items-start gap-3 p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
            <MapPin className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
            <div>
              <span className="text-slate-400 block">Doorstep Pool Location</span>
              <span className="font-bold text-white line-clamp-2">{location}</span>
            </div>
          </div>
        </div>

        {/* Fee & Discount Summary */}
        <div className="pt-4 border-t border-slate-800">
          <div className="space-y-2 mb-4 text-xs">
            <div className="flex justify-between text-slate-400">
              <span>Base Solo Price:</span>
              <span>₹{quote.basePrice.toLocaleString("en-IN")} × {swimmerCount}</span>
            </div>
            {quote.isGroup && (
              <div className="flex justify-between text-emerald-400 font-semibold">
                <span>Group Scaling Discount ({quote.savingsPerPersonPercent}%):</span>
                <span>-₹{quote.totalSavings.toLocaleString("en-IN")}</span>
              </div>
            )}
            <div className="flex justify-between items-baseline pt-2 border-t border-slate-800">
              <span className="text-sm font-bold text-white">Total Payable Fee:</span>
              <span className="text-2xl font-black text-cyan-400">
                ₹{quote.totalBatchPrice.toLocaleString("en-IN")}
              </span>
            </div>
          </div>

          <div className="p-3 bg-cyan-500/10 border border-cyan-500/20 rounded-xl flex items-center gap-2.5 text-xs text-cyan-300">
            <ShieldCheck className="w-4 h-4 flex-shrink-0 text-cyan-400" />
            <span>Includes doorstep coaching assurance, certified trainer, and reschedule flexibility.</span>
          </div>
        </div>
      </div>

      {/* Buttons */}
      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          onClick={onBack}
          disabled={submitting}
          className="px-6 py-3.5 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 font-bold text-sm transition"
        >
          ← Back to Swimmer
        </button>

        <button
          type="button"
          onClick={handleConfirmBooking}
          disabled={submitting}
          className="px-8 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-cyan-400 hover:from-cyan-400 hover:to-cyan-300 text-slate-950 font-bold transition shadow-lg shadow-cyan-500/25 flex items-center gap-2 disabled:opacity-50"
        >
          {submitting ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Registering Booking...</span>
            </>
          ) : (
            <>
              <span>Confirm & Book Slot</span>
              <span className="text-lg">✓</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
