import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/components/footer.html"
with open(file_path, "r") as f:
    content = f.read()

# Replace the whole <script> block at the bottom again
script_start = content.find("<script>")
script_end = content.rfind("</script>") + 9

new_script = """<script>
document.addEventListener('DOMContentLoaded', function() {
    const footerLinks = document.querySelectorAll('.footer a');
    const footerModal = new bootstrap.Modal(document.getElementById('footerContentModal'));
    const modalBody = document.getElementById('footerContentModalBody');
    const modalTitle = document.getElementById('footerContentModalLabel');
    
    // Intercept footer links
    footerLinks.forEach(link => {
        if(link.closest('ul')) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const href = this.getAttribute('href');
                const titleText = this.textContent.trim();
                
                modalTitle.innerHTML = `<i class="fa-solid fa-circle-info text-primary me-2"></i> ${titleText}`;
                
                if(!href || href === '#' || href.startsWith('/#')) {
                    modalBody.innerHTML = `
                        <div class="text-center py-5">
                            <i class="fa-solid fa-person-digging text-muted" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                            <h4 class="text-white">Coming Soon</h4>
                            <p class="text-secondary">This section is currently under development. Please check back later!</p>
                        </div>
                    `;
                    footerModal.show();
                    return;
                }
                
                // Show loading state
                modalBody.innerHTML = `
                    <div class="text-center py-5">
                        <i class="fa-solid fa-circle-notch fa-spin text-primary" style="font-size: 2rem;"></i>
                        <p class="mt-3 text-muted">Loading content...</p>
                    </div>
                `;
                footerModal.show();
                
                // Fetch the page
                fetch(href)
                    .then(response => response.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        const mainContent = doc.querySelector('.site-main');
                        
                        if (mainContent) {
                            modalBody.innerHTML = mainContent.innerHTML;
                        } else {
                            const container = doc.querySelector('.container.py-4') || doc.body;
                            modalBody.innerHTML = container.innerHTML || 'Failed to load content.';
                        }
                    })
                    .catch(error => {
                        modalBody.innerHTML = `
                            <div class="text-center py-5 text-danger">
                                <i class="fa-solid fa-triangle-exclamation" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                                <h4>Error</h4>
                                <p>Failed to load the content. Please try again later.</p>
                            </div>
                        `;
                    });
            });
        }
    });
});
</script>"""

if script_start != -1 and script_end != -1:
    content = content[:script_start] + new_script + content[script_end:]
    with open(file_path, "w") as f:
        f.write(content)
    print("Cleaned up footer script successfully.")
else:
    print("Could not find script block.")
