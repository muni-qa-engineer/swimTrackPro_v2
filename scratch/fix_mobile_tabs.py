import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/about_swimming.html"
with open(file_path, "r") as f:
    content = f.read()

target_css = """    .custom-pills .nav-link {
        color: var(--color-text-secondary);
        border-radius: var(--radius-md);
        padding: 1rem 1.5rem;
        font-weight: 600;
        text-align: left;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid transparent;
        background: rgba(255,255,255,0.02);
        backdrop-filter: blur(10px);
        margin-bottom: 0.25rem;
    }"""

replacement_css = """    /* Hide scrollbar for mobile horizontal nav */
    .custom-pills::-webkit-scrollbar {
        display: none;
    }
    .custom-pills {
        -ms-overflow-style: none;  /* IE and Edge */
        scrollbar-width: none;  /* Firefox */
    }

    .custom-pills .nav-link {
        flex-shrink: 0; /* Prevents squishing on mobile so it actually scrolls */
        color: var(--color-text-secondary);
        border-radius: var(--radius-md);
        padding: 1rem 1.5rem;
        font-weight: 600;
        text-align: left;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid transparent;
        background: rgba(255,255,255,0.02);
        backdrop-filter: blur(10px);
        margin-bottom: 0.25rem;
    }"""

content = content.replace(target_css, replacement_css)

with open(file_path, "w") as f:
    f.write(content)

print("Updated about_swimming.html CSS for horizontal scrolling tabs on mobile")
