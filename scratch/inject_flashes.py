import os

def inject_flash(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    target = '<div class="container py-4">'
    
    flash_html = """
    <!-- Flash message alerts container -->
    <div class="row justify-content-center">
        <div class="col-12">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'success' if category == 'success' else 'danger' if category == 'danger' or category == 'error' else 'warning' if category == 'warning' else 'info' }} alert-dismissible fade show mb-4 shadow-sm" role="alert" style="border-radius: 12px; font-weight: 500;">
                            {{ message }}
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>
    </div>
"""

    if target in content and "get_flashed_messages" not in content:
        content = content.replace(target, target + flash_html)
        with open(filepath, "w") as f:
            f.write(content)
        print(f"Injected into {filepath}")
    else:
        print(f"Skipped {filepath} (target not found or already has flashes)")

inject_flash("/Users/munisekhar/Desktop/swimTrackPro_v2/templates/my_bookings.html")
inject_flash("/Users/munisekhar/Desktop/swimTrackPro_v2/templates/guest_dashboard.html")
