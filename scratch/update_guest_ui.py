import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/guest_dashboard.html"
with open(file_path, "r") as f:
    content = f.read()

# 1. Replace My Swimmers Block
target_swimmers = """                <!-- My Swimmers -->
                <div class="glass-panel" style="padding: 1.5rem; flex: 1;">
                    <div class="flex justify-between items-center mb-3">
                        <h3 class="font-display" style="font-size: 1.25rem; margin: 0;"><i class="fa-solid fa-users text-accent"></i> My Swimmers</h3>
                        <span class="badge badge-success">{{ students|length if students else 0 }}</span>
                    </div>
                    <div style="max-height: 180px; overflow-y: auto;">
                        {% if students and students|length > 0 %}
                            {% for s in students %}
                            <div class="swimmer-row">
                                <div class="swimmer-avatar">{{ s.name[:1]|upper }}</div>
                                <div>
                                    <div style="font-weight: 600; font-size: 0.95rem;">{{ s.name }}</div>
                                    <div class="text-muted" style="font-size: 0.8rem;">
                                        {% if s.completed_sessions is defined and s.total_sessions is defined and s.total_sessions > 0 %}
                                            {{ s.completed_sessions }}/{{ s.total_sessions }} completed
                                        {% else %}
                                            Active Swimmer
                                        {% endif %}
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        {% else %}
                            <p class="text-muted" style="font-size: 0.9rem;">No swimmers registered.</p>
                        {% endif %}
                    </div>
                </div>"""

replacement_swimmers = """                <!-- My Swimmers Interactive -->
                <div class="glass-panel" style="padding: 1.5rem; flex: 1; display: flex; flex-direction: column;">
                    <div class="flex justify-between items-center mb-2">
                        <h3 class="font-display" style="font-size: 1.25rem; margin: 0;"><i class="fa-solid fa-users text-accent"></i> My Swimmers</h3>
                        <span class="badge badge-success">{{ students|length if students else 0 }}</span>
                    </div>
                    <p class="text-muted small mb-3">Your swimmers are here to learn and their progress is steadily going up! <i class="fa-solid fa-arrow-trend-up text-success ms-1"></i></p>
                    <div style="flex: 1; overflow-y: auto; padding-right: 5px;">
                        {% if students and students|length > 0 %}
                            {% for s in students %}
                            {% set pct = ((s.completed_sessions / s.total_sessions) * 100) if s.total_sessions and s.total_sessions > 0 else 0 %}
                            <div class="swimmer-row mb-3" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); padding: 1rem; border-radius: var(--radius-md); transition: transform 0.2s;" onmouseover="this.style.transform='translateX(5px)'" onmouseout="this.style.transform='translateX(0)'">
                                <div class="flex items-center gap-3 mb-2">
                                    <div class="swimmer-avatar" style="width: 40px; height: 40px; background: linear-gradient(135deg, var(--color-primary), var(--color-accent)); display: flex; align-items: center; justify-content: center; border-radius: 50%; font-weight: bold; color: white;">{{ s.name[:1]|upper }}</div>
                                    <div style="flex: 1;">
                                        <div style="font-weight: 700; font-size: 1rem; display: flex; justify-content: space-between;">
                                            {{ s.name }}
                                            <span class="badge" style="background: rgba(16,185,129,0.1); color: #10b981;">{{ s.skill_level if s.skill_level else 'Beginner' }}</span>
                                        </div>
                                    </div>
                                </div>
                                {% if s.total_sessions is defined and s.total_sessions > 0 %}
                                <div class="progress mt-2" style="height: 6px; background: rgba(255,255,255,0.1);">
                                    <div class="progress-bar bg-success" role="progressbar" style="width: {{ pct }}%;" aria-valuenow="{{ pct }}" aria-valuemin="0" aria-valuemax="100"></div>
                                </div>
                                <div class="d-flex justify-content-between text-muted mt-1" style="font-size: 0.75rem;">
                                    <span>{{ s.completed_sessions }} Completed</span>
                                    <span>{{ s.total_sessions }} Total</span>
                                </div>
                                {% else %}
                                <div class="text-muted small mt-1"><i class="fa-solid fa-person-swimming text-primary"></i> Active & Learning</div>
                                {% endif %}
                            </div>
                            {% endfor %}
                        {% else %}
                            <div class="text-center p-4">
                                <div style="font-size: 2rem; color: rgba(255,255,255,0.1); margin-bottom: 10px;"><i class="fa-solid fa-water"></i></div>
                                <p class="text-muted" style="font-size: 0.9rem;">No swimmers registered yet.</p>
                            </div>
                        {% endif %}
                    </div>
                </div>"""
content = content.replace(target_swimmers, replacement_swimmers)

# 2. Insert Available Coaches before </section>
target_coaches_insert = """    </section>"""
replacement_coaches = """        <!-- Available Coaches -->
        <div class="mt-5 mb-3">
            <h3 class="font-display mb-4" style="font-size: 1.5rem;"><i class="fa-solid fa-star text-warning"></i> Available Coaches</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {% for coach in available_coaches %}
                <div class="glass-panel coach-card" style="padding: 1.5rem; position: relative; transition: transform 0.3s;" onmouseover="this.style.transform='translateY(-5px)'" onmouseout="this.style.transform='translateY(0)'">
                    <!-- Favorite Toggle -->
                    <button class="btn btn-link p-0 position-absolute" style="top: 1rem; right: 1rem; z-index: 10; color: {{ '#ef4444' if coach.is_favorited else 'rgba(255,255,255,0.3)' }}; transition: color 0.3s;" onclick="toggleFavorite('{{ coach.username }}', this)">
                        <i class="fa-{{ 'solid' if coach.is_favorited else 'regular' }} fa-heart fa-xl"></i>
                    </button>
                    
                    <div class="d-flex align-items-center gap-3 mb-4">
                        {% if coach.photos %}
                            <img src="{{ url_for('static', filename='uploads/' + coach.photos) }}" alt="{{ coach.name }}" style="width: 70px; height: 70px; border-radius: 50%; object-fit: cover; border: 2px solid var(--color-primary);">
                        {% else %}
                            <div style="width: 70px; height: 70px; border-radius: 50%; background: rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; font-size: 1.8rem; font-weight: 700; color: var(--color-primary); border: 2px solid var(--color-primary);">
                                {{ coach.name[:1]|upper }}
                            </div>
                        {% endif %}
                        <div>
                            <h4 class="mb-1 text-white" style="font-weight: 700; font-size: 1.2rem;">{{ coach.name }}</h4>
                            <div class="text-warning small" style="font-weight: 600;"><i class="fa-solid fa-star"></i> {{ "%.1f"|format(coach.rating) }} Rating</div>
                        </div>
                    </div>
                    
                    <div class="text-muted small mb-4">
                        <div class="mb-1"><i class="fa-solid fa-briefcase me-2 text-primary"></i>{{ coach.experience }}</div>
                        <div class="mb-1"><i class="fa-solid fa-certificate me-2 text-accent"></i>{{ coach.qualification }}</div>
                        {% if coach.specialties %}
                        <div><i class="fa-solid fa-medal me-2 text-warning"></i>{{ coach.specialties[:40] }}...</div>
                        {% endif %}
                    </div>
                    
                    <button class="btn btn-outline w-100" style="border-color: rgba(6,182,212,0.5); color: var(--color-primary);" onclick='viewCoachProfile({{ coach|tojson|safe }})'>View Profile</button>
                </div>
                {% else %}
                <div class="col-12 text-center p-5 glass-panel" style="grid-column: 1 / -1;">
                    <p class="text-muted mb-0">No coaches currently available.</p>
                </div>
                {% endfor %}
            </div>
        </div>
        
    </section>"""
content = content.replace(target_coaches_insert, replacement_coaches)

# 3. Insert Coach Profile Modal and JS before {% endblock %}
target_js = """<script src="{{ url_for('static', filename='dashboard_core.js') }}"></script>

{% endblock %}"""

replacement_js = """<script src="{{ url_for('static', filename='dashboard_core.js') }}"></script>

<!-- Coach Profile Modal -->
<div class="modal fade" id="coachProfileModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content glass-panel" style="background: rgba(15, 15, 18, 0.95); border: 1px solid rgba(255,255,255,0.1);">
            <div class="modal-header border-0 pb-0">
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body pt-0 px-4 pb-4">
                <div class="text-center mb-4">
                    <div id="modalCoachAvatar" style="width: 100px; height: 100px; border-radius: 50%; background: rgba(255,255,255,0.1); margin: 0 auto 1rem; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; font-weight: 700; color: var(--color-primary); border: 3px solid var(--color-primary); overflow: hidden;"></div>
                    <h3 id="modalCoachName" class="font-display text-white mb-1"></h3>
                    <div id="modalCoachRating" class="text-warning small" style="font-weight: 600;"></div>
                </div>
                
                <div class="mb-3">
                    <h6 class="text-primary font-display mb-2">About</h6>
                    <p id="modalCoachBio" class="text-muted small mb-0"></p>
                </div>
                
                <div class="grid grid-cols-2 gap-3 mb-3">
                    <div class="p-3 rounded" style="background: rgba(255,255,255,0.03);">
                        <div class="text-muted" style="font-size: 0.7rem; text-transform: uppercase;">Experience</div>
                        <div id="modalCoachExp" style="font-size: 0.9rem; font-weight: 600; color: white;"></div>
                    </div>
                    <div class="p-3 rounded" style="background: rgba(255,255,255,0.03);">
                        <div class="text-muted" style="font-size: 0.7rem; text-transform: uppercase;">Location</div>
                        <div id="modalCoachLoc" style="font-size: 0.9rem; font-weight: 600; color: white;"></div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <h6 class="text-accent font-display mb-2">Qualifications</h6>
                    <p id="modalCoachQual" class="text-muted small mb-0"></p>
                </div>
                
                <div class="mb-3">
                    <h6 class="text-warning font-display mb-2">Specialties</h6>
                    <p id="modalCoachSpec" class="text-muted small mb-0"></p>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    let coachModalObj = null;
    document.addEventListener('DOMContentLoaded', () => {
        coachModalObj = new bootstrap.Modal(document.getElementById('coachProfileModal'));
    });

    function toggleFavorite(username, btnElement) {
        const icon = btnElement.querySelector('i');
        // Optimistic UI update
        const isCurrentlyFavorited = icon.classList.contains('fa-solid');
        
        if (isCurrentlyFavorited) {
            icon.classList.remove('fa-solid');
            icon.classList.add('fa-regular');
            btnElement.style.color = 'rgba(255,255,255,0.3)';
        } else {
            icon.classList.remove('fa-regular');
            icon.classList.add('fa-solid');
            btnElement.style.color = '#ef4444';
        }

        const formData = new FormData();
        formData.append('trainer_username', username);

        fetch('/api/toggle_favorite_coach', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status !== 'success') {
                // Revert if failed
                alert(data.message || "Failed to update favorite.");
                if (isCurrentlyFavorited) {
                    icon.classList.add('fa-solid');
                    icon.classList.remove('fa-regular');
                    btnElement.style.color = '#ef4444';
                } else {
                    icon.classList.add('fa-regular');
                    icon.classList.remove('fa-solid');
                    btnElement.style.color = 'rgba(255,255,255,0.3)';
                }
            }
        })
        .catch(err => {
            console.error(err);
        });
    }

    function viewCoachProfile(coach) {
        document.getElementById('modalCoachName').innerText = coach.name;
        document.getElementById('modalCoachRating').innerHTML = `<i class="fa-solid fa-star"></i> ${parseFloat(coach.rating).toFixed(1)} Rating`;
        document.getElementById('modalCoachBio').innerText = coach.bio || "No bio provided.";
        document.getElementById('modalCoachExp').innerText = coach.experience || "N/A";
        document.getElementById('modalCoachLoc').innerText = coach.residence_location || "N/A";
        document.getElementById('modalCoachQual').innerText = coach.qualification || "N/A";
        document.getElementById('modalCoachSpec').innerText = coach.specialties || "N/A";
        
        const avatarContainer = document.getElementById('modalCoachAvatar');
        if (coach.photos) {
            avatarContainer.innerHTML = `<img src="/static/uploads/${coach.photos}" style="width: 100%; height: 100%; object-fit: cover;">`;
        } else {
            avatarContainer.innerHTML = coach.name.substring(0, 1).toUpperCase();
        }
        
        coachModalObj.show();
    }
</script>

{% endblock %}"""
content = content.replace(target_js, replacement_js)

with open(file_path, "w") as f:
    f.write(content)

print("Updated guest_dashboard.html UI")
