import re

with open('templates/about_swimming.html', 'r') as f:
    content = f.read()

# Replace hero image if not already replaced
content = re.sub(r'swimming_hero.jpg', 'about_swimming_hero.jpg', content)

# Replace strokes image if not already replaced
content = re.sub(r'swimming_styles.jpg', 'about_swimming_strokes.jpg', content)

# Add image to rehab section
rehab_content = """<h3><i class="fa-solid fa-hand-holding-medical"></i> Rehab & Therapy</h3>
                    <img src="{{ url_for('static', filename='images/about_swimming_rehab.jpg') }}" alt="Aquatic Therapy" class="therapy-img">
                    <p>Aquatic therapy uses the unique properties of water—buoyancy, resistance, and hydrostatic pressure—for rehabilitation.</p>"""
content = re.sub(r'<h3><i class="fa-solid fa-hand-holding-medical"></i> Rehab & Therapy</h3>\s*<p>Aquatic therapy[^<]+</p>', rehab_content, content)

# Add image to training section
training_content = """<h3><i class="fa-solid fa-dumbbell"></i> Training & Endurance</h3>
                    <img src="{{ url_for('static', filename='images/about_swimming_training.jpg') }}" alt="Swimming Training Gear" class="therapy-img">
                    <p>Building swimming endurance requires a structured approach to training.</p>"""
content = re.sub(r'<h3><i class="fa-solid fa-dumbbell"></i> Training & Endurance</h3>\s*<p>Building swimming endurance[^<]+</p>', training_content, content)

with open('templates/about_swimming.html', 'w') as f:
    f.write(content)
