import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/base.html"
with open(file_path, "r") as f:
    content = f.read()

target = """            document.addEventListener('submit', function(e) {
                const form = e.target;
                const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]') || """

replacement = """            document.addEventListener('submit', function(e) {
                if (e.defaultPrevented) return;
                
                const form = e.target;
                const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]') || """

content = content.replace(target, replacement)

with open(file_path, "w") as f:
    f.write(content)

print("Updated base.html global submit listener to respect e.defaultPrevented")
