"use client";

import React from "react";
import { Check } from "lucide-react";

interface StepperProps {
  currentStep: number;
  totalSteps?: number;
}

export function BookingStepper({ currentStep, totalSteps = 3 }: StepperProps) {
  const steps = [
    { number: 1, title: "Session Details", desc: "Coach, package & pool" },
    { number: 2, title: "Swimmer Info", desc: "Batch size & swimmer" },
    { number: 3, title: "Payment & Summary", desc: "Review & confirm" },
  ];

  return (
    <div className="w-full max-w-3xl mx-auto mb-8 px-4">
      <div className="flex items-center justify-between relative">
        <div className="absolute left-0 top-1/2 -translate-y-1/2 h-0.5 bg-slate-800 w-full z-0" />
        <div
          className="absolute left-0 top-1/2 -translate-y-1/2 h-0.5 bg-gradient-to-r from-cyan-500 to-cyan-400 z-0 transition-all duration-500"
          style={{ width: `${((currentStep - 1) / (totalSteps - 1)) * 100}%` }}
        />

        {steps.map((s) => {
          const isDone = currentStep > s.number;
          const isCurrent = currentStep === s.number;

          return (
            <div key={s.number} className="relative z-10 flex flex-col items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-300 shadow-lg ${
                  isDone
                    ? "bg-emerald-500 text-white shadow-emerald-500/20"
                    : isCurrent
                    ? "bg-cyan-500 text-slate-950 ring-4 ring-cyan-500/20 shadow-cyan-500/30 scale-105"
                    : "bg-slate-900 border border-slate-700 text-slate-400"
                }`}
              >
                {isDone ? <Check className="w-5 h-5 stroke-[2.5]" /> : s.number}
              </div>
              <div className="text-center mt-2 hidden sm:block">
                <p
                  className={`text-xs font-semibold ${
                    isCurrent ? "text-cyan-400" : isDone ? "text-slate-200" : "text-slate-500"
                  }`}
                >
                  {s.title}
                </p>
                <p className="text-[10px] text-slate-500">{s.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
