"""
Package Tier Service for SwimTrackPro.
Handles package tier normalization, skip allocations, and Cult.fit-style pause days pool.
"""

def get_package_tier_info(raw_package):
    """
    Returns normalized package details:
    - key: 'Monthly', '3_months', '6_months', '9_months', '12_months', 'Custom', 'Single'
    - name: User-friendly name
    - is_monthly: True if monthly package
    - is_long_term: True if 3, 6, 9, 12 months or multi-month package
    - months: Duration in months (1, 3, 6, 9, 12)
    - total_skips: Allowed skip sessions (Monthly = 3, 3m = 9, 6m = 18, 9m = 27, 12m = 36)
    - pause_days: Allocated pause days (Monthly = 0, 3m = 15, 6m = 30, 9m = 45, 12m = 60)
    """
    pkg = str(raw_package or '').strip().lower()

    if '12' in pkg or 'year' in pkg:
        return {
            'key': '12_months',
            'name': '1 Year Package',
            'is_monthly': False,
            'is_long_term': True,
            'months': 12,
            'total_skips': 36,
            'pause_days': 60
        }
    elif '9' in pkg:
        return {
            'key': '9_months',
            'name': '9 Months Package',
            'is_monthly': False,
            'is_long_term': True,
            'months': 9,
            'total_skips': 27,
            'pause_days': 45
        }
    elif '6' in pkg:
        return {
            'key': '6_months',
            'name': '6 Months Package',
            'is_monthly': False,
            'is_long_term': True,
            'months': 6,
            'total_skips': 18,
            'pause_days': 30
        }
    elif '3' in pkg:
        return {
            'key': '3_months',
            'name': '3 Months Package',
            'is_monthly': False,
            'is_long_term': True,
            'months': 3,
            'total_skips': 9,
            'pause_days': 15
        }
    elif 'monthly' in pkg:
        return {
            'key': 'Monthly',
            'name': 'Monthly Package',
            'is_monthly': True,
            'is_long_term': False,
            'months': 1,
            'total_skips': 3,
            'pause_days': 0
        }
    elif 'custom' in pkg:
        return {
            'key': 'Custom',
            'name': 'Custom Package',
            'is_monthly': False,
            'is_long_term': True,
            'months': 3,
            'total_skips': 9,
            'pause_days': 15
        }
    else:
        return {
            'key': 'Single',
            'name': 'Single / Trial Session',
            'is_monthly': False,
            'is_long_term': False,
            'months': 0,
            'total_skips': 0,
            'pause_days': 0
        }
