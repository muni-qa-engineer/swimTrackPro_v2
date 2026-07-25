import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/my_bookings.html"
with open(file_path, "r") as f:
    content = f.read()

# We need to replace the inline headers and grids with Bootstrap Nav Tabs.
# Let's find the start of the grids.
start_marker = "{% if active_items %}"
end_marker = "{% endif %}\n\n                                {% if ns.show_add_card and role != 'trainer' %}"

if start_marker in content and end_marker in content:
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    old_block = content[start_idx:end_idx]
    
    new_tabs_block = """
                                <ul class="nav nav-pills mb-4" id="pills-tab-{{loop.index}}" role="tablist" style="background: rgba(0,0,0,0.2); padding: 0.5rem; border-radius: 50px; display: inline-flex;">
                                  <li class="nav-item" role="presentation">
                                    <button class="nav-link active rounded-pill px-4" id="pills-active-tab-{{loop.index}}" data-bs-toggle="pill" data-bs-target="#pills-active-{{loop.index}}" type="button" role="tab" aria-controls="pills-active-{{loop.index}}" aria-selected="true" style="font-weight: 600;"><i class="fa-solid fa-circle-play me-2 text-accent"></i>Active ({{active_items|length}})</button>
                                  </li>
                                  <li class="nav-item" role="presentation">
                                    <button class="nav-link rounded-pill px-4" id="pills-booked-tab-{{loop.index}}" data-bs-toggle="pill" data-bs-target="#pills-booked-{{loop.index}}" type="button" role="tab" aria-controls="pills-booked-{{loop.index}}" aria-selected="false" style="font-weight: 600;"><i class="fa-solid fa-calendar-check me-2 text-primary"></i>Booked ({{booked_items|length}})</button>
                                  </li>
                                  <li class="nav-item" role="presentation">
                                    <button class="nav-link rounded-pill px-4" id="pills-completed-tab-{{loop.index}}" data-bs-toggle="pill" data-bs-target="#pills-completed-{{loop.index}}" type="button" role="tab" aria-controls="pills-completed-{{loop.index}}" aria-selected="false" style="font-weight: 600;"><i class="fa-solid fa-check-double me-2 text-muted"></i>Completed ({{completed_items|length}})</button>
                                  </li>
                                </ul>

                                <div class="tab-content" id="pills-tabContent-{{loop.index}}">
                                  <div class="tab-pane fade show active" id="pills-active-{{loop.index}}" role="tabpanel" aria-labelledby="pills-active-tab-{{loop.index}}" tabindex="0">
                                      {% if active_items %}
                                      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                                          {% for b in active_items %}
                                              {{ render_booking_card(b, role, trainer_map, upi_id, account_holder_name) }}
                                          {% endfor %}
                                      </div>
                                      {% else %}
                                      <p class="text-muted py-4"><i class="fa-solid fa-mug-hot me-2"></i>No active bookings.</p>
                                      {% endif %}
                                  </div>
                                  <div class="tab-pane fade" id="pills-booked-{{loop.index}}" role="tabpanel" aria-labelledby="pills-booked-tab-{{loop.index}}" tabindex="0">
                                      {% if booked_items %}
                                      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                                          {% for b in booked_items %}
                                              {{ render_booking_card(b, role, trainer_map, upi_id, account_holder_name) }}
                                          {% endfor %}
                                      </div>
                                      {% else %}
                                      <p class="text-muted py-4"><i class="fa-solid fa-mug-hot me-2"></i>No upcoming bookings.</p>
                                      {% endif %}
                                  </div>
                                  <div class="tab-pane fade" id="pills-completed-{{loop.index}}" role="tabpanel" aria-labelledby="pills-completed-tab-{{loop.index}}" tabindex="0">
                                      {% if completed_items %}
                                      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                                          {% for b in completed_items %}
                                              {{ render_booking_card(b, role, trainer_map, upi_id, account_holder_name) }}
                                          {% endfor %}
                                      </div>
                                      {% else %}
                                      <p class="text-muted py-4"><i class="fa-solid fa-mug-hot me-2"></i>No completed bookings yet.</p>
                                      {% endif %}
                                  </div>
                                </div>
"""
    content = content.replace(old_block, new_tabs_block)
    
    with open(file_path, "w") as f:
        f.write(content)
    print("Tabs inserted.")
else:
    print("Could not find markers.")
