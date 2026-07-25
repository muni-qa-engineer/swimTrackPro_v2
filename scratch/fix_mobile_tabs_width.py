import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/about_swimming.html"
with open(file_path, "r") as f:
    content = f.read()

target_css = """    /* Responsive */
    @media (max-width: 991.98px) {
        .hero-section { height: 250px; padding: 2rem; background-attachment: scroll; }
        .hero-overlay { padding: 2rem; }
        .content-pane { padding: 1.5rem; }
        .sidebar-sticky { position: static; margin-bottom: 2rem; }
        
        .custom-pills {
            display: flex;
            overflow-x: auto;
            white-space: nowrap;
            padding-bottom: 10px;
            margin-bottom: 10px;
        }
        .custom-pills .nav-link {
            padding: 0.75rem 1rem;
            margin-bottom: 0;
        }
    }"""

replacement_css = """    /* Responsive */
    @media (max-width: 991.98px) {
        .hero-section { height: 250px; padding: 2rem; background-attachment: scroll; }
        .hero-overlay { padding: 2rem; }
        .content-pane { padding: 1.5rem; }
        .sidebar-sticky { 
            position: static; 
            margin-bottom: 2rem; 
            max-width: 100%; 
            width: 100%;
        }
        
        .custom-pills {
            display: flex;
            overflow-x: auto;
            white-space: nowrap;
            padding-bottom: 10px;
            margin-bottom: 10px;
            width: 100%;
            max-width: 100%;
            -webkit-overflow-scrolling: touch;
            scroll-snap-type: x mandatory;
        }
        .custom-pills .nav-link {
            padding: 0.75rem 1rem;
            margin-bottom: 0;
            scroll-snap-align: start;
        }
    }"""

content = content.replace(target_css, replacement_css)

with open(file_path, "w") as f:
    f.write(content)

print("Updated about_swimming.html mobile CSS for horizontal tabs scrolling")
