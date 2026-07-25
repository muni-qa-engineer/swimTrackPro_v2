import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/components/footer.html"
with open(file_path, "r") as f:
    content = f.read()

# I want to add a Modal HTML structure at the bottom of footer.html, and a script to handle it.
modal_html = """
<!-- Footer Content Modal -->
<div class="modal fade" id="footerContentModal" tabindex="-1" aria-labelledby="footerContentModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-xl modal-dialog-scrollable">
        <div class="modal-content" style="background: rgba(24, 24, 27, 0.98); backdrop-filter: var(--backdrop-blur); border: 1px solid rgba(255, 255, 255, 0.08); color: white;">
            <div class="modal-header" style="border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
                <h5 class="modal-title font-display" id="footerContentModalLabel"><i class="fa-solid fa-circle-info text-primary me-2"></i> Information</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body" id="footerContentModalBody" style="padding: 2rem;">
                <!-- Dynamic Content goes here -->
                <div class="text-center py-5">
                    <i class="fa-solid fa-circle-notch fa-spin text-primary" style="font-size: 2rem;"></i>
                    <p class="mt-3 text-muted">Loading...</p>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const footerLinks = document.querySelectorAll('.footer a');
    const footerModal = new bootstrap.Modal(document.getElementById('footerContentModal'));
    const modalBody = document.getElementById('footerContentModalBody');
    const modalTitle = document.getElementById('footerContentModalLabel');
    
    footerLinks.forEach(link => {
        // We only intercept links that are inside the columns, not social links or brand
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
                            // Fallback if no .site-main
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
</script>
"""

if modal_html not in content:
    content = content + "\n" + modal_html
    with open(file_path, "w") as f:
        f.write(content)
    print("Added Footer Modal logic.")
else:
    print("Footer Modal logic already exists.")
