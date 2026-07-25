import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/about_trainer.html"
with open(file_path, "r") as f:
    content = f.read()

# 1. Update Form Tag
target_form = '<form action="/coach/feedback/{{ c.username }}" method="POST">'
replacement_form = '<form action="/coach/feedback/{{ c.username }}" method="POST" onsubmit="return validateFeedback(this, \'{{ c.username }}\')">'
content = content.replace(target_form, replacement_form)

# 2. Update hidden rating input (remove required attribute)
target_input = '<input type="hidden" id="rating-{{ c.username }}" name="rating" value="" required>'
replacement_input = '<input type="hidden" id="rating-{{ c.username }}" name="rating" value="">'
content = content.replace(target_input, replacement_input)

# 3. Add validateFeedback function
target_js = """        function highlightStars(stars, value) {"""
replacement_js = """        window.validateFeedback = function(form, username) {
            const hiddenInput = document.getElementById(`rating-${username}`);
            const starLabel = document.getElementById(`star-label-${username}`);
            if (!hiddenInput.value || hiddenInput.value === "0" || hiddenInput.value === "") {
                starLabel.innerHTML = '<span class="text-danger fw-bold"><i class="fa-solid fa-circle-exclamation"></i> Please select a rating!</span>';
                
                // Add a small shake animation to draw attention
                const starSelector = document.getElementById(`star-selector-${username}`);
                starSelector.style.transform = 'translate(5px, 0)';
                setTimeout(() => starSelector.style.transform = 'translate(-5px, 0)', 100);
                setTimeout(() => starSelector.style.transform = 'translate(5px, 0)', 200);
                setTimeout(() => starSelector.style.transform = 'translate(0, 0)', 300);
                
                return false;
            }
            return true;
        }

        function highlightStars(stars, value) {"""

content = content.replace(target_js, replacement_js)

with open(file_path, "w") as f:
    f.write(content)

print("Updated about_trainer.html with client-side feedback validation.")
