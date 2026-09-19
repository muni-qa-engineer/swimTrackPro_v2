with open('templates/profile.html', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "const fileLabel = document.getElementById('fileLabel');" in line:
        continue
    if "const filenameDisplay = document.getElementById('filenameDisplay');" in line:
        continue
    if "fileInput.addEventListener('change', () => {" in line:
        skip = True
        continue
    if skip and "});" in line and "fileLabel.innerHTML" not in line and "filenameDisplay.textContent" not in line:
        # Check if we are ending the change event listener
        # Actually it's easier to just do text replacement
        pass

