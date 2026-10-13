/**
 * SwimTrackPro - Pricing Engine & Single Source of Truth
 * -----------------------------------------------------
 * Handles dynamic, decoupled pricing calculations for all packages
 * and group sizes (1 to 5 swimmers).
 *
 * Mathematical Mechanics:
 * Total Batch Price = Math.round(BasePrice * Multiplier)
 * Price Per Swimmer = Math.round(TotalBatchPrice / SwimmerCount)
 */

(function (global) {
  'use strict';

  // Default Independent Base Rates (1-on-1, in INR)
  const DEFAULT_BASE_PRICES = Object.freeze({
    demo: 500,
    single: 750,
    monthly_2d: 5000,
    monthly_3d: 7500,
    '3_months': 18000,
  });

  // Group Multipliers (2 to 5 Swimmers)
  const GROUP_MULTIPLIERS = Object.freeze({
    1: 1.00,
    2: 1.70,
    3: 2.30,
    4: 2.80,
    5: 3.20,
  });

  // Exact Discount & Coach Yield Metrics from Specification
  const DISCOUNT_PERCENTAGES = Object.freeze({
    1: 0.0,
    2: 15.0,
    3: 23.3,
    4: 30.0,
    5: 36.0,
  });

  const COACH_BONUS_PERCENTAGES = Object.freeze({
    1: 0.0,
    2: 70.0,
    3: 130.0,
    4: 180.0,
    5: 220.0,
  });

  const PACKAGE_METADATA = Object.freeze({
    demo: {
      key: 'demo',
      name: 'Demo Session',
      tierLabel: 'Trial',
      sessions: 1,
      description: 'Single assessment trial at your doorstep pool',
      defaultWeeklyDays: null,
    },
    single: {
      key: 'single',
      name: 'Single Day Booking',
      tierLabel: 'Pay-as-you-go',
      sessions: 1,
      description: 'Standalone 1-hour coaching slot with instant confirmation',
      defaultWeeklyDays: null,
    },
    monthly_2d: {
      key: 'monthly_2d',
      name: 'Monthly (2 days/week)',
      tierLabel: 'Structured',
      sessions: 8,
      description: '8 sessions (4 calendar weeks) • Fixed weekly schedule',
      defaultWeeklyDays: 2,
    },
    monthly_3d: {
      key: 'monthly_3d',
      name: 'Monthly (3 days/week)',
      tierLabel: 'Recommended',
      sessions: 12,
      description: '12 sessions (4 calendar weeks) • Technique & stamina building',
      defaultWeeklyDays: 3,
    },
    '3_months': {
      key: '3_months',
      name: '3 Calendar Months',
      tierLabel: 'Best Value',
      sessions: 36,
      description: '36 sessions (3 days/wk × 12 weeks) • Loyalty rate with makeup credits',
      defaultWeeklyDays: 3,
    },
    custom: {
      key: 'custom',
      name: 'Custom Schedule',
      tierLabel: 'Flexible',
      sessions: 'Dynamic',
      description: 'Dynamic custom duration up to 60 days with hourly rate',
      defaultWeeklyDays: null,
    },
  });

  const PRICING_CONFIG = {
    BASE_PRICES: { ...DEFAULT_BASE_PRICES },
    GROUP_MULTIPLIERS,
    DISCOUNT_PERCENTAGES,
    COACH_BONUS_PERCENTAGES,
    PACKAGE_METADATA,
  };

  /**
   * Helper: Resolves the effective base prices taking into account
   * runtime overrides from window.SWIMTRACK_PRICING_CONFIG or settings.
   */
  function getEffectiveBasePrices(customOverrides) {
    const runtimeConfig = (typeof window !== 'undefined' && window.SWIMTRACK_PRICING_CONFIG) || {};
    const runtimeBase = runtimeConfig.base_prices || {};
    return {
      ...DEFAULT_BASE_PRICES,
      ...runtimeBase,
      ...(customOverrides || {}),
    };
  }

  /**
   * Helper: Normalizes package key from various forms (e.g., 'Demo', 'Monthly', 'monthly_2d')
   */
  function normalizePackageKey(rawKey, options = {}) {
    if (!rawKey) return 'monthly_3d';
    const clean = String(rawKey).trim().toLowerCase();

    if (clean === 'demo') return 'demo';
    if (clean === 'single') return 'single';
    if (clean === '3_months' || clean === '3months' || clean === '3-months') return '3_months';
    if (clean === 'custom' || clean === 'customize') return 'custom';

    if (clean === 'monthly' || clean.startsWith('monthly')) {
      const days = options.weeklyDays || (clean.includes('2') ? 2 : 3);
      return days === 2 ? 'monthly_2d' : 'monthly_3d';
    }

    if (clean === 'monthly_2d' || clean === 'monthly_2days' || clean === 'monthly2d') return 'monthly_2d';
    if (clean === 'monthly_3d' || clean === 'monthly_3days' || clean === 'monthly3d') return 'monthly_3d';

    return clean in PACKAGE_METADATA ? clean : 'monthly_3d';
  }

  /**
   * Core Calculation Function
   *
   * @param {string} packageKey - 'demo', 'single', 'monthly_2d', 'monthly_3d', '3_months', 'custom'
   * @param {number} swimmerCount - Swimmer count from 1 to 5 (clamped)
   * @param {Object} options - Optional overrides: { weeklyDays, customBasePrice, basePricesOverride }
   * @returns {Object} Quote details including totalBatchPrice and pricePerPerson
   */
  function getPackageQuote(packageKey, swimmerCount = 1, options = {}) {
    // Edge case handling: sanitize and clamp swimmer count between 1 and 5
    const parsedCount = parseInt(swimmerCount, 10);
    const count = Number.isNaN(parsedCount) ? 1 : Math.min(5, Math.max(1, parsedCount));

    const normalizedKey = normalizePackageKey(packageKey, options);
    const meta = PACKAGE_METADATA[normalizedKey] || {
      key: normalizedKey,
      name: packageKey || 'Custom Package',
      tierLabel: 'Custom',
      sessions: 1,
      description: '',
      defaultWeeklyDays: null,
    };

    const effectiveBasePrices = getEffectiveBasePrices(options.basePricesOverride);

    // Determine 1-on-1 base price
    let basePrice = 0;
    if (typeof options.customBasePrice === 'number' && options.customBasePrice >= 0) {
      basePrice = Math.round(options.customBasePrice);
    } else if (normalizedKey in effectiveBasePrices) {
      basePrice = effectiveBasePrices[normalizedKey];
    } else if (normalizedKey === 'custom') {
      // Custom hourly rate defaults to Single session rate (750)
      const sessionCount = parseInt(options.sessionCount, 10) || 1;
      basePrice = sessionCount * (effectiveBasePrices.single || 750);
    } else {
      basePrice = effectiveBasePrices.monthly_3d || 7500;
    }

    const multiplier = GROUP_MULTIPLIERS[count] || 1.00;

    // Core formulas from specification
    const totalBatchPrice = Math.round(basePrice * multiplier);
    const pricePerPerson = Math.round(totalBatchPrice / count);

    // Discounts & coach economics
    const savingsPerPersonPercent = DISCOUNT_PERCENTAGES[count] || 0.0;
    const coachBonusPercent = COACH_BONUS_PERCENTAGES[count] || 0.0;

    // Theoretical non-discounted total if each paid full 1-on-1 solo rate
    const standardSoloTotal = basePrice * count;
    const totalSavings = Math.max(0, standardSoloTotal - totalBatchPrice);

    // Cost per session per person (for unit economics breakdown)
    let sessionsCountNumber = typeof meta.sessions === 'number' ? meta.sessions : 1;
    if (options.sessionCount && !Number.isNaN(parseInt(options.sessionCount, 10))) {
      sessionsCountNumber = parseInt(options.sessionCount, 10);
    }
    const costPerPersonPerSession = sessionsCountNumber > 0
      ? Number((pricePerPerson / sessionsCountNumber).toFixed(2))
      : pricePerPerson;

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
    };
  }

  /**
   * Generates a matrix quote for all 5 swimmer counts for a given package
   */
  function getPackageMatrix(packageKey, options = {}) {
    const matrix = {};
    for (let c = 1; c <= 5; c++) {
      matrix[c] = getPackageQuote(packageKey, c, options);
    }
    return matrix;
  }

  /**
   * Generates full pricing matrix across all packages
   */
  function getFullPricingMatrix(options = {}) {
    const packages = ['demo', 'single', 'monthly_2d', 'monthly_3d', '3_months'];
    const result = {};
    packages.forEach((pkg) => {
      result[pkg] = getPackageMatrix(pkg, options);
    });
    return result;
  }

  // Engine Export Object
  const PricingEngine = {
    PRICING_CONFIG,
    DEFAULT_BASE_PRICES,
    GROUP_MULTIPLIERS,
    DISCOUNT_PERCENTAGES,
    COACH_BONUS_PERCENTAGES,
    PACKAGE_METADATA,
    getPackageQuote,
    getPackageMatrix,
    getFullPricingMatrix,
    normalizePackageKey,
    getEffectiveBasePrices,
  };

  // UMD / Global Export
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = PricingEngine;
  }
  if (typeof exports !== 'undefined') {
    exports.PricingEngine = PricingEngine;
    exports.getPackageQuote = getPackageQuote;
    exports.PRICING_CONFIG = PRICING_CONFIG;
  }
  if (typeof global !== 'undefined') {
    global.PricingEngine = PricingEngine;
    global.getPackageQuote = getPackageQuote;
    global.PRICING_CONFIG = PRICING_CONFIG;
  }
})(typeof window !== 'undefined' ? window : globalThis);
