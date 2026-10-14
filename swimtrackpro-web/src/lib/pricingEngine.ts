/**
 * SwimTrackPro - TypeScript Dynamic Pricing Engine
 * ------------------------------------------------
 * Single Source of Truth for all package quotes, group scaling (1 to 5 swimmers),
 * savings percentages, and trainer payouts.
 */

export interface PackageMetadata {
  key: string;
  name: string;
  tierLabel: string;
  sessions: number | string;
  description: string;
  defaultWeeklyDays: number | null;
  allowedWeeklyDays?: number[];
  pauseDays: number;
  totalSkips: number;
}

export interface PricingQuote {
  packageKey: string;
  packageName: string;
  tierLabel: string;
  sessions: number | string;
  swimmerCount: number;
  basePrice: number;
  multiplier: number;
  totalBatchPrice: number;
  pricePerPerson: number;
  savingsPerPersonPercent: number;
  coachBonusPercent: number;
  totalSavings: number;
  costPerPersonPerSession: number;
  isGroup: boolean;
  pauseDays: number;
  totalSkips: number;
}

export const DEFAULT_BASE_PRICES: Record<string, number> = Object.freeze({
  demo: 500,
  single: 750,
  monthly_2d: 5000,
  monthly_3d: 7500,
  "3_months": 18000,
  "6_months": 36000,
  "9_months": 54000,
  "12_months": 72000,
});

export const GROUP_MULTIPLIERS: Record<number, number> = Object.freeze({
  1: 1.0,
  2: 1.7,
  3: 2.3,
  4: 2.8,
  5: 3.2,
});

export const DISCOUNT_PERCENTAGES: Record<number, number> = Object.freeze({
  1: 0.0,
  2: 15.0,
  3: 23.3,
  4: 30.0,
  5: 36.0,
});

export const COACH_BONUS_PERCENTAGES: Record<number, number> = Object.freeze({
  1: 0.0,
  2: 70.0,
  3: 130.0,
  4: 180.0,
  5: 220.0,
});

export const PACKAGE_METADATA: Record<string, PackageMetadata> = Object.freeze({
  demo: {
    key: "demo",
    name: "Demo Session",
    tierLabel: "Trial",
    sessions: 1,
    description: "Single assessment trial at your doorstep pool",
    defaultWeeklyDays: null,
    pauseDays: 0,
    totalSkips: 0,
  },
  single: {
    key: "single",
    name: "Single Day Booking",
    tierLabel: "Pay-as-you-go",
    sessions: 1,
    description: "Standalone 1-hour coaching slot with instant confirmation",
    defaultWeeklyDays: null,
    pauseDays: 0,
    totalSkips: 0,
  },
  monthly_2d: {
    key: "monthly_2d",
    name: "Monthly (2 days/week)",
    tierLabel: "Structured",
    sessions: 8,
    description: "8 sessions (4 calendar weeks) • Fixed weekly schedule",
    defaultWeeklyDays: 2,
    allowedWeeklyDays: [2],
    pauseDays: 0,
    totalSkips: 3,
  },
  monthly_3d: {
    key: "monthly_3d",
    name: "Monthly (3 days/week)",
    tierLabel: "Recommended",
    sessions: 12,
    description: "12 sessions (4 calendar weeks) • Technique & stamina building",
    defaultWeeklyDays: 3,
    allowedWeeklyDays: [3],
    pauseDays: 0,
    totalSkips: 3,
  },
  "3_months": {
    key: "3_months",
    name: "3 Calendar Months",
    tierLabel: "Best Value",
    sessions: 36,
    description: "36 sessions (3 days/wk × 12 wks) • 15 pause days & 9 skips",
    defaultWeeklyDays: 3,
    allowedWeeklyDays: [3],
    pauseDays: 15,
    totalSkips: 9,
  },
  "6_months": {
    key: "6_months",
    name: "6 Calendar Months",
    tierLabel: "Half Year",
    sessions: 72,
    description: "72 sessions (3 days/wk × 24 wks) • 30 pause days & 18 skips",
    defaultWeeklyDays: 3,
    allowedWeeklyDays: [3],
    pauseDays: 30,
    totalSkips: 18,
  },
  "9_months": {
    key: "9_months",
    name: "9 Calendar Months",
    tierLabel: "Extended Pass",
    sessions: 108,
    description: "108 sessions (3 days/wk × 36 wks) • 45 pause days & 27 skips",
    defaultWeeklyDays: 3,
    allowedWeeklyDays: [3],
    pauseDays: 45,
    totalSkips: 27,
  },
  "12_months": {
    key: "12_months",
    name: "1 Year Annual Pass",
    tierLabel: "Pro Athlete",
    sessions: 144,
    description: "144 sessions (3 days/wk × 48 wks) • 60 pause days & 36 skips",
    defaultWeeklyDays: 3,
    allowedWeeklyDays: [3],
    pauseDays: 60,
    totalSkips: 36,
  },
  custom: {
    key: "custom",
    name: "Custom Schedule",
    tierLabel: "Flexible",
    sessions: "Dynamic",
    description: "Custom date range with flexible frequency up to 60 days",
    defaultWeeklyDays: null,
    pauseDays: 15,
    totalSkips: 9,
  },
});

export function normalizePackageKey(
  rawKey: string | undefined | null,
  options: { weeklyDays?: number } = {}
): string {
  if (!rawKey) return "monthly_3d";
  const clean = String(rawKey).trim().toLowerCase();

  if (clean === "demo") return "demo";
  if (clean === "single") return "single";
  if (clean === "3_months" || clean === "3months" || clean === "3-months") return "3_months";
  if (clean === "6_months" || clean === "6months" || clean === "6-months") return "6_months";
  if (clean === "9_months" || clean === "9months" || clean === "9-months") return "9_months";
  if (clean === "12_months" || clean === "12months" || clean === "12-months" || clean === "1year" || clean === "1_year") return "12_months";
  if (clean === "custom" || clean === "customize") return "custom";

  if (clean === "monthly" || clean.startsWith("monthly")) {
    const days = options.weeklyDays || (clean.includes("2") ? 2 : 3);
    return days === 2 ? "monthly_2d" : "monthly_3d";
  }

  return clean in PACKAGE_METADATA ? clean : "monthly_3d";
}

export function getPackageQuote(
  packageKey: string,
  swimmerCount: number = 1,
  options: {
    weeklyDays?: number;
    customBasePrice?: number;
    basePricesOverride?: Record<string, number>;
    sessionCount?: number;
  } = {}
): PricingQuote {
  const count = Math.min(5, Math.max(1, Math.round(Number(swimmerCount) || 1)));
  const normalizedKey = normalizePackageKey(packageKey, options);
  const meta = PACKAGE_METADATA[normalizedKey] || {
    key: normalizedKey,
    name: packageKey,
    tierLabel: "Custom",
    sessions: 1,
    description: "",
    defaultWeeklyDays: null,
    pauseDays: 0,
    totalSkips: 0,
  };

  const effectivePrices = {
    ...DEFAULT_BASE_PRICES,
    ...(options.basePricesOverride || {}),
  };

  let basePrice = 0;
  if (typeof options.customBasePrice === "number" && options.customBasePrice >= 0) {
    basePrice = Math.round(options.customBasePrice);
  } else if (normalizedKey in effectivePrices) {
    basePrice = effectivePrices[normalizedKey];
  } else if (normalizedKey === "custom") {
    const sessions = Number(options.sessionCount) || 1;
    basePrice = sessions * (effectivePrices.single || 750);
  } else {
    basePrice = effectivePrices.monthly_3d || 7500;
  }

  const multiplier = GROUP_MULTIPLIERS[count] || 1.0;
  const totalBatchPrice = Math.round(basePrice * multiplier);
  const pricePerPerson = Math.round(totalBatchPrice / count);

  const savingsPerPersonPercent = DISCOUNT_PERCENTAGES[count] || 0.0;
  const coachBonusPercent = COACH_BONUS_PERCENTAGES[count] || 0.0;
  const standardSoloTotal = basePrice * count;
  const totalSavings = Math.max(0, standardSoloTotal - totalBatchPrice);

  let sessionCountNum = typeof meta.sessions === "number" ? meta.sessions : 1;
  if (options.sessionCount && !Number.isNaN(options.sessionCount)) {
    sessionCountNum = options.sessionCount;
  }
  const costPerPersonPerSession =
    sessionCountNum > 0 ? Number((pricePerPerson / sessionCountNum).toFixed(2)) : pricePerPerson;

  return {
    packageKey: normalizedKey,
    packageName: meta.name,
    tierLabel: meta.tierLabel,
    sessions: meta.sessions,
    swimmerCount: count,
    basePrice,
    multiplier,
    totalBatchPrice,
    pricePerPerson,
    savingsPerPersonPercent,
    coachBonusPercent,
    totalSavings,
    costPerPersonPerSession,
    isGroup: count > 1,
    pauseDays: meta.pauseDays,
    totalSkips: meta.totalSkips,
  };
}
