import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/booking.html"
with open(file_path, "r") as f:
    content = f.read()

# Replace hiddenTrainerInput with the dropdown in Step 1
old_input = '<input type="hidden" name="trainer_username" id="hiddenTrainerInput" required>'
new_input = '''
        <!-- Coach Selection added to Step 1 -->
        <div class="booking-step-pane" id="step-pane-0" style="display:none;"></div> <!-- dummy to keep indexing simple if needed, wait no -->
        
        <div class="form-group mb-4" style="max-width: 800px; margin: 0 auto 1.5rem auto;">
            <label for="coachSelect" class="form-label" style="color: var(--color-primary); font-weight: 700;">Select Coach <span class="text-danger">*</span></label>
            <select name="trainer_username" id="coachSelect" class="form-control" required style="background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); color: white; padding: 0.75rem; border-radius: var(--radius-sm);">
                <option value="">-- Choose a Coach --</option>
                {% for t in trainers %}
                <option value="{{ t.username }}" data-slots='{{ t.available_slots or "[]" }}'>{{ t.name }} (Rating: {{ t.rating }})</option>
                {% endfor %}
            </select>
        </div>
'''
if old_input in content:
    content = content.replace(old_input, new_input)
else:
    print("Could not find hiddenTrainerInput")

# Remove Step 2
start_idx = content.find("<!-- STEP 2: Coach Selection -->")
end_idx = content.find("<!-- STEP 3: Swimmer Details -->")
if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + content[end_idx:]
else:
    print("Could not find Step 2 or Step 3 markers")

# Rename Step 3 to Step 2
content = content.replace("<!-- STEP 3: Swimmer Details -->", "<!-- STEP 2: Swimmer Details -->")
content = content.replace('id="step-pane-3"', 'id="step-pane-2"')
content = content.replace("3. Swimmer Details", "2. Swimmer Details")
content = content.replace("wizardPrev(3)", "wizardPrev(2)")

with open(file_path, "w") as f:
    f.write(content)
print("booking.html updated successfully.")
