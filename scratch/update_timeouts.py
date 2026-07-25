import os
import re

directories = [
    "/Users/munisekhar/Desktop/swimTrackPro_v2/templates",
    "/Users/munisekhar/Desktop/swimTrackPro_v2/static"
]

for root_dir in directories:
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".html") or filename.endswith(".js"):
                filepath = os.path.join(dirpath, filename)
                
                with open(filepath, "r") as f:
                    content = f.read()
                
                original_content = content
                
                # Replace guest/trainer dashboard welcome toast timeout (3500 -> 1000)
                if "}, 3500);" in content:
                    content = content.replace("}, 3500);", "}, 1000);")
                
                # Replace booking.js confirmation toast (3000 -> 1000)
                if "'success',\n    3000\n  );" in content:
                    content = content.replace("'success',\n    3000\n  );", "'success',\n    1000\n  );")
                
                # Also generic createToast with 3000
                if "3000" in content:
                    # specifically look for createToast(..., ..., 3000) or similar
                    content = re.sub(r"createToast\(([^,]+),\s*([^,]+),\s*3000\)", r"createToast(\1, \2, 1000)", content)
                    content = re.sub(r"createToast\(([^,]+),\s*3000\)", r"createToast(\1, 1000)", content)

                if content != original_content:
                    with open(filepath, "w") as f:
                        f.write(content)
                    print(f"Updated {filename}")

print("Timeouts updated successfully.")
