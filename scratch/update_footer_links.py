import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/components/footer.html"
with open(file_path, "r") as f:
    content = f.read()

# We need to replace everything from "<!-- About Swimming Modal -->" to the end of the file.
target = content.split("<!-- About Swimming Modal -->")[0]

new_modal_and_script = """<!-- Footer Dynamic Modal -->
<div class="modal fade" id="footerDynamicModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
        <div class="modal-content" style="background: var(--color-bg); border: 1px solid rgba(255,255,255,0.1); border-radius: var(--radius-lg);">
            <!-- Cancel Icon at top right -->
            <div class="modal-header border-0 pb-0 justify-content-end" style="padding: 1rem 1.5rem 0; z-index: 10;">
                <button type="button" class="btn text-white" data-bs-dismiss="modal" aria-label="Cancel" style="font-size: 1.5rem; padding: 0;">
                    <i class="fa-solid fa-circle-xmark"></i>
                </button>
            </div>
            <div class="modal-body p-0" id="footerDynamicModalBody" style="min-height: 50vh;">
                <!-- Content injected here -->
            </div>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', () => {
    // Apply modal to all these internal pages linked in the footer
    const targetPaths = ['/about', '/register', '/help', '/about-swimming', '/faq', '/terms-agreement'];
    
    const footerLinks = document.querySelectorAll('footer a');
    footerLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && targetPaths.includes(href)) {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const modalEl = document.getElementById('footerDynamicModal');
                const modalBody = document.getElementById('footerDynamicModalBody');
                
                modalBody.innerHTML = `
                    <div class="d-flex justify-content-center align-items-center py-5">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                `;
                
                if (typeof bootstrap !== 'undefined') {
                    const modal = new bootstrap.Modal(modalEl);
                    modal.show();
                }
                
                fetch(href)
                    .then(r => r.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        
                        // Extract the main content. Prioritize <main>, then a main container, then body.
                        let contentToInject = doc.querySelector('main');
                        if (!contentToInject) {
                            contentToInject = doc.querySelector('.container.py-4') || doc.body;
                        }
                        
                        modalBody.innerHTML = contentToInject.innerHTML;
                    })
                    .catch(err => {
                        modalBody.innerHTML = '<div class="text-center py-5 text-danger">Failed to load content.</div>';
                    });
            });
        }
    });
});
</script>
"""

with open(file_path, "w") as f:
    f.write(target + new_modal_and_script)

print("Updated footer.html to apply modal to all internal links with a cancel icon.")
