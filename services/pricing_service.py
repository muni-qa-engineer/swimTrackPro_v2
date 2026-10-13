"""
Pricing Service
SwimTrackPro - Dynamic & Decoupled Pricing Architecture

Single Source of Truth on Backend:
- Independent Base Rates (1-on-1):
  * Demo: ₹500 (1 session)
  * Single Day: ₹750 (1 session)
  * Monthly 2d/wk: ₹5,000 (8 sessions)
  * Monthly 3d/wk: ₹7,500 (12 sessions)
  * 3 Months: ₹18,000 (36 sessions)
- Dynamic Group Multipliers (2 to 5 Swimmers):
  * 1 Swimmer: 1.00x (Baseline)
  * 2 Swimmers: 1.70x (15.0% discount/swimmer, +70% coach yield)
  * 3 Swimmers: 2.30x (23.3% discount/swimmer, +130% coach yield)
  * 4 Swimmers: 2.80x (30.0% discount/swimmer, +180% coach yield)
  * 5 Swimmers: 3.20x (36.0% discount/swimmer, +220% coach yield)

Formulas:
- Total Batch Price = round(BasePrice * Multiplier)
- Price Per Swimmer = round(TotalBatchPrice / SwimmerCount)
"""

import json
import os

DEFAULT_BASE_PRICES = {
    'demo': 500,
    'single': 750,
    'monthly_2d': 5000,
    'monthly_3d': 7500,
    '3_months': 18000,
}

GROUP_MULTIPLIERS = {
    1: 1.00,
    2: 1.70,
    3: 2.30,
    4: 2.80,
    5: 3.20,
}

DISCOUNT_PERCENTAGES = {
    1: 0.0,
    2: 15.0,
    3: 23.3,
    4: 30.0,
    5: 36.0,
}

COACH_BONUS_PERCENTAGES = {
    1: 0.0,
    2: 70.0,
    3: 130.0,
    4: 180.0,
    5: 220.0,
}

PACKAGE_SESSIONS = {
    'demo': 1,
    'single': 1,
    'monthly_2d': 8,
    'monthly_3d': 12,
    '3_months': 36,
    'custom': None,
}

PACKAGE_NAMES = {
    'demo': 'Demo Session',
    'single': 'Single Day',
    'monthly_2d': 'Monthly (2 days/week)',
    'monthly_3d': 'Monthly (3 days/week)',
    '3_months': '3 Calendar Months',
    'custom': 'Custom Schedule',
}

PACKAGE_METADATA = {
    'demo': {'name': 'Demo Session', 'sessions': 1, 'badge': 'Trial'},
    'single': {'name': 'Single Day', 'sessions': 1, 'badge': 'Flexible'},
    'monthly_2d': {'name': 'Monthly (2 days/week)', 'sessions': 8, 'badge': 'Popular'},
    'monthly_3d': {'name': 'Monthly (3 days/week)', 'sessions': 12, 'badge': 'Recommended'},
    '3_months': {'name': '3 Calendar Months', 'sessions': 36, 'badge': 'Best Value'},
}


def _get_settings_path():
    return os.path.join(os.path.dirname(__file__), 'settings.json')


def get_base_prices():
    """
    Returns configured base prices, merging defaults with any
    persisted admin overrides in settings.json.
    """
    settings_file = _get_settings_path()
    prices = dict(DEFAULT_BASE_PRICES)
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                pricing_data = data.get('pricing', {})
                overrides = pricing_data.get('base_prices', {})
                for k, v in overrides.items():
                    if k in prices and isinstance(v, (int, float)) and v >= 0:
                        prices[k] = int(v)
        except Exception:
            pass
    return prices


def update_base_prices(new_prices):
    """
    Admin helper to update base prices in settings.json.
    """
    if not isinstance(new_prices, dict):
        return False
    settings_file = _get_settings_path()
    data = {}
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {}

    if 'pricing' not in data:
        data['pricing'] = {}
    if 'base_prices' not in data['pricing']:
        data['pricing']['base_prices'] = dict(DEFAULT_BASE_PRICES)

    for k, v in new_prices.items():
        if k in DEFAULT_BASE_PRICES and isinstance(v, (int, float)) and v >= 0:
            data['pricing']['base_prices'][k] = int(v)

    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return True


def normalize_package_key(raw_package, weekly_days=None, session_count=None):
    """
    Normalizes a package string into the canonical keys:
    'demo', 'single', 'monthly_2d', 'monthly_3d', '3_months', 'custom'
    """
    if not raw_package:
        return 'monthly_3d'

    clean = str(raw_package).strip().lower()

    if clean in ['demo']:
        return 'demo'
    if clean in ['single']:
        return 'single'
    if clean in ['3_months', '3months', '3-months']:
        return '3_months'
    if clean in ['custom']:
        return 'custom'

    if clean in ['monthly_2d', 'monthly_2days', 'monthly2d', 'monthly_2']:
        return 'monthly_2d'
    if clean in ['monthly_3d', 'monthly_3days', 'monthly3d', 'monthly_3']:
        return 'monthly_3d'

    if clean == 'monthly' or clean.startswith('monthly'):
        days = weekly_days or session_count
        try:
            days_int = int(days) if days is not None else 3
        except (ValueError, TypeError):
            days_int = 3
        return 'monthly_2d' if days_int == 2 else 'monthly_3d'

    return clean if clean in DEFAULT_BASE_PRICES else 'monthly_3d'


def get_package_quote(package_key, swimmer_count=1, session_count=None, weekly_days=None, custom_base=None):
    """
    Computes quote returning total batch price, per-person share, and economics.
    """
    try:
        count = int(swimmer_count or 1)
    except (ValueError, TypeError):
        count = 1
    count = max(1, min(5, count))

    canonical_key = normalize_package_key(package_key, weekly_days=weekly_days, session_count=session_count)
    base_prices = get_base_prices()

    if custom_base is not None and isinstance(custom_base, (int, float)) and custom_base >= 0:
        base_price = int(custom_base)
    elif canonical_key in base_prices:
        base_price = base_prices[canonical_key]
    elif canonical_key == 'custom':
        # Default single session anchor rate
        single_rate = base_prices.get('single', 750)
        sessions = max(0, int(session_count or 1))
        base_price = sessions * single_rate
    else:
        base_price = base_prices.get('monthly_3d', 7500)

    multiplier = GROUP_MULTIPLIERS.get(count, 1.00)
    total_batch_price = round(base_price * multiplier)
    price_per_person = round(total_batch_price / count)

    discount_percent = DISCOUNT_PERCENTAGES.get(count, 0.0)
    coach_bonus_percent = COACH_BONUS_PERCENTAGES.get(count, 0.0)
    total_savings = max(0, (base_price * count) - total_batch_price)

    sessions_val = PACKAGE_SESSIONS.get(canonical_key)
    if canonical_key == 'custom' and session_count is not None:
        sessions_val = session_count

    return {
        'package_key': canonical_key,
        'package_name': PACKAGE_NAMES.get(canonical_key, canonical_key.title()),
        'swimmer_count': count,
        'sessions': sessions_val,
        'base_price': base_price,
        'multiplier': multiplier,
        'total_batch_price': total_batch_price,
        'price_per_person': price_per_person,
        'savings_per_person_percent': discount_percent,
        'coach_bonus_percent': coach_bonus_percent,
        'total_savings': total_savings,
        'is_group': count > 1
    }


def calculate_package_price(package_key, swimmer_count=1, session_count=None, weekly_days=None):
    """
    Convenience method: returns the final integer total batch price.
    """
    quote = get_package_quote(
        package_key=package_key,
        swimmer_count=swimmer_count,
        session_count=session_count,
        weekly_days=weekly_days
    )
    return quote['total_batch_price']


def calculate_discounted_fee(package, persons, session_count=None):
    """
    SwimTrackPro authoritative pricing calculator.
    Replaces old hardcoded tier calculations with the decoupled
    base rate & group multiplier architecture.

    Returns:
        int -> Total payable amount (batch fee)
        0   -> Invalid / requires trainer discussion
    """
    try:
        persons = int(persons or 1)
    except Exception:
        persons = 1

    # Clamp group size between 1 and 5
    if persons < 1 or persons > 5:
        return 0

    base_prices = get_base_prices()
    multiplier = GROUP_MULTIPLIERS.get(persons, 1.00)

    clean_pkg = str(package or '').strip()

    # Demo Session: ₹500 base rate × multiplier
    if clean_pkg.lower() == 'demo':
        base = base_prices.get('demo', 500)
        return round(base * multiplier)

    # Single Day Booking: ₹750 base rate × multiplier
    if clean_pkg.lower() == 'single':
        base = base_prices.get('single', 750)
        return round(base * multiplier)

    # Monthly Package: 2 days/wk (₹5,000) or 3 days/wk (₹7,500)
    if clean_pkg.lower() == 'monthly':
        try:
            weekly_days = int(session_count or 3)
        except Exception:
            weekly_days = 3

        if weekly_days == 2:
            base = base_prices.get('monthly_2d', 5000)
        else:
            base = base_prices.get('monthly_3d', 7500)

        return round(base * multiplier)

    # 3 Calendar Months Package: ₹18,000 base rate × multiplier
    if clean_pkg.lower() in ['3_months', '3months', '3-months']:
        base = base_prices.get('3_months', 18000)
        return round(base * multiplier)

    # Custom Package: Dynamic duration
    if clean_pkg.lower() == 'custom':
        try:
            sessions = max(0, int(session_count or 0))
        except Exception:
            sessions = 0

        # More than 14 sessions requires trainer discussion
        if sessions > 14:
            return 0

        # 12 to 14 sessions are capped at 3-days/wk monthly equivalent
        if 12 <= sessions <= 14:
            base = base_prices.get('monthly_3d', 7500)
        else:
            single_rate = base_prices.get('single', 750)
            base = sessions * single_rate

        return round(base * multiplier)

    # Other Long Term Packages (6, 9, 12 months)
    if clean_pkg.lower() in ['6_months', '9_months', '12_months']:
        # Pro-rated based on 3-month anchor (18000 for 3 mos = 6000/mo)
        months_map = {'6_months': 6, '9_months': 9, '12_months': 12}
        months = months_map.get(clean_pkg.lower(), 6)
        base = 6000 * months
        return round(base * multiplier)

    # Fallback to monthly 3d
    base = base_prices.get('monthly_3d', 7500)
    return round(base * multiplier)


def get_pricing_config_dict():
    """
    Returns complete config dictionary for JSON serialization or template injection.
    """
    return {
        'base_prices': get_base_prices(),
        'multipliers': GROUP_MULTIPLIERS,
        'discounts': DISCOUNT_PERCENTAGES,
        'coach_bonuses': COACH_BONUS_PERCENTAGES,
        'packages': PACKAGE_METADATA,
    }
