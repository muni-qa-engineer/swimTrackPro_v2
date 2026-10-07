import json
import os
import time
from datetime import datetime

DEFAULT_PROMOTION = {
    'id': 1,
    'promo_key': 'top_banner',
    'event_name': 'Summer Swimming Camp 2026',
    'badge_text': 'SUMMER CAMP',
    'message': '☀️ Summer Swimming Camp 2026 is LIVE! Enroll early & get 20% off coaching at your apartment pool in Hyderabad.',
    'cta_text': 'Book Summer Camp',
    'cta_url': '/#plans',
    'banner_theme': 'summer',
    'is_active': True,
    'promo_version_id': 'promo_summer_camp_2026',
    'updated_at': ''
}

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')


def _read_settings_json():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _write_settings_json(data):
    try:
        current = _read_settings_json()
        current.update(data)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error writing settings.json: {e}")


def _build_version_id(event_name, updated_ts):
    clean_name = "".join(c if c.isalnum() else "_" for c in str(event_name).lower()).strip("_")
    ts_str = str(int(updated_ts)) if updated_ts else str(int(time.time()))
    return f"promo_{clean_name}_{ts_str}"


def get_active_promotion():
    """Retrieve the current promotion config from DB with fallback to settings.json/defaults."""
    from swimtrackpro.runtime import get_pg_connection

    # Attempt PostgreSQL read
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, promo_key, event_name, badge_text, message, cta_text, cta_url, 
                   banner_theme, is_active, updated_at
            FROM promotions 
            WHERE promo_key = 'top_banner'
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()

        if row:
            updated_ts = row[9].timestamp() if isinstance(row[9], datetime) else time.time()
            return {
                'id': row[0],
                'promo_key': row[1],
                'event_name': row[2] or '',
                'badge_text': row[3] or 'SPECIAL OFFER',
                'message': row[4] or '',
                'cta_text': row[5] or 'Explore Plans',
                'cta_url': row[6] or '/#plans',
                'banner_theme': row[7] or 'ocean',
                'is_active': bool(row[8]),
                'updated_at': row[9].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row[9], datetime) else str(row[9]),
                'promo_version_id': _build_version_id(row[2], updated_ts)
            }
    except Exception as e:
        # DB query failed or table not ready, fall back to JSON
        pass

    # Fallback to settings.json
    settings = _read_settings_json()
    promo = settings.get('promotion')
    if promo and isinstance(promo, dict):
        updated_ts = promo.get('updated_ts', time.time())
        promo['promo_version_id'] = _build_version_id(promo.get('event_name', 'event'), updated_ts)
        return promo

    # Fallback to default
    default = dict(DEFAULT_PROMOTION)
    default['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return default


def save_promotion(event_name, badge_text, message, cta_text, cta_url, banner_theme, is_active):
    """Save promotion configuration to database and settings.json backup."""
    from swimtrackpro.runtime import get_pg_connection

    event_name = (event_name or 'Special Event').strip()
    badge_text = (badge_text or 'SPECIAL OFFER').strip().upper()
    message = (message or '').strip()
    cta_text = (cta_text or 'Explore Plans').strip()
    cta_url = (cta_url or '/#plans').strip()
    banner_theme = (banner_theme or 'ocean').strip().lower()
    is_active = bool(is_active)
    now = datetime.now()
    now_ts = time.time()

    # 1. Update/Insert in PostgreSQL
    db_success = False
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO promotions (promo_key, event_name, badge_text, message, cta_text, cta_url, banner_theme, is_active, updated_at)
            VALUES ('top_banner', %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (promo_key) DO UPDATE 
            SET event_name = EXCLUDED.event_name,
                badge_text = EXCLUDED.badge_text,
                message = EXCLUDED.message,
                cta_text = EXCLUDED.cta_text,
                cta_url = EXCLUDED.cta_url,
                banner_theme = EXCLUDED.banner_theme,
                is_active = EXCLUDED.is_active,
                updated_at = EXCLUDED.updated_at
        """, (event_name, badge_text, message, cta_text, cta_url, banner_theme, is_active, now))
        conn.commit()
        conn.close()
        db_success = True
    except Exception as e:
        print(f"Error saving promotion to database: {e}")

    # 2. Update settings.json backup
    promo_data = {
        'id': 1,
        'promo_key': 'top_banner',
        'event_name': event_name,
        'badge_text': badge_text,
        'message': message,
        'cta_text': cta_text,
        'cta_url': cta_url,
        'banner_theme': banner_theme,
        'is_active': is_active,
        'updated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_ts': now_ts,
        'promo_version_id': _build_version_id(event_name, now_ts)
    }
    _write_settings_json({'promotion': promo_data})

    return promo_data


def toggle_promotion_status(new_status=None):
    """Toggle the active status of the promotional banner."""
    current = get_active_promotion()
    if new_status is None:
        target_status = not current.get('is_active', True)
    else:
        target_status = bool(new_status)

    return save_promotion(
        event_name=current.get('event_name'),
        badge_text=current.get('badge_text'),
        message=current.get('message'),
        cta_text=current.get('cta_text'),
        cta_url=current.get('cta_url'),
        banner_theme=current.get('banner_theme'),
        is_active=target_status
    )
