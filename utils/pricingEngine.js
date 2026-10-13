/**
 * SwimTrackPro - Pricing Engine Module (`utils/pricingEngine.js`)
 * Single source of truth for dynamic pricing calculations.
 */

export const PRICING_CONFIG = {
  BASE_PRICES: {
    demo: 500,
    single: 750,
    monthly_2d: 5000,
    monthly_3d: 7500,
    '3_months': 18000,
  },
  GROUP_MULTIPLIERS: {
    1: 1.00,
    2: 1.70,
    3: 2.30,
    4: 2.80,
    5: 3.20,
  },
  DISCOUNT_PERCENTAGES: {
    1: 0.0,
    2: 15.0,
    3: 23.3,
    4: 30.0,
    5: 36.0,
  },
  COACH_BONUS_PERCENTAGES: {
    1: 0.0,
    2: 70.0,
    3: 130.0,
    4: 180.0,
    5: 220.0,
  },
};

export function getPackageQuote(packageKey, swimmerCount = 1, options = {}) {
  const parsedCount = parseInt(swimmerCount, 10);
  const count = Number.isNaN(parsedCount) ? 1 : Math.min(5, Math.max(1, parsedCount));

  let key = String(packageKey || 'monthly_3d').trim().toLowerCase();
  if (key === 'monthly') {
    key = options.weeklyDays === 2 ? 'monthly_2d' : 'monthly_3d';
  }

  const basePrice = (options.customBasePrice !== undefined)
    ? options.customBasePrice
    : (PRICING_CONFIG.BASE_PRICES[key] || 7500);

  const multiplier = PRICING_CONFIG.GROUP_MULTIPLIERS[count] || 1.00;
  const totalBatchPrice = Math.round(basePrice * multiplier);
  const pricePerPerson = Math.round(totalBatchPrice / count);

  return {
    packageKey: key,
    swimmerCount: count,
    basePrice,
    multiplier,
    totalBatchPrice,
    pricePerPerson,
    savingsPerPersonPercent: PRICING_CONFIG.DISCOUNT_PERCENTAGES[count] || 0.0,
    coachBonusPercent: PRICING_CONFIG.COACH_BONUS_PERCENTAGES[count] || 0.0,
    totalSavings: Math.max(0, (basePrice * count) - totalBatchPrice),
  };
}

export default {
  PRICING_CONFIG,
  getPackageQuote,
};
