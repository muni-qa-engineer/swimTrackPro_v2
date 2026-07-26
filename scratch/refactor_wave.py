import os
import re

template_dir = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates"

for root, _, files in os.walk(template_dir):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Replace <i class="fa-solid fa-water"></i> with 🏊🏼‍♂️
            new_content = re.sub(r'<i class="fa-solid fa-water"></i>', '🏊🏼‍♂️', content)
            
            # Replace <i class="fa-solid fa-water logo-icon"></i> with <span class="logo-icon">🏊🏼‍♂️</span>
            new_content = re.sub(r'<i class="fa-solid fa-water logo-icon"></i>', '<span class="logo-icon">🏊🏼‍♂️</span>', new_content)
            
            # Replace <i class="fa-solid fa-water" style="..."></i> with <span style="...">🏊🏼‍♂️</span>
            new_content = re.sub(r'<i class="fa-solid fa-water"\s+style="([^"]+)"></i>', r'<span style="\1">🏊🏼‍♂️</span>', new_content)
            
            if content != new_content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {file}")
