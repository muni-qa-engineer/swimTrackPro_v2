import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/my_bookings.html"
with open(file_path, "r") as f:
    content = f.read()

# 1. Define macro at the top of the content block
macro_start = """{% block content %}
{% macro render_booking_card(b, role, trainer_map, upi_id, account_holder_name) %}"""

macro_end = """{% endmacro %}

<div class="container py-4">"""

# Replace {% block content %} with macro definition + container start
content = content.replace("{% block content %}\n<div class=\"container py-4\">", macro_start)

# 2. Extract the booking card HTML
# We need to find <div class="booking-card h-100 ... to </div> <!-- end of booking card -->
# Wait, it's easier to find it using regex or just string splitting
start_str = """                                {% for b in group_items %}
                                <div class="booking-card h-100 {% if b.is_completed %}past-session{% endif %}">"""
end_str = """                                </div>
                                {% endfor %}

                                {% if ns.show_add_card and role != 'trainer' %}"""

card_start_idx = content.find('<div class="booking-card h-100')
card_end_idx = content.find('                                </div>\n                                {% endfor %}') + len('                                </div>')

card_html = content[card_start_idx:card_end_idx]

# Insert the card HTML into the macro
macro_def = macro_start + "\n" + card_html + "\n" + macro_end
content = content.replace(macro_start, macro_def)

# 3. Replace the old loop with the new categorized loops
new_loops = """
                                {% set active_items = [] %}
                                {% set booked_items = [] %}
                                {% set completed_items = [] %}
                                {% for b in group_items %}
                                    {% if b.is_completed %}
                                        {% set _ = completed_items.append(b) %}
                                    {% elif (b.completed_classes or 0) > 0 %}
                                        {% set _ = active_items.append(b) %}
                                    {% else %}
                                        {% set _ = booked_items.append(b) %}
                                    {% endif %}
                                {% endfor %}

                                {% if active_items %}
                                <h6 class="text-accent mb-3 mt-2" style="font-family: var(--font-display);"><i class="fa-solid fa-circle-play"></i> Active</h6>
                                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                                    {% for b in active_items %}
                                        {{ render_booking_card(b, role, trainer_map, upi_id, account_holder_name) }}
                                    {% endfor %}
                                </div>
                                {% endif %}

                                {% if booked_items %}
                                <h6 class="text-primary mb-3 mt-4" style="font-family: var(--font-display);"><i class="fa-solid fa-calendar-check"></i> Booked</h6>
                                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                                    {% for b in booked_items %}
                                        {{ render_booking_card(b, role, trainer_map, upi_id, account_holder_name) }}
                                    {% endfor %}
                                </div>
                                {% endif %}

                                {% if completed_items %}
                                <h6 class="text-muted mb-3 mt-4" style="font-family: var(--font-display);"><i class="fa-solid fa-check-double"></i> Completed</h6>
                                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                                    {% for b in completed_items %}
                                        {{ render_booking_card(b, role, trainer_map, upi_id, account_holder_name) }}
                                    {% endfor %}
                                </div>
                                {% endif %}
"""

old_loop_block = content[content.find('                                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">\n\n                                {% for b in group_items %}'):content.find('                                {% if ns.show_add_card and role != \'trainer\' %}')]

# Wait, the original had <div class="grid..."> which contained the cards. Now we have multiple grids.
old_full_block = """                            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

                                {% for b in group_items %}
""" + card_html + """
                                {% endfor %}"""

# Now replace the full block with the new loops
content = content.replace(old_full_block, new_loops)

# 4. We need to handle the renew card. The renew card was inside the original grid.
# We should probably wrap the renew card in its own grid or append it to the completed items grid.
# Wait, if we append it, we have to modify the new_loops above.
# Let's just output it in a separate grid below.
old_renew = """
                                {% if ns.show_add_card and role != 'trainer' %}
                                {% set latest_booking = group_items[-1] %}
                                <div class="col-12 col-lg-6 col-xl-4 mb-2">
                                    <a href="#" class="border-dashed" onclick="openRenewModal('{{ latest_booking.id }}', '{{ latest_booking.start_date }}'); return false;">
                                        <div class="card-body d-flex flex-column align-items-center justify-content-center">
                                            <div style="font-size: 2.5rem; color: var(--color-primary); font-weight: 300;">+</div>
                                            <h5 class="text-primary font-display" style="font-size: 1.15rem; margin-top: 0.5rem; margin-bottom: 0.25rem;">Renew Package</h5>
                                            <p class="text-muted" style="font-size: 0.8rem;">Completed or expiring soon.</p>
                                        </div>
                                    </a>
                                </div>
                                {% endif %}

                            </div>"""

new_renew = """
                                {% if ns.show_add_card and role != 'trainer' %}
                                {% set latest_booking = group_items[-1] %}
                                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    <div class="col-12 mb-2">
                                        <a href="#" class="border-dashed h-100" onclick="openRenewModal('{{ latest_booking.id }}', '{{ latest_booking.start_date }}'); return false;" style="display:block; padding:2rem;">
                                            <div class="card-body d-flex flex-column align-items-center justify-content-center h-100">
                                                <div style="font-size: 2.5rem; color: var(--color-primary); font-weight: 300;">+</div>
                                                <h5 class="text-primary font-display" style="font-size: 1.15rem; margin-top: 0.5rem; margin-bottom: 0.25rem;">Renew Package</h5>
                                                <p class="text-muted" style="font-size: 0.8rem;">Completed or expiring soon.</p>
                                            </div>
                                        </a>
                                    </div>
                                </div>
                                {% endif %}
"""
content = content.replace(old_renew, new_renew)


with open(file_path, "w") as f:
    f.write(content)
print("done")
