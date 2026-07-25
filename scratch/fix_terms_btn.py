import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/terms_agreement.html"
with open(file_path, "r") as f:
    content = f.read()

target = """<button type="button" class="btn btn-primary px-5 py-3" onclick="window.close();">"""
replacement = """<button type="button" class="btn btn-primary px-5 py-3" data-bs-dismiss="modal" onclick="if(!this.closest('.modal')) window.location.href='/';">"""

content = content.replace(target, replacement)

with open(file_path, "w") as f:
    f.write(content)

print("Updated terms_agreement.html close button.")
