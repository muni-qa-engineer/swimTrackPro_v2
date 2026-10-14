"use client";

import React, { useState } from "react";
import { CoachInfo } from "@/app/actions/booking";
import { PACKAGE_METADATA } from "@/lib/pricingEngine";
import { LocationMapModal } from "./LocationMapModal";
import {
  Calendar,
  Clock,
  MapPin,
  Crosshair,
  Star,
  UserCheck,
  AlertTriangle,
  Loader2,
  Check,
} from "lucide-react";

interface Step1Props {
  coaches: CoachInfo[];
  selectedCoach: string;
  setSelectedCoach: (c: string) => void;
  selectedPackage: string;
  setSelectedPackage: (p: string) => void;
  selectedDays: string[];
  setSelectedDays: (days: string[]) => void;
  startDate: string;
  setStartDate: (d: string) => void;
  timeSlot: string;
  setTimeSlot: (t: string) => void;
  location: string;
  setLocation: (loc: string) => void;
  latitude: string;
  setLatitude: (lat: string) => void;
  longitude: string;
  setLongitude: (lng: string) => void;
  onNext: () => void;
}

const ALL_DAYS = [
  { short: "Mon", full: "Monday" },
  { short: "Tue", full: "Tuesday" },
  { short: "Wed", full: "Wednesday" },
  { short: "Thu", full: "Thursday" },
  { short: "Fri", full: "Friday" },
  { short: "Sat", full: "Saturday" },
  { short: "Sun", full: "Sunday" },
];

export function Step1SessionDetails({
  coaches,
  selectedCoach,
  setSelectedCoach,
  selectedPackage,
  setSelectedPackage,
  selectedDays,
  setSelectedDays,
  startDate,
  setStartDate,
  timeSlot,
  setTimeSlot,
  location,
  setLocation,
  setLatitude,
  setLongitude,
  onNext,
}: Step1Props) {
  const [mapModalOpen, setMapModalOpen] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [detectedToast, setDetectedToast] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const activeCoachObj = coaches.find((c) => c.username === selectedCoach);
  const packageMeta = PACKAGE_METADATA[selectedPackage] || PACKAGE_METADATA["monthly_3d"];

  const toggleDay = (dayFull: string) => {
    if (selectedDays.includes(dayFull)) {
      setSelectedDays(selectedDays.filter((d) => d !== dayFull));
    } else {
      setSelectedDays([...selectedDays, dayFull]);
    }
  };

  const handleDetectGPS = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }
    setDetecting(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude.toFixed(6);
        const lng = pos.coords.longitude.toFixed(6);
        setLatitude(lat);
        setLongitude(lng);

        try {
          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`
          );
          const data = await res.json();
          setLocation(data.display_name || `${lat}, ${lng}`);
        } catch {
          setLocation(`${lat}, ${lng}`);
        } finally {
          setDetecting(false);
          setDetectedToast(true);
          setTimeout(() => setDetectedToast(false), 2500);
        }
      },
      () => {
        alert("Could not access GPS location. Please enter your society/pool name manually.");
        setDetecting(false);
      }
    );
  };

  const handleValidateAndNext = () => {
    setErrorMsg(null);
    if (!selectedCoach) {
      setErrorMsg("Please select an assigned coach to continue.");
      return;
    }
    if (!startDate) {
      setErrorMsg("Please select a training start date.");
      return;
    }
    if (!timeSlot) {
      setErrorMsg("Please choose your preferred time slot.");
      return;
    }

    const pkg = selectedPackage.toLowerCase();
    if (pkg.includes("monthly")) {
      if (selectedDays.length < 2 || selectedDays.length > 3) {
        setErrorMsg("Monthly Package requires choosing 2 or 3 training days per week.");
        return;
      }
    } else if (["3_months", "6_months", "9_months", "12_months"].includes(pkg)) {
      if (selectedDays.length !== 3) {
        setErrorMsg("Long Term packages require choosing exactly 3 training days per week.");
        return;
      }
    }

    if (!location.trim()) {
      setErrorMsg("Please enter your society, apartment, or doorstep pool address.");
      return;
    }

    onNext();
  };

  const todayStr = new Date().toISOString().split("T")[0];

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {errorMsg && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl flex items-center gap-3 text-sm">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* 1. Coach Selection */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 sm:p-6 backdrop-blur">
        <label className="text-sm font-bold text-cyan-400 uppercase tracking-wider block mb-3">
          1. Select Coach <span className="text-rose-500">*</span>
        </label>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {coaches.map((c) => {
            const isSelected = selectedCoach === c.username;
            return (
              <div
                key={c.username}
                onClick={() => setSelectedCoach(c.username)}
                className={`p-4 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${
                  isSelected
                    ? "bg-cyan-500/10 border-cyan-400 ring-2 ring-cyan-500/30 shadow-lg shadow-cyan-500/10"
                    : "bg-slate-950/40 border-slate-800 hover:border-slate-700"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-bold text-white text-base">{c.name}</h4>
                    <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 font-bold border border-amber-500/20">
                      <Star className="w-3.5 h-3.5 fill-amber-400" />
                      {c.rating.toFixed(1)}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">{c.experience} • {c.qualification}</p>
                </div>

                <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                  <span className="text-slate-500">{c.residenceLocation}</span>
                  {isSelected && (
                    <span className="text-cyan-400 font-bold flex items-center gap-1">
                      <UserCheck className="w-3.5 h-3.5" /> Selected
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. Package Tier Selection */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 sm:p-6 backdrop-blur">
        <label className="text-sm font-bold text-cyan-400 uppercase tracking-wider block mb-3">
          2. Membership & Package Tier <span className="text-rose-500">*</span>
        </label>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {Object.entries(PACKAGE_METADATA).map(([key, meta]) => {
            const isSelected = selectedPackage === key;
            return (
              <div
                key={key}
                onClick={() => setSelectedPackage(key)}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${
                  isSelected
                    ? "bg-cyan-500/10 border-cyan-400 ring-2 ring-cyan-500/30"
                    : "bg-slate-950/40 border-slate-800 hover:border-slate-700"
                }`}
              >
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 block mb-1">
                    {meta.tierLabel}
                  </span>
                  <h4 className="font-bold text-white text-sm leading-tight">{meta.name}</h4>
                  <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{meta.description}</p>
                </div>
                {meta.pauseDays > 0 && (
                  <div className="mt-2 text-[10px] text-emerald-400 font-semibold">
                    +{meta.pauseDays} Pause Days
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Date, Days & Time Slots */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 sm:p-6 backdrop-blur space-y-5">
        <label className="text-sm font-bold text-cyan-400 uppercase tracking-wider block">
          3. Training Schedule & Timing <span className="text-rose-500">*</span>
        </label>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Start Date <span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <input
                type="date"
                min={todayStr}
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 transition"
              />
              <Calendar className="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Session Time Slot <span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <select
                value={timeSlot}
                onChange={(e) => setTimeSlot(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 transition appearance-none"
              >
                <option value="">-- Choose Time Slot --</option>
                {activeCoachObj?.availableSlots && activeCoachObj.availableSlots.length > 0 ? (
                  activeCoachObj.availableSlots.map((slot) => (
                    <option key={slot} value={slot}>
                      {slot}
                    </option>
                  ))
                ) : (
                  <>
                    <option value="06:00 AM - 07:00 AM">06:00 AM - 07:00 AM (Morning)</option>
                    <option value="07:00 AM - 08:00 AM">07:00 AM - 08:00 AM (Morning)</option>
                    <option value="08:00 AM - 09:00 AM">08:00 AM - 09:00 AM (Morning)</option>
                    <option value="04:00 PM - 05:00 PM">04:00 PM - 05:00 PM (Evening)</option>
                    <option value="05:00 PM - 06:00 PM">05:00 PM - 06:00 PM (Evening)</option>
                    <option value="06:00 PM - 07:00 PM">06:00 PM - 07:00 PM (Evening)</option>
                  </>
                )}
              </select>
              <Clock className="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>
        </div>

        {/* Weekly Days Picker */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-semibold text-slate-300">
              Weekly Training Days <span className="text-rose-500">*</span>
            </label>
            <span className="text-[11px] text-cyan-400 font-medium">
              {packageMeta.key.includes("monthly")
                ? "Select 2 or 3 days"
                : ["3_months", "6_months", "9_months", "12_months"].includes(packageMeta.key)
                ? "Select exactly 3 days"
                : "Choose class days"}
            </span>
          </div>

          <div className="grid grid-cols-7 gap-2">
            {ALL_DAYS.map((d) => {
              const isChecked = selectedDays.includes(d.full);
              return (
                <button
                  type="button"
                  key={d.full}
                  onClick={() => toggleDay(d.full)}
                  className={`py-2 rounded-xl text-xs font-bold transition border ${
                    isChecked
                      ? "bg-cyan-500 text-slate-950 border-cyan-400 shadow-md shadow-cyan-500/20"
                      : "bg-slate-950 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700"
                  }`}
                >
                  {d.short}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 4. Single Unified Pool Location */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 sm:p-6 backdrop-blur">
        <label className="text-sm font-bold text-cyan-400 uppercase tracking-wider block mb-2">
          4. Pool Location <span className="text-rose-500">*</span>
        </label>
        <p className="text-xs text-slate-400 mb-3">
          Doorstep society, apartment, or community swimming pool
        </p>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setMapModalOpen(true)}
            className="px-3.5 py-2.5 rounded-xl border border-slate-700 text-cyan-400 hover:bg-slate-800 transition flex items-center justify-center"
            title="Pick on interactive map"
          >
            <MapPin className="w-5 h-5" />
          </button>

          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g. My Home, Gachibowli"
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 transition placeholder:text-slate-600"
            required
          />

          <button
            type="button"
            onClick={handleDetectGPS}
            disabled={detecting}
            className="px-4 py-2.5 rounded-xl border border-slate-700 hover:border-cyan-500/50 bg-slate-800/50 hover:bg-slate-800 text-cyan-400 text-xs font-bold transition flex items-center gap-1.5 whitespace-nowrap disabled:opacity-50"
          >
            {detecting ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Locating...</span>
              </>
            ) : detectedToast ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400">Detected</span>
              </>
            ) : (
              <>
                <Crosshair className="w-3.5 h-3.5" />
                <span>Detect</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Next Step Action Button */}
      <div className="flex justify-end pt-2">
        <button
          type="button"
          onClick={handleValidateAndNext}
          className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-cyan-400 hover:from-cyan-400 hover:to-cyan-300 text-slate-950 font-bold transition shadow-lg shadow-cyan-500/25 flex items-center justify-center gap-2"
        >
          <span>Continue to Swimmer Details</span>
          <span className="text-lg">→</span>
        </button>
      </div>

      <LocationMapModal
        isOpen={mapModalOpen}
        onClose={() => setMapModalOpen(false)}
        initialLocation={location}
        onSelectLocation={(addr, lat, lng) => {
          setLocation(addr);
          if (lat) setLatitude(lat);
          if (lng) setLongitude(lng);
        }}
      />
    </div>
  );
}
