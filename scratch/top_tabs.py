file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/my_bookings.html"
with open(file_path, "r") as f:
    content = f.read()

start_marker = '<div id="bookingsSection">'
end_marker = '<!-- Pause Package Modal -->'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    old_block = content[start_idx:end_idx]
    
    new_block = """{% macro render_grouped_bookings(booking_list, role, trainer_map, upi_id, account_holder_name) %}
    {% set grouped_bookings = {} %}
    {% for b in booking_list|sort(attribute='start_date') %}
        {% set group_key = ((b.created_by or 'N/A')|lower|trim) ~ '|' ~ ((b.owner_phone or 'No Phone')|trim) %}
        {% if group_key not in grouped_bookings %}
            {% set _ = grouped_bookings.update({group_key: []}) %}
        {% endif %}
        {% set _ = grouped_bookings[group_key].append(b) %}
    {% endfor %}

    {% for group_key, group_items in grouped_bookings.items() %}
    {% set group_name = group_items[0].created_by or 'N/A' %}
    {% set group_phone = group_key.split('|')[1] %}
    {% set ns = namespace(has_active=false, has_booked=false, show_add_card=false) %}
    {% for booking in group_items %}
        {% if not booking.is_completed %}
            {% if (booking.completed_classes or 0) > 0 %}
                {% set ns.has_active = true %}
            {% else %}
                {% set ns.has_booked = true %}
            {% endif %}
            {% if booking.remaining_classes is defined and booking.remaining_classes <= 3 %}
                {% set ns.show_add_card = true %}
            {% endif %}
        {% else %}
            {% set ns.show_add_card = true %}
        {% endif %}
    {% endfor %}

    <div class="col-12 mb-4">
        <div class="glass-panel" style="padding: 0; overflow: hidden; border-color: rgba(255,255,255,0.05);">
            <div class="flex justify-between items-center trainer-group-header {% if role == 'trainer' %}cursor-pointer{% endif %}" data-group-key="{{ group_key }}-{{ loop.index }}" style="background: rgba(255, 255, 255, 0.02); padding: 1.25rem 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <div>
                    {% if role == 'trainer' %}
                    <span class="trainer-group-arrow me-2">{% if loop.first %}▼{% else %}<i class="fa-solid fa-play"></i>{% endif %}</span>
                    {% endif %}
                    <strong style="font-size: 1.1rem;"><i class="fa-solid fa-user text-primary"></i> {{ group_name|title }}</strong>
                    <span class="text-muted ms-3" style="font-size: 0.9rem;"><i class="fa-solid fa-phone"></i> {{ group_phone }}</span>
                </div>
                <span class="badge badge-success">
                    {{ group_items|length }} Booking{{ 's' if group_items|length > 1 else '' }}
                </span>
            </div>

            <div class="trainer-group-body" style="padding: 1.5rem; {% if role == 'trainer' and not loop.first %}display:none;{% endif %}">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {% for b in group_items %}
                        {{ render_booking_card(b, role, trainer_map, upi_id, account_holder_name) }}
                    {% endfor %}

                    {% if ns.show_add_card and role != 'trainer' %}
                    {% set latest_booking = group_items[-1] %}
                    <div class="col-12 mb-2">
                        <a href="#" class="border-dashed h-100" onclick="openRenewModal('{{ latest_booking.id }}', '{{ latest_booking.start_date }}'); return false;" style="display:block; padding:2rem;">
                            <div class="card-body d-flex flex-column align-items-center justify-content-center h-100">
                                <div style="font-size: 2.5rem; color: var(--color-primary); font-weight: 300;">+</div>
                                <h5 class="text-primary font-display" style="font-size: 1.15rem; margin-top: 0.5rem; margin-bottom: 0.25rem;">Renew Package</h5>
                                <p class="text-muted" style="font-size: 0.8rem;">Completed or expiring soon.</p>
                            </div>
                        </a>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
{% endmacro %}

<div id="bookingsSection">
    <div class="row g-0">
        <div class="col-12 px-0">
            {% if not bookings %}
                <p class="text-muted text-center py-5">No bookings found. Start by booking a slot!</p>
            {% else %}
                {% set active_all = [] %}
                {% set booked_all = [] %}
                {% set completed_all = [] %}
                {% for b in bookings %}
                    {% if b.is_completed %}
                        {% set _ = completed_all.append(b) %}
                    {% elif (b.completed_classes or 0) > 0 %}
                        {% set _ = active_all.append(b) %}
                    {% else %}
                        {% set _ = booked_all.append(b) %}
                    {% endif %}
                {% endfor %}

                <div class="text-center mb-5 mt-2">
                    <ul class="nav nav-pills d-inline-flex" id="mainPills-tab" role="tablist" style="background: rgba(0,0,0,0.2); padding: 0.5rem; border-radius: 50px; border: 1px solid rgba(255,255,255,0.05);">
                      <li class="nav-item" role="presentation">
                        <button class="nav-link active rounded-pill px-4 py-2" id="mainPills-active-tab" data-bs-toggle="pill" data-bs-target="#mainPills-active" type="button" role="tab" aria-controls="mainPills-active" aria-selected="true" style="font-weight: 600; font-size: 0.95rem; transition: all 0.3s ease;"><i class="fa-solid fa-circle-play me-2 text-accent"></i>Active <span class="badge bg-light text-dark ms-2 rounded-pill">{{active_all|length}}</span></button>
                      </li>
                      <li class="nav-item" role="presentation">
                        <button class="nav-link rounded-pill px-4 py-2" id="mainPills-booked-tab" data-bs-toggle="pill" data-bs-target="#mainPills-booked" type="button" role="tab" aria-controls="mainPills-booked" aria-selected="false" style="font-weight: 600; font-size: 0.95rem; transition: all 0.3s ease;"><i class="fa-solid fa-calendar-check me-2 text-primary"></i>Booked <span class="badge bg-light text-dark ms-2 rounded-pill">{{booked_all|length}}</span></button>
                      </li>
                      <li class="nav-item" role="presentation">
                        <button class="nav-link rounded-pill px-4 py-2" id="mainPills-completed-tab" data-bs-toggle="pill" data-bs-target="#mainPills-completed" type="button" role="tab" aria-controls="mainPills-completed" aria-selected="false" style="font-weight: 600; font-size: 0.95rem; transition: all 0.3s ease;"><i class="fa-solid fa-check-double me-2 text-muted"></i>Completed <span class="badge bg-light text-dark ms-2 rounded-pill">{{completed_all|length}}</span></button>
                      </li>
                    </ul>
                </div>

                <div class="tab-content" id="mainPills-tabContent">
                  <div class="tab-pane fade show active" id="mainPills-active" role="tabpanel" aria-labelledby="mainPills-active-tab" tabindex="0">
                      {% if active_all %}
                          {{ render_grouped_bookings(active_all, role, trainer_map, upi_id, account_holder_name) }}
                      {% else %}
                          <p class="text-muted text-center py-5"><i class="fa-solid fa-mug-hot me-2 text-accent" style="font-size: 2rem; opacity: 0.5;"></i><br><br>No active bookings.</p>
                      {% endif %}
                  </div>
                  <div class="tab-pane fade" id="mainPills-booked" role="tabpanel" aria-labelledby="mainPills-booked-tab" tabindex="0">
                      {% if booked_all %}
                          {{ render_grouped_bookings(booked_all, role, trainer_map, upi_id, account_holder_name) }}
                      {% else %}
                          <p class="text-muted text-center py-5"><i class="fa-solid fa-mug-hot me-2 text-primary" style="font-size: 2rem; opacity: 0.5;"></i><br><br>No upcoming bookings.</p>
                      {% endif %}
                  </div>
                  <div class="tab-pane fade" id="mainPills-completed" role="tabpanel" aria-labelledby="mainPills-completed-tab" tabindex="0">
                      {% if completed_all %}
                          {{ render_grouped_bookings(completed_all, role, trainer_map, upi_id, account_holder_name) }}
                      {% else %}
                          <p class="text-muted text-center py-5"><i class="fa-solid fa-mug-hot me-2 text-muted" style="font-size: 2rem; opacity: 0.5;"></i><br><br>No completed bookings yet.</p>
                      {% endif %}
                  </div>
                </div>
            {% endif %}
        </div>
    </div>
</div>
</div>
"""
    
    content = content.replace(old_block, new_block)
    
    with open(file_path, "w") as f:
        f.write(content)
    print("Done refactoring with top tabs.")
else:
    print("Could not find markers.")
