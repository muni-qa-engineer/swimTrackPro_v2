"use client";

import React, { useState } from "react";
import { getPackageQuote } from "@/lib/pricingEngine";
import { Phone, Mail, Award, AlertTriangle, Minus, Plus, Sparkles } from "lucide-react";

interface Step2Props {
  swimmerName: string;
  setSwimmerName: (name: string) => void;
  skillLevel: string;
  setSkillLevel: (skill: string) => void;
  swimmerCount: number;
  setSwimmerCount: (count: number) => void;
  contactPhone: string;
  setContactPhone: (p: string) => void;
  contactEmail: string;
  setContactEmail: (e: string) => void;
  selectedPackage: string;
  selectedDays: string[];
  onBack: () => void;
  onNext: () => void;
}

const SKILL_LEVELS = ["Beginner", "Intermediate", "Regular", "Competitor"];

export function Step2SwimmerDetails({
  swimmerName,
  setSwimmerName,
  skillLevel,
  setSkillLevel,
  swimmerCount,
  setSwimmerCount,
  contactPhone,
  setContactPhone,
  contactEmail,
  setContactEmail,
  selectedPackage,
  selectedDays,
  onBack,
  onNext,
}: Step2Props) {
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const quote = getPackageQuote(selectedPackage, swimmerCount, {
    weeklyDays: selectedDays.length,
  });

  const handleValidateAndNext = () => {
    setErrorMsg(null);
    if (!swimmerName.trim()) {
      setErrorMsg("Please enter the swimmer full name.");
      return;
    }
    const cleanPhone = contactPhone.replace(/\D/g, "");
    if (cleanPhone.length !== 10) {
      setErrorMsg("Please enter a valid 10-digit mobile number.");
      return;
    }
    onNext();
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {errorMsg && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl flex items-center gap-3 text-sm">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Swimmer Information */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 sm:p-6 backdrop-blur space-y-4">
        <label className="text-sm font-bold text-cyan-400 uppercase tracking-wider block">
          Swimmer Profile <span className="text-rose-500">*</span>
        </label>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Swimmer Full Name <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={swimmerName}
              onChange={(e) => setSwimmerName(e.target.value)}
              placeholder="e.g. Rahul Sharma"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 transition"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Current Skill Level <span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <select
                value={skillLevel}
                onChange={(e) => setSkillLevel(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 transition appearance-none"
              >
                {SKILL_LEVELS.map((lvl) => (
                  <option key={lvl} value={lvl}>
                    {lvl}
                  </option>
                ))}
              </select>
              <Award className="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Contact Phone (Password) <span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <input
                type="tel"
                maxLength={10}
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                placeholder="10-digit mobile number"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 transition"
                required
              />
              <Phone className="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
            <span className="text-[11px] text-slate-500 mt-1 block">
              Your account & OTP access is linked to this phone number.
            </span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Email Address <span className="text-slate-500 text-[11px]">(Optional)</span>
            </label>
            <div className="relative">
              <input
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                placeholder="parent@example.com - for booking receipts"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 transition"
              />
              <Mail className="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>
        </div>
      </div>

      {/* Swimmers & Group Scaling Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 sm:p-6 backdrop-blur">
        <div className="flex items-center justify-between mb-4">
          <div>
            <label className="text-sm font-bold text-cyan-400 uppercase tracking-wider block">
              Swimmers in Batch
            </label>
            <p className="text-xs text-slate-400">
              Group scaling discounts applied up to 36% OFF
            </p>
          </div>

          {/* Stepper buttons 1-5 */}
          <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 p-1.5 rounded-xl">
            <button
              type="button"
              disabled={swimmerCount <= 1}
              onClick={() => setSwimmerCount(Math.max(1, swimmerCount - 1))}
              className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:pointer-events-none transition"
            >
              <Minus className="w-4 h-4" />
            </button>
            <span className="w-8 text-center font-bold text-white text-base">
              {swimmerCount}
            </span>
            <button
              type="button"
              disabled={swimmerCount >= 5}
              onClick={() => setSwimmerCount(Math.min(5, swimmerCount + 1))}
              className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:pointer-events-none transition"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Dynamic Pricing Quote Preview Card */}
        <div className="p-4 rounded-xl bg-gradient-to-br from-slate-950 to-slate-900 border border-cyan-500/20">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs text-slate-400 block">Total Batch Fee</span>
              <div className="text-2xl font-black text-white">
                ₹{quote.totalBatchPrice.toLocaleString("en-IN")}
              </div>
            </div>

            {quote.isGroup && (
              <div className="text-right">
                <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/20">
                  <Sparkles className="w-3.5 h-3.5" />
                  {quote.savingsPerPersonPercent}% OFF Per Person
                </span>
                <span className="text-xs text-slate-400 block mt-1">
                  ₹{quote.pricePerPerson.toLocaleString("en-IN")} / swimmer
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          onClick={onBack}
          className="px-6 py-3.5 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 font-bold text-sm transition"
        >
          ← Back to Session
        </button>

        <button
          type="button"
          onClick={handleValidateAndNext}
          className="px-8 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-cyan-400 hover:from-cyan-400 hover:to-cyan-300 text-slate-950 font-bold transition shadow-lg shadow-cyan-500/25 flex items-center gap-2"
        >
          <span>Review & Confirm</span>
          <span className="text-lg">→</span>
        </button>
      </div>
    </div>
  );
}
