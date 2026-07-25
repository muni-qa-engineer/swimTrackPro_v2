import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/components/footer.html"
with open(file_path, "r") as f:
    content = f.read()

target = "}, 50);"
replacement = "}, 500);"
content = content.replace(target, replacement)

with open(file_path, "w") as f:
    f.write(content)

print("Updated footer.html mermaid timeout.")
